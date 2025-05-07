import os
import sys
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

def get_capture_times(filepaths):
    """Get capture times for multiple files in one exiftool call."""
    try:
        # Use exiftool to read EXIF data for all files at once
        cmd = ['exiftool', '-DateTimeOriginal', '-d', '%Y:%m:%d %H:%M:%S', '-json'] + [str(f) for f in filepaths]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error running exiftool: {result.stderr}")
            return {}
            
        # Parse JSON output
        import json
        data = json.loads(result.stdout)
        
        # Create dictionary of filepath -> capture time
        times = {}
        for item in data:
            filepath = Path(item['SourceFile'])
            if 'DateTimeOriginal' in item:
                try:
                    times[filepath] = datetime.strptime(item['DateTimeOriginal'], "%Y:%m:%d %H:%M:%S")
                except Exception as e:
                    print(f"Error parsing date for {filepath}: {e}")
        
        return times
        
    except Exception as e:
        print(f"Error reading EXIF data: {e}")
        return {}

def move_file_with_sidecar(file_path, target_dir):
    """Moves a file and its associated .xmp file, if present."""
    # Move original file
    shutil.move(str(file_path), target_dir)
    
    # Check for associated .xmp file
    xmp_path = file_path.with_suffix('.xmp')
    if xmp_path.exists():
        shutil.move(str(xmp_path), target_dir)

def run_helicon_focus(stack_dir: Path, output_dir: Path, use_tiff: bool = False, combine_ab: bool = True) -> None:
    """Process a stack with Helicon Focus using methods A, B, C and optionally combine A+B."""
    from helicon_focus import process_stack
    process_stack(stack_dir, output_dir, combine_ab=combine_ab)

def stack_images(source_dir, target_dir=None, stack_interval=1) -> List[Path]:
    print(f"\n🔍 Analyzing directory: {source_dir}")
    source_path = Path(source_dir)
    created_stacks = []  # List of created stack directories
    stack_count = 0  # Initialize stack counter
    if target_dir:
        target_path = Path(target_dir)
    else:
        target_path = source_path

    print("💾 Searching for image files...")
    files = sorted(source_path.glob("*.*"))
    
    # Supported image formats
    supported_formats = {
        'RAW': [".orf", ".nef", ".cr2", ".arw", ".rw2", ".raf", ".dng"],  # Olympus, Nikon, Canon, Sony, Panasonic, Fuji, Adobe
        'Standard': [".jpg", ".jpeg", ".tiff", ".tif", ".png"],
    }
    
    # Create flat list of all extensions
    all_extensions = [ext.lower() for exts in supported_formats.values() for ext in exts]
    
    # Find all image files
    image_files = [f for f in files if f.suffix.lower() in all_extensions]
    total_images = len(image_files)
    
    if total_images == 0:
        print("⚠️ No supported image files found!")
        print("\nSupported formats:")
        for category, extensions in supported_formats.items():
            print(f"{category}: {', '.join(extensions)}")
        return
    
    # Count files per format
    format_counts = {}
    for f in image_files:
        ext = f.suffix.lower()
        format_counts[ext] = format_counts.get(ext, 0) + 1
    
    print(f"✅ {total_images} image files found:")
    for ext, count in format_counts.items():
        print(f"  - {count}x {ext}")
    
    print(f"✅ {total_images} image files found.")
    print("📅 Reading EXIF data...")
    
    # Get capture times for all files at once
    print("📅 Reading EXIF data in batch mode...")
    capture_times = get_capture_times(image_files)
    
    # Filter files with EXIF data
    image_files = [f for f in image_files if f in capture_times]
    if len(image_files) < total_images:
        print(f"⚠️ {total_images - len(image_files)} files without EXIF data found and skipped.")
    
    if not image_files:
        print("❌ No usable files found!")
        return

    print(f"🔄 Analyzing time intervals between {len(image_files)} images...")
    
    last_time = None
    stack = []
    stack_num = 1
    stacks_created = 0
    files_moved = 0
    stack_sizes = []

    for i, file in enumerate(image_files, 1):
        capture_time = capture_times[file]
        
        if i % 10 == 0:  # Show progress every 10 files
            print(f"\r💾 Processing file {i}/{len(image_files)}...", end="")

        if last_time and (capture_time - last_time).total_seconds() > stack_interval:
            if len(stack) > 1:
                stack_dir = target_path / f"Stack_{stack_num:03}"
                stack_dir.mkdir(parents=True, exist_ok=True)
                for f in stack:
                    move_file_with_sidecar(f, stack_dir)
                    files_moved += 1
                created_stacks.append(stack_dir)
                stack_sizes.append((stack_num, len(stack)))
                stacks_created += 1
                stack_num += 1
            stack = []

        stack.append(file)
        last_time = capture_time

    # Process last stack
    if len(stack) > 1:
        stack_dir = target_path / f"Stack_{stack_num:03}"
        stack_dir.mkdir(parents=True, exist_ok=True)
        for file in stack:
            move_file_with_sidecar(file, stack_dir)
            files_moved += 1
        created_stacks.append(stack_dir)
        stack_sizes.append((stack_num, len(stack)))
        stacks_created += 1

    print("\r" + " " * 50 + "\r", end="")  # Clear the last progress indicator
    print(f"✅ Done: {stacks_created} stacks created.")
    
    if stacks_created > 0:
        print("\n📂 Stack overview:")
        for num, size in stack_sizes:
            print(f"Stack_{num:03} → {size} images")
        print(f"\n📁 {files_moved} files moved.")
        print(f"📁 Target directory: {target_path.resolve()}")
    else:
        print("ℹ️ No focus stacks found. Possible reasons:")
        print("  - Images were not taken in rapid succession")
        print("  - Time interval between shots > 1 second")
        print("  - Only single images in directory")
    
    return created_stacks

