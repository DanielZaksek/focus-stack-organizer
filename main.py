#!/usr/bin/env python3
"""
Main control script for Focus Stack Organizer.
This script provides a command-line interface to control both the focus stack sorter
and Helicon Focus functionality independently.
"""

import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from focus_stack_sorter import stack_images, ImageFormat
from helicon_focus import process_stack


@dataclass
class HeliconConfig:
    """Configuration for Helicon Focus processing.
    
    Args:
        radius: Radius parameter for HeliconFocus (1-8)
        smoothing: Smoothing parameter for HeliconFocus (0-4)
        jpeg_quality: JPEG quality if output_format is 'jpg' (1-100)
        output_format: Output format ('jpg', 'tif', or 'dng')
        combine_ab: Whether to combine methods A and B
    """
    radius: int = 3
    smoothing: int = 1
    jpeg_quality: int = 95
    output_format: str = "dng"
    combine_ab: bool = True

    def __post_init__(self):
        """Validate configuration parameters."""
        if not 1 <= self.radius <= 8:
            raise ValueError("Radius must be between 1 and 8")
        if not 0 <= self.smoothing <= 4:
            raise ValueError("Smoothing must be between 0 and 4")
        if not 1 <= self.jpeg_quality <= 100:
            raise ValueError("JPEG quality must be between 1 and 100")
        if self.output_format not in ["jpg", "tif", "dng"]:
            raise ValueError("Output format must be 'jpg', 'tif', or 'dng'")


def add_helicon_args(parser: argparse.ArgumentParser) -> None:
    """Add Helicon Focus arguments to a parser."""
    parser.add_argument("--radius", type=int, default=3,
                      help="Radius parameter for HeliconFocus (default: 3)")
    parser.add_argument("--smoothing", type=int, default=1,
                      help="Smoothing parameter for HeliconFocus (default: 1)")
    parser.add_argument("--jpeg-quality", type=int, default=95,
                      help="JPEG quality 1-100 (default: 95)")
    parser.add_argument("--output-format", choices=['jpg', 'tif', 'dng'], default='dng',
                      help="Output format (default: dng)")
    parser.add_argument("--no-ab", action="store_true",
                      help="Skip A+B combination in HeliconFocus processing")


def get_helicon_config(args: argparse.Namespace) -> HeliconConfig:
    """Create HeliconConfig from parsed arguments."""
    return HeliconConfig(
        radius=args.radius,
        smoothing=args.smoothing,
        jpeg_quality=args.jpeg_quality,
        output_format=args.output_format,
        combine_ab=not args.no_ab
    )


def process_with_helicon(stack_dir: Path, output_dir: Path, config: HeliconConfig) -> List[Path]:
    """Process a stack with Helicon Focus.
    
    Args:
        stack_dir: Directory containing images to stack
        output_dir: Directory for output files
        config: HeliconFocus configuration
        
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
        radius=config.radius,
        smoothing=config.smoothing,
        jpeg_quality=config.jpeg_quality,
        output_format=config.output_format,
        combine_ab=config.combine_ab
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
