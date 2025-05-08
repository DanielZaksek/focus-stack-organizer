import os
import json
import shutil
import subprocess
from concurrent import futures
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from common import ImageFormat
from config_manager import ConfigManager

def get_image_dates(image_paths: List[Path]) -> Dict[Path, datetime]:
    """Extract dates from multiple images in one exiftool call."""
    if not image_paths:
        return {}

    try:
        # Use exiftool to read EXIF data for all files at once
        cmd = ['exiftool', '-DateTimeOriginal', '-d', '%Y:%m:%d %H:%M:%S', '-json'] + [str(f) for f in image_paths]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # Parse JSON output
        data = json.loads(result.stdout)
        
        # Create dictionary of filepath -> capture time
        dates = {}
        for item in data:
            filepath = Path(item['SourceFile'])
            if 'DateTimeOriginal' in item:
                try:
                    dates[filepath] = datetime.strptime(item['DateTimeOriginal'], "%Y:%m:%d %H:%M:%S")
                except ValueError as e:
                    print(f"Error parsing date for {filepath}: {e}")
        
        return dates
        
    except subprocess.CalledProcessError as e:
        print(f"Error running exiftool: {e}")
    except Exception as e:
        print(f"Error processing EXIF data: {e}")
    
    return {}
    
    # If no EXIF data or error, use file modification time
    return datetime.fromtimestamp(os.path.getmtime(image_path))

def check_directory_access(path, is_source=True):
    """
    Check if a directory exists and is accessible.
    
    Args:
        path: Path to check
        is_source: True if this is a source directory, False if destination
    
    Returns:
        tuple: (bool, str) - (success, error_message)
    """
    try:
        path = Path(path)
        if not path.exists():
            if is_source:
                return False, f"Source directory does not exist: {path}"
            # For destination, we'll try to create it
            try:
                path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                return False, f"Could not create destination directory {path}: {e}"
        
        # Check if we can read/write
        if is_source:
            if not os.access(path, os.R_OK):
                return False, f"Cannot read from source directory: {path}"
        else:
            if not os.access(path, os.W_OK):
                return False, f"Cannot write to destination directory: {path}"
                
        return True, ""
    except Exception as e:
        return False, f"Error checking directory {path}: {e}"

def copy_file_with_date(args):
    """Copy a single file to its date-based destination."""
    image_path, date, destination_path, config = args
    try:
        # Create year and date directories
        year_dir = destination_path / str(date.year)
        date_dir = year_dir / date.strftime(config['import']['file_organization']['date_format'])

        year_dir.mkdir(exist_ok=True)
        date_dir.mkdir(exist_ok=True)

        # Copy file to destination
        dest_file = date_dir / image_path.name
        if dest_file.exists() and config['import']['skip_existing']:
            return 'skipped', image_path

        shutil.copy2(image_path, dest_file)

        # Copy XMP file if enabled and exists
        if config['import']['copy_xmp_files']:
            xmp_path = image_path.with_suffix('.xmp')
            if xmp_path.exists():
                shutil.copy2(xmp_path, date_dir / xmp_path.name)

        return 'success', image_path

    except Exception as e:
        print(f"Error copying {image_path}: {e}")
        return 'error', image_path

def import_images(source_path: str, destination_path: Optional[str] = None) -> bool:
    """Import images from source to destination, organizing by date.

    Args:
        source_path: Path to source directory containing images
        destination_path: Optional path to destination directory. If not provided,
                         uses the default_destination from config.

    Returns:
        bool: True if import was successful, False otherwise
    """
    # Load configuration
    config = ConfigManager().get_config()
    
    # Convert paths to Path objects
    source_path = Path(source_path)
    if destination_path is None:
        if not config.get('import', {}).get('default_destination'):
            print("❌ No destination directory specified and no default set in config")
            return False
        destination_path = Path(config['import']['default_destination'])
    else:
        destination_path = Path(destination_path)

    # Check directories
    for path, is_source in [(source_path, True), (destination_path, False)]:
        success, error = check_directory_access(path, is_source)
        if not success:
            print(f"Error accessing {'source' if is_source else 'destination'} directory: {error}")
            return False

    # Find all image files
    print("🔍 Scanning for images...")
    image_files = []
    for root, _, files in os.walk(source_path):
        for file in files:
            if ImageFormat.is_supported(file):
                image_files.append(Path(root) / file)

    if not image_files:
        print("❌ No supported image files found.")
        return False

    print(f"✅ Found {len(image_files)} image files")

    # Get dates for all images in batch
    print("📅 Reading image dates...")
    image_dates = get_image_dates(image_files)
    
    if not image_dates:
        print("❌ Could not extract dates from any images")
        return False

    # Prepare copy operations
    copy_operations = [
        (img, date, destination_path)
        for img, date in image_dates.items()
    ]

    # Process files in parallel
    success_count = error_count = skipped_count = 0
    total = len(copy_operations)

    print("💾 Copying files...")
    with futures.ThreadPoolExecutor(max_workers=config['import']['max_threads']) as executor:
        future_to_file = {executor.submit(copy_file_with_date, args + (config,)): args[0]
                         for args in copy_operations}

        completed = 0
        for future in futures.as_completed(future_to_file):
            completed += 1
            status, file = future.result()
            
            # Update counts
            if status == 'success':
                success_count += 1
            elif status == 'skipped':
                skipped_count += 1
            else:
                error_count += 1

            # Show progress
            progress = (completed / total) * 100
            print(f"\r📊 Progress: {progress:.1f}% ({completed}/{total})", end="")

    # Print summary
    print("\n\n📊 Import Summary:")
    print(f"✅ Successfully copied: {success_count}")
    print(f"⏭️ Skipped (already exist): {skipped_count}")
    print(f"❌ Errors: {error_count}")

    return error_count == 0