def print_usage():
    print("❗ Usage: python focus_stack_sorter.py <source_dir> [<target_dir>] [options]")
    print("\nOptions:")
    print("  --interval      Maximum time interval between images in seconds (optional, default: 1)")
    print("  --stack         Process stacks with HeliconFocus after organizing")
    print("  --stack-only    Process existing stacks with HeliconFocus without sorting")
    print("  --resume        Process only unprocessed stacks with HeliconFocus")
    print("  --tiff          Use TIFF format for HeliconFocus processing (default: RAW/DNG)")
    print("  --no-ab         Skip A+B combination in HeliconFocus processing")
    print("\nExamples:")
    print("  python focus_stack_sorter.py ~/Pictures/OM1_RAWs")
    print("  python focus_stack_sorter.py ~/Pictures/OM1_RAWs ~/Stacks")
    print("  python focus_stack_sorter.py ~/Pictures/OM1_RAWs --interval 2")
    print("  python focus_stack_sorter.py ~/Pictures/OM1_RAWs ~/Stacks --interval 0.5")

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] in ["-h", "--help"]:
        print_usage()
        sys.exit(1)

    source_dir = sys.argv[1]
    target_dir = None
    interval = 1.0  # Default: 1 second
    use_helicon = False
    stack_only = False
    resume = False
    use_tiff = False
    combine_ab = True  # Default: create A+B combination

    # Process remaining arguments
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--interval":
            if i + 1 >= len(sys.argv):
                print("❌ Error: --interval requires a value in seconds")
                sys.exit(1)
            try:
                interval = float(sys.argv[i + 1])
                if interval <= 0:
                    print("❌ Error: Interval must be greater than 0")
                    sys.exit(1)
                i += 2
            except ValueError:
                print(f"❌ Error: Invalid interval '{sys.argv[i + 1]}'")
                sys.exit(1)
        elif sys.argv[i] == "--stack":
            use_helicon = True
            i += 1
        elif sys.argv[i] == "--tiff":
            use_tiff = True
            i += 1
        elif sys.argv[i] == "--no-ab":
            combine_ab = False
            i += 1
        elif sys.argv[i] == "--stack-only":
            stack_only = True
            use_helicon = True
            i += 1
        elif sys.argv[i] == "--resume":
            resume = True
            use_helicon = True
            i += 1
        else:
            if target_dir is None:
                target_dir = sys.argv[i]
            else:
                print(f"❌ Error: Unknown parameter '{sys.argv[i]}'")
                print_usage()
                sys.exit(1)
            i += 1

    # Create target directory if not specified
    if not target_dir:
        target_dir = source_dir
    
    # Start total time measurement
    total_start = time.time()
    
    # Find existing stacks if not sorting
    if stack_only:
        print("\n🔍 Looking for existing stacks...")
        stacks = []
        for item in Path(target_dir).iterdir():
            if item.is_dir() and item.name.startswith("Stack_"):
                stacks.append(item)
        print(f"Found {len(stacks)} existing stacks")
    else:
        # Run stacking
        sort_start = time.time()
        stacks = stack_images(source_dir, target_dir, interval)
        sort_time = time.time() - sort_start
        print(f"\n⏱️ Sorting time: {sort_time:.2f} seconds")
    
    # Process with HeliconFocus if requested
    if use_helicon:
        # Filter stacks if resuming
        if resume:
            unprocessed_stacks = []
            for stack in stacks:
                if not (stack / "stacked").exists():
                    unprocessed_stacks.append(stack)
            print(f"\n🔍 Found {len(unprocessed_stacks)} unprocessed stacks")
            stacks = unprocessed_stacks
        stack_start = time.time()
        print("\n🎨 Processing stacks with HeliconFocus...")
        # Create 'stacked' directory in stack directory
        for stack_dir in stacks:
            output_dir = stack_dir / "stacked"
            print(f"\n📂 Output directory: {output_dir}")
            run_helicon_focus(stack_dir, output_dir, use_tiff, combine_ab)
        
        stack_time = time.time() - stack_start
        print(f"\n⏱️ Total stacking time: {stack_time:.2f} seconds")
    
    # Print total execution time
    total_time = time.time() - total_start
    print(f"\n⏱️ Total execution time: {total_time:.2f} seconds")
