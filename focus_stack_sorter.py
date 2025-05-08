import os
import sys
import shutil
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Dict, List, Optional, Set
from common import ImageFormat





@dataclass
class SorterConfig:
    """Configuration for focus stack sorting.
    
    Args:
        source_dir: Directory containing images to sort
        target_dir: Optional output directory. If not specified, uses source_dir.
        stack_interval: Time interval in seconds to group images. Default is 1 second.
    """
    source_dir: Path
    target_dir: Optional[Path] = None
    stack_interval: float = 1.0

    def __post_init__(self):
        """Validate and process configuration after initialization."""
        # Convert paths to Path objects
        self.source_dir = Path(self.source_dir)
        if self.target_dir is None:
            self.target_dir = self.source_dir
        else:
            self.target_dir = Path(self.target_dir)
            
        # Validate parameters
        if not self.source_dir.exists():
            raise FileNotFoundError(f"Source directory does not exist: {self.source_dir}")
        if self.stack_interval <= 0:
            raise ValueError("Stack interval must be greater than 0 seconds")


def get_capture_times(filepaths, exif_config=None):
    """Get capture times for multiple files in one exiftool call.
    
    Args:
        filepaths: List of files to process
        exif_config: Optional dictionary with exiftool configuration
            - date_format: Format string for date parsing
            - exif_tag: EXIF tag to read date from
    """
    if exif_config is None:
        from config_manager import ConfigManager
        config = ConfigManager().get_config()
        exif_config = config.get('sorter', {}).get('exiftool', {
            'date_format': '%Y:%m:%d %H:%M:%S',
            'exif_tag': 'DateTimeOriginal'
        })
    
    try:
        # Use exiftool to read EXIF data for all files at once
        cmd = ['exiftool', f"-{exif_config['exif_tag']}", '-d', exif_config['date_format'], '-json']
        cmd.extend(str(f) for f in filepaths)
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error running exiftool: {result.stderr}")
            return {}
            
        # Parse JSON output
        import json
        data = json.loads(result.stdout)
        
        # Create dictionary of filepath -> capture time
        times = {}
        tag_name = exif_config['exif_tag']
        for item in data:
            filepath = Path(item['SourceFile'])
            if tag_name in item:
                try:
                    times[filepath] = datetime.strptime(item[tag_name], exif_config['date_format'])
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



def stack_images(source_dir: Path, target_dir: Optional[Path] = None, stack_interval: Optional[float] = None) -> List[Path]:
    """Sort images into focus stacks based on capture time intervals.
    
    This function analyzes a directory for supported image files and groups them into
    stacks based on their capture times. Images taken within the specified interval
    are considered part of the same stack.
    
    Args:
        source_dir: Directory containing images to sort
        target_dir: Optional output directory. If not specified, uses source_dir.
        stack_interval: Time interval in seconds to group images. Default is 1 second.
        
    Returns:
        List[Path]: List of created stack directories. Each directory contains the
        images for one focus stack and will be named 'Stack_XXX' where XXX is a
        sequential number.
    """
    # Load configuration
    from config_manager import ConfigManager
    config = ConfigManager().get_config()
    focus_config = config.get('sorter', {})
    
    # Use configuration or defaults
    stack_interval = stack_interval or focus_config.get('stack_interval', 1.0)
    min_stack_size = focus_config.get('min_stack_size', 2)
    stack_name_format = focus_config.get('stack_name_format', 'Stack_{:03d}')
    progress_update_count = focus_config.get('progress_update_count', 20)
    
    source_path = Path(source_dir)
    target_path = target_dir if target_dir else source_path
    created_stacks = []  # List of created stack directories
    stack_count = 0  # Initialize stack counter

    print(f"\n🔍 Analyzing directory: {source_path}")
    print("💾 Searching for image files...")
    
    # Get all files and supported extensions
    files = sorted(source_path.glob("*.*"))
    all_extensions = ImageFormat.all_extensions()
    
    # Find all image files
    image_files = [f for f in files if f.suffix.lower() in all_extensions]
    total_images = len(image_files)
    
    if total_images == 0:
        print("⚠️ No supported image files found!")
        print("\nSupported formats:")
        for category, extensions in ImageFormat.extensions().items():
            print(f"{category}: {', '.join(extensions)}")
        return created_stacks
    
    # Count files per format and find XMP files
    format_counts = {}
    xmp_files = []
    for f in files:
        ext = f.suffix.lower()
        if ext == '.xmp':
            xmp_files.append(f)
        elif ext in all_extensions:
            format_counts[ext] = format_counts.get(ext, 0) + 1
    
    print("\n📊 Images found:")
    
    # Group files by categories
    found_categories = {}
    for category, extensions in ImageFormat.extensions().items():
        category_files = []
        for ext in extensions:
            count = format_counts.get(ext.lower(), 0)
            if count > 0:
                category_files.append(f"  - {count}x {ext}")
        if category_files:
            found_categories[category] = category_files
    
    # Zeige gefundene Bilddateien an
    if found_categories:
        for category, files in found_categories.items():
            print(f"\n{category} formats:")
            for line in files:
                print(line)
    
    # Zeige XMP-Dateien an, falls vorhanden
    if xmp_files:
        print(f"\nSidecar files:")
        print(f"  - {len(xmp_files)}x .xmp")
    
    if total_images > 0:
        print(f"\n✅ Total: {total_images} image files")
    
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

    last_time = None
    stack = []
    stack_num = 1
    stacks_created = 0
    files_moved = 0
    stack_sizes = []

    for i, file in enumerate(image_files, 1):
        capture_time = capture_times[file]
        
        # Show progress
        progress = (i / len(image_files)) * 100
        if i % max(1, len(image_files) // progress_update_count) == 0:
            print(f"\r💾 Processing files: {progress:.1f}% ({i}/{len(image_files)})", end="")

        if last_time and (capture_time - last_time).total_seconds() > stack_interval:
            if len(stack) >= min_stack_size:
                stack_dir = target_path / stack_name_format.format(stack_num)
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
    if len(stack) >= min_stack_size:
        stack_dir = target_path / stack_name_format.format(stack_num)
        stack_dir.mkdir(parents=True, exist_ok=True)
        for file in stack:
            move_file_with_sidecar(file, stack_dir)
            files_moved += 1
        created_stacks.append(stack_dir)
        stack_sizes.append(len(stack))
        stacks_created += 1

    print("\r" + " " * 80 + "\r", end="")  # Clear the last progress indicator
    print(f"✅ Done: {stacks_created} stacks created in {target_path.resolve()}")
    # Print stack overview
    if stack_sizes:
        print("\n📂 Stack overview:")
        for i, size in enumerate(stack_sizes, 1):
            stack_dir = target_path / stack_name_format.format(i)
            xmp_count = len(list(stack_dir.glob("*.xmp")))
            xmp_info = f" (+{xmp_count} xmp)" if xmp_count > 0 else ""
            print(f"Stack_{i:03d} → {size[1] if isinstance(size, tuple) else size} images{xmp_info}")
        print(f"\n📁 {files_moved} files moved.")
        print(f"📁 Target directory: {target_path.resolve()}")
    else:
        print("ℹ️ No focus stacks found. Possible reasons:")
        print("  - Images were not taken in rapid succession")
        print("  - Time interval between shots > 1 second")
        print("  - Only single images in directory")
    
    return created_stacks
