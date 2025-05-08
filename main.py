#!/usr/bin/env python3
"""
Main control script for Focus Stack Organizer.
This script provides a command-line interface to control both the focus stack sorter
and Helicon Focus functionality independently.
"""

import os
import sys
import time
import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Set, Tuple

from focus_stack_sorter import stack_images, ImageFormat
from helicon_focus import process_stack
from image_importer import import_images
from config_manager import ConfigManager


def import_only(source_dir: str, destination_dir: Optional[str] = None) -> Tuple[bool, Set[Path]]:
    """Import images from source to destination.
    
    Args:
        source_dir: Directory containing source images
        destination_dir: Optional destination directory
    
    Returns:
        Tuple[bool, Set[Path]]: (success, created_directories)
    """
    print("\n📥 Importing images...")
    return import_images(source_dir, destination_dir)


def import_and_sort(source_dir: str, destination_dir: Optional[str] = None) -> Tuple[bool, List[Path]]:
    """Import images and sort them into stacks.
    
    Args:
        source_dir: Directory containing source images
        destination_dir: Optional destination directory
    
    Returns:
        Tuple[bool, List[Path]]: (success, created_stacks)
    """
    print("\n🔄 Starting import and sort workflow")
    
    # 1. Import images
    success, created_dirs = import_only(source_dir, destination_dir)
    if not success:
        return False, []
    
    if not created_dirs:
        print("❌ No directories were created during import")
        return False, []
    
    # 2. Sort into stacks
    target_dir = max(created_dirs, key=lambda d: d.stat().st_mtime)
    print(f"\n📂 Found target directory: {target_dir}")
    print("\n🔍 Sorting into stacks...")
    
    stacks = stack_images(target_dir)
    return bool(stacks), stacks


def sort_only(directory: str) -> List[Path]:
    """Sort images in a directory into stacks.
    
    Args:
        directory: Directory containing images to sort
    
    Returns:
        List[Path]: Created stack directories
    """
    print("\n🔍 Sorting images into stacks...")
    return stack_images(Path(directory))


def stack_only(directory: str) -> bool:
    """Process a directory with Helicon Focus.
    
    Args:
        directory: Directory containing images to stack
    
    Returns:
        bool: True if successful
    """
    target_dir = Path(directory)
    if not target_dir.exists():
        print(f"\n❌ Directory does not exist: {target_dir}")
        return False
        
    print("\n🔄 Processing with Helicon Focus...")
    output_dir = target_dir / "stacked"
    results = process_with_helicon(target_dir, output_dir)
    return bool(results)


def sort_and_stack(directory: str) -> bool:
    """Sort images into stacks and process with Helicon Focus.
    
    Args:
        directory: Directory containing images to process
    
    Returns:
        bool: True if successful
    """
    print("\n🔄 Starting sort and stack workflow")
    
    # 1. Sort into stacks
    stacks = sort_only(directory)
    if not stacks:
        print("❌ No stacks created")
        return False
    
    # 2. Process with Helicon Focus
    total_stacks = len(stacks)
    for idx, stack_dir in enumerate(stacks, 1):
        print(f"\n📂 Processing stack: {stack_dir.name} ({idx}/{total_stacks})")
        if not stack_only(str(stack_dir)):
            print(f"❌ Failed to process stack {stack_dir.name}")
            continue
        if idx < total_stacks:
            print(f"📊 Progress: {idx}/{total_stacks} stacks completed")
    
    return True


def auto_process(source_dir: str, destination_dir: Optional[str] = None) -> bool:
    """Import, sort, and stack images in one go.
    
    Args:
        source_dir: Directory containing source images
        destination_dir: Optional destination directory
    
    Returns:
        bool: True if successful
    """
    print("\n🔄 Starting automatic processing workflow")
    
    # 1. Import and sort
    success, stacks = import_and_sort(source_dir, destination_dir)
    if not success:
        return False
    
    # 2. Process with Helicon Focus
    print("\n🔄 Processing stacks with Helicon Focus...")
    total_stacks = len(stacks)
    for idx, stack_dir in enumerate(stacks, 1):
        print(f"\n📂 Processing stack: {stack_dir.name} ({idx}/{total_stacks})")
        if not stack_only(str(stack_dir)):
            print(f"❌ Failed to process stack {stack_dir.name}")
            continue
        if idx < total_stacks:
            print(f"📊 Progress: {idx}/{total_stacks} stacks completed")
    
    print("\n✅ Automatic processing complete!")
    return True


from helicon_focus import HeliconConfig, process_stack


def add_helicon_args(parser: argparse.ArgumentParser) -> None:
    """Add Helicon Focus arguments to a parser."""
    # No arguments needed as configuration is handled via config.json
    pass


def get_helicon_config(args: argparse.Namespace) -> HeliconConfig:
    """Create HeliconConfig from config.json."""
    return HeliconConfig.from_config()


