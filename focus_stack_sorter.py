import os
import sys
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from common import ImageFormat

# Konstanten für die Optimierung
BATCH_SIZE = 100  # Anzahl der Dateien pro Batch für exiftool
MAX_WORKERS = 4   # Maximale Anzahl paralleler Threads


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


def process_batch(batch: List[Path], exif_config: dict) -> Dict[Path, datetime]:
    """Process a batch of files with exiftool."""
    try:
        cmd = ['exiftool', f"-{exif_config['exif_tag']}", '-d', exif_config['date_format'], '-json']
        cmd.extend(str(f) for f in batch)
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error running exiftool for batch: {result.stderr}")
            return {}
            
        import json
        data = json.loads(result.stdout)
        
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
        print(f"Error processing batch: {e}")
        return {}

def get_capture_times(filepaths: List[Path], exif_config=None) -> Dict[Path, datetime]:
    """Get capture times for multiple files using parallel batch processing.
    
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
    
    # Teile Dateien in Batches auf
    batches = [filepaths[i:i + BATCH_SIZE] for i in range(0, len(filepaths), BATCH_SIZE)]
    
    # Verarbeite Batches parallel
    all_times = {}
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_batch = {executor.submit(process_batch, batch, exif_config): batch 
                         for batch in batches}
        
        for future in future_to_batch:
            try:
                times = future.result()
                all_times.update(times)
            except Exception as e:
                print(f"Error processing batch: {e}")
    
    return all_times

def move_files_batch(files: List[Tuple[Path, Path]], xmp_check: bool = True) -> int:
    """Move multiple files and their XMP sidecars in parallel.
    
    Args:
        files: List of (source_path, target_dir) tuples
        xmp_check: Whether to check and move XMP sidecar files
    
    Returns:
        Number of files moved
    """
    moved = 0
    
    def move_single(src_target: Tuple[Path, Path]) -> int:
        try:
            src, target = src_target
            shutil.move(str(src), target)
            count = 1
            
            if xmp_check:
                xmp_path = src.with_suffix('.xmp')
                if xmp_path.exists():
                    shutil.move(str(xmp_path), target)
                    count += 1
            return count
        except Exception as e:
            print(f"Error moving {src}: {e}")
            return 0
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for count in executor.map(move_single, files):
            moved += count
    
    return moved



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
        List[Path]: Created stack directories. Each directory contains the image
        files for one focus stack and will be named 'Stack_XXX' where XXX is a
        sequential number.
    """
    # Load configuration
    from config_manager import ConfigManager
    config = ConfigManager().get_config()
    
    # Initialize configuration
    sorter_config = config.get('sorter', {})
    min_stack_size = sorter_config.get('min_stack_size', 2)
    stack_name_format = sorter_config.get('stack_name_format', 'Stack_{:03d}')
    progress_update_count = sorter_config.get('progress_updates', 20)
    
    if stack_interval is None:
        stack_interval = sorter_config.get('stack_interval', 1.0)
    
    # Create target directory if not exists
    target_path = Path(target_dir) if target_dir else source_dir
    target_path.mkdir(parents=True, exist_ok=True)
    
    # Get all supported image formats
    all_extensions = set()
    for extensions in ImageFormat.extensions().values():
        all_extensions.update(extensions)
    
    # Find all image files
    print("\n🔍 Finding image files...")
    image_files = []
    xmp_files = []
    format_counts = {}
    total_images = 0
    
    for f in source_dir.rglob('*'):
        if not f.is_file():
            continue
            
        ext = f.suffix.lower()
        if ext == '.xmp':
            xmp_files.append(f)
        elif ext in all_extensions:
            image_files.append(f)
            format_counts[ext] = format_counts.get(ext, 0) + 1
            total_images += 1
    
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
    
    # Get capture times for all files at once (bereits optimiert durch Batching)
    print("📅 Reading EXIF data in batch mode...")
    capture_times = get_capture_times(image_files)
    
    # Filter files with EXIF data
    image_files = [f for f in image_files if f in capture_times]
    if len(image_files) < total_images:
        print(f"⚠️ {total_images - len(image_files)} files without EXIF data found and skipped.")
    
    if not image_files:
        print("❌ No usable files found!")
        return []

    # Sortiere Dateien nach Aufnahmezeit
    sorted_files = sorted(image_files, key=lambda f: capture_times[f])
    
    # Identifiziere Stacks basierend auf Zeitintervallen
    stacks = []
    current_stack = []
    last_time = None
    
    for file in sorted_files:
        capture_time = capture_times[file]
        if last_time and (capture_time - last_time).total_seconds() > stack_interval:
            if len(current_stack) >= min_stack_size:
                stacks.append(current_stack)
            current_stack = []
        current_stack.append(file)
        last_time = capture_time
    
    # Letzten Stack hinzufügen, wenn groß genug
    if len(current_stack) >= min_stack_size:
        stacks.append(current_stack)
    
    # Erstelle Stack-Verzeichnisse parallel
    created_stacks = []
    files_to_move = []
    stack_sizes = []
    
    for stack_num, stack_files in enumerate(stacks, 1):
        stack_dir = target_path / stack_name_format.format(stack_num)
        stack_dir.mkdir(parents=True, exist_ok=True)
        created_stacks.append(stack_dir)
        stack_sizes.append((stack_num, len(stack_files)))
        
        # Sammle alle Dateien zum Verschieben
        files_to_move.extend([(f, stack_dir) for f in stack_files])
    
    # Verschiebe Dateien parallel
    print("\n📦 Moving files in parallel...")
    files_moved = move_files_batch(files_to_move)

    print("\r" + " " * 80 + "\r", end="")  # Clear the last progress indicator
    print(f"✅ Done: {len(created_stacks)} stacks created in {target_path.resolve()}")
    
    # Print stack overview
    if stack_sizes:
        print("\n📂 Stack overview:")
        for stack_num, size in stack_sizes:
            stack_dir = target_path / stack_name_format.format(stack_num)
            xmp_count = len(list(stack_dir.glob("*.xmp")))
            xmp_info = f" (+{xmp_count} xmp)" if xmp_count > 0 else ""
            print(f"Stack_{stack_num:03d} → {size} images{xmp_info}")
        print(f"\n📁 {files_moved} files moved.")
        print(f"📁 Target directory: {target_path.resolve()}")
    else:
        print("ℹ️ No focus stacks found. Possible reasons:")
        print("  - Images were not taken in rapid succession")
        print("  - Time interval between shots > 1 second")
        print("  - Only single images in directory")
    
    return created_stacks
