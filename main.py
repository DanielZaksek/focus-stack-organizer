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
from typing import List, Optional

from focus_stack_sorter import stack_images, ImageFormat
from helicon_focus import process_stack
from image_importer import import_images
from config_manager import ConfigManager


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

import argparse
from pathlib import Path
import sys
import time

from focus_stack_sorter import stack_images
from helicon_focus import process_stack

def main() -> None:
    """Main entry point for the Focus Stack Organizer."""
    parser = argparse.ArgumentParser(description="Focus Stack Organizer Control Center")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Import command
    import_parser = subparsers.add_parser('import', help='Import images from SD card')
    import_parser.add_argument('source_dir', help='Source directory containing images')
    import_parser.add_argument('target_dir', nargs='?', help='Target directory for import')
    import_parser.add_argument('--set-default', action='store_true', help='Set target directory as default destination')

    # Config commands
    config_parser = subparsers.add_parser("config", help="Configure default settings")
    config_parser.add_argument("--set-import-destination", help="Set default import destination directory")
    config_parser.add_argument("--show", action="store_true", help="Show current configuration")

    # Focus Stack Sorter command
    sort_parser = subparsers.add_parser("sort", help="Sort and organize focus stacks")
    sort_parser.add_argument("source_dir", help="Source directory containing images")
    sort_parser.add_argument("--target-dir", help="Target directory for sorted stacks")
    sort_parser.add_argument("--interval", type=float, default=1.0,
                          help="Time interval between shots to separate stacks (default: 1.0)")

    # Combined sort and stack command
    sort_stack_parser = subparsers.add_parser("sort-and-stack", help="Sort images into stacks and process with Helicon Focus")
    sort_stack_parser.add_argument("source_dir", help="Source directory containing images")
    sort_stack_parser.add_argument("--target-dir", help="Target directory for sorted stacks")
    sort_stack_parser.add_argument("--interval", type=float, default=1.0,
                                help="Time interval between shots to separate stacks (default: 1.0)")
    add_helicon_args(sort_stack_parser)

    # Helicon Focus command
    stack_parser = subparsers.add_parser("stack", help="Process stacks with Helicon Focus")
    stack_parser.add_argument("stack_dir", help="Directory containing images to stack")
    stack_parser.add_argument("--output-dir", help="Output directory for stacked images")
    add_helicon_args(stack_parser)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Start total time measurement
    total_start = time.time()

    if args.command == "sort":
        source_path = Path(args.source_dir)
        target_path = Path(args.target_dir) if args.target_dir else source_path

        print(f"\n🔍 Starting Focus Stack Sorter")
        print(f"Source directory: {source_path}")
        print(f"Target directory: {target_path}")
        print(f"Stack interval: {args.interval} seconds")

        stacks = stack_images(source_path, target_path, args.interval)
        if stacks:
            print(f"\n✅ Successfully created {len(stacks)} stacks")

    elif args.command == "stack":
        stack_path = Path(args.stack_dir)
        config = get_helicon_config(args)

        # Check if the path contains Stack_XXX directories and sort them by number
        stack_dirs = [d for d in stack_path.iterdir() if d.is_dir() and d.name.startswith("Stack_")]
        # Sort by the numeric part of Stack_XXX
        stack_dirs.sort(key=lambda x: int(x.name.split('_')[1]))

        if stack_dirs:
            # Case 2: Found Stack_XXX directories
            print(f"\n📂 Found {len(stack_dirs)} stack directories")
            response = input("\nDo you want to process these stack directories? [y/N]: ").lower()
            
            if response == 'y':
                total_stacks = len(stack_dirs)
                for idx, stack_dir in enumerate(stack_dirs, 1):
                    print(f"\n📚 Processing stack directory: {stack_dir.name} ({idx}/{total_stacks})")
                    output_path = stack_dir / "stacked"
                    process_with_helicon(stack_dir, output_path, config)
                    if idx < total_stacks:
                        print(f"📊 Progress: {idx}/{total_stacks} stacks completed")
            else:
                print("\n⏹ Skipping stack directories")

        # Case 1: Check for images in the current directory
        image_files = []
        for ext in ImageFormat.all_extensions():
            image_files.extend(stack_path.glob(f"*{ext}"))
            image_files.extend(stack_path.glob(f"*{ext.upper()}"))

        if len(image_files) <= 1:
            print(f"\n⚠️ Not enough images found in {stack_path} (found: {len(image_files)})")
            print("At least 2 images are required for focus stacking.")
            sys.exit(1)

        # Process images in the current directory
        print(f"\n📚 Found {len(image_files)} images in directory")
        output_path = Path(args.output_dir) if args.output_dir else stack_path / "stacked"
        process_with_helicon(stack_path, output_path, config)

    elif args.command == "config":
        config_manager = ConfigManager()
        
        if args.set_import_destination:
            config_manager.set_default_import_destination(args.set_import_destination)
            print(f"\n✅ Default import destination set to: {args.set_import_destination}")
        
        if args.show:
            default_import_dest = config_manager.get_default_import_destination()
            print("\nCurrent configuration:")
            print(f"Default import destination: {default_import_dest or 'Not set'}")

    elif args.command == "import":
        config_manager = ConfigManager()
        source_path = Path(args.source_dir)
        
        # Use target_dir if provided, otherwise use default from config
        target_path = None
        if args.target_dir:
            target_path = Path(args.target_dir)
        else:
            target_path = config_manager.get_default_destination()
        if not target_path:
            print("❌ No target directory specified and no default set in config")
            return

        # Set as default if requested
        if args.set_default:
            config_manager.set_default_destination(target_path)

        print(f"\n📸 Starting Image Import")
        print(f"Source directory: {source_path}")
        print(f"Target directory: {target_path}")

        if import_images(source_path, target_path):
            print("\n✅ Import complete!")
        else:
            sys.exit(1)

    elif args.command == "sort-and-stack":
        source_path = Path(args.source_dir)
        target_path = Path(args.target_dir) if args.target_dir else source_path

        print(f"\n🔍 Starting Focus Stack Sorter")
        print(f"Source directory: {source_path}")
        print(f"Target directory: {target_path}")
        print(f"Stack interval: {args.interval} seconds")

        # First sort the images into stacks
        stacks = stack_images(source_path, target_path, args.interval)
        if not stacks:
            print("\n❌ No stacks were created")
            sys.exit(1)
            
        # Sort stacks by their number
        stacks.sort(key=lambda x: int(x.name.split('_')[1]))

        print(f"\n✅ Successfully created {len(stacks)} stacks")
        print("\n🔄 Now processing each stack with Helicon Focus...")

        # Then process each stack with Helicon Focus
        config = get_helicon_config(args)
        total_results = []
        total_stacks = len(stacks)
        
        for idx, stack_dir in enumerate(stacks, 1):
            print(f"\n📂 Processing stack: {stack_dir.name} ({idx}/{total_stacks})")
            output_path = stack_dir / "stacked"
            results = process_with_helicon(stack_dir, output_path, config)
            total_results.extend(results)
            if idx < total_stacks:
                print(f"📊 Progress: {idx}/{total_stacks} stacks completed")

        print(f"\n🎉 Complete! Created {len(total_results)} stacked images from {len(stacks)} stacks")

    # Print total execution time
    total_time = time.time() - total_start
    print(f"\n⏱️ Total execution time: {total_time:.2f} seconds")

if __name__ == "__main__":
    main()