def process_with_helicon(stack_dir: Path, output_dir: Path, config: Optional[HeliconConfig] = None) -> List[Path]:
    """Process a stack with Helicon Focus.
    
    Args:
        stack_dir: Directory containing images to stack
        output_dir: Directory for output files
        config: Optional HeliconFocus configuration. If None, uses config.json settings.
        
    Returns:
        List[Path]: Paths to created output files
    """
    # Ensure directories exist
    stack_dir = Path(stack_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    return process_stack(
        stack_dir=stack_dir,
        output_dir=output_dir,
        config=config
    )

    return results or []

def main() -> None:
    """
Main control script for Focus Stack Organizer.
This script provides a command-line interface to control both the focus stack sorter
and Helicon Focus functionality independently.
"""
    """Main entry point for the Focus Stack Organizer."""
    total_start = time.time()
    
    parser = argparse.ArgumentParser(description="Focus Stack Organizer Control Center")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Import command
    import_parser = subparsers.add_parser('import', help='Import images from source to destination')
    import_parser.add_argument('source', help='Source directory containing images')
    import_parser.add_argument('destination', nargs='?', help='Destination directory (optional)')

    # Import and sort command
    import_sort_parser = subparsers.add_parser('import-sort', help='Import images and sort into stacks')
    import_sort_parser.add_argument('source', help='Source directory containing images')
    import_sort_parser.add_argument('destination', nargs='?', help='Destination directory (optional)')

    # Sort command
    sort_parser = subparsers.add_parser('sort', help='Sort images in a directory into stacks')
    sort_parser.add_argument('directory', help='Directory containing images')

    # Stack command
    stack_parser = subparsers.add_parser('stack', help='Process a directory with Helicon Focus')
    stack_parser.add_argument('directory', help='Directory containing images')

    # Sort and stack command
    sort_stack_parser = subparsers.add_parser('sort-stack', help='Sort images into stacks and process with Helicon Focus')
    sort_stack_parser.add_argument('directory', help='Directory containing images')

    # Auto process command
    auto_parser = subparsers.add_parser('auto', help='Import, sort, and stack images in one go')
    auto_parser.add_argument('source', help='Source directory containing images')
    auto_parser.add_argument('destination', nargs='?', help='Destination directory (optional)')

    # Config command
    config_parser = subparsers.add_parser('config', help='Show or modify configuration')
    config_parser.add_argument('--show', action='store_true', help='Show current configuration')
    config_parser.add_argument('--set-import-destination', help='Set default import destination')
    
    args = parser.parse_args()
    
    if args.command == "import":
        success, _ = import_only(args.source, args.destination)
        if success:
            print("\n✅ Import completed successfully")
            sys.exit(0)
        else:
            print("\n❌ Import failed")
            sys.exit(1)
    
    elif args.command == "import-sort":
        success, stacks = import_and_sort(args.source, args.destination)
        if success:
            print(f"\n✅ Successfully created {len(stacks)} stacks")
            sys.exit(0)
        else:
            print("\n❌ Import and sort failed")
            sys.exit(1)
    
    elif args.command == "sort":
        stacks = sort_only(args.directory)
        if stacks:
            print(f"\n✅ Successfully created {len(stacks)} stacks")
            sys.exit(0)
        else:
            print("\n❌ No stacks created")
            sys.exit(1)
    
    elif args.command == "stack":
        if stack_only(args.directory):
            print("\n✅ Stack processed successfully")
            sys.exit(0)
        else:
            print("\n❌ Stack processing failed")
            sys.exit(1)
    
    elif args.command == "sort-stack":
        if sort_and_stack(args.directory):
            print("\n✅ Sort and stack completed successfully")
            sys.exit(0)
        else:
            print("\n❌ Sort and stack failed")
            sys.exit(1)
    
    elif args.command == "auto":
        if auto_process(args.source, args.destination):
            print("\n✅ Automatic processing completed successfully")
            sys.exit(0)
        else:
            print("\n❌ Automatic processing failed")
            sys.exit(1)
    
    elif args.command == "config":
        config_manager = ConfigManager()
        
        if args.set_import_destination:
            config_manager.set_default_destination(args.set_import_destination)
            print(f"\n✅ Default import destination set to: {args.set_import_destination}")
        
        if args.show:
            config = config_manager.get_config()
            print("\nCurrent configuration:")
            print(f"Default import destination: {config.get('import', {}).get('default_destination', 'Not set')}")
            print(f"Import threads: {config.get('import', {}).get('max_threads', 4)}")
            print(f"Skip existing files: {config.get('import', {}).get('skip_existing', True)}")
            print(f"Copy XMP files: {config.get('import', {}).get('copy_xmp_files', True)}")
            print(f"Stack interval: {config.get('sorter', {}).get('stack_interval', 1.0)} seconds")
            print(f"Min stack size: {config.get('sorter', {}).get('min_stack_size', 2)} images")
        
        sys.exit(0)
    
    else:
        parser.print_help()
        sys.exit(1)
    
    # Print total execution time
    total_time = time.time() - total_start
    print(f"\n⏱️ Total execution time: {total_time:.2f} seconds")


if __name__ == "__main__":
    main()
