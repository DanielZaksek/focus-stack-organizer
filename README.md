# Focus Stack Organizer 📸

A tool for organizing and stacking focus stacking images with Helicon Focus. Perfect for macro and product photography with cameras like the Olympus OM-1 that support focus bracketing.

## Features 🌟

- Automatic sorting of images into focus stacks based on capture times
- Integration with Helicon Focus for batch processing
- Support for RAW formats (ORF, NEF, CR2, ARW, RW2, RAF, DNG) and standard formats (JPG, TIFF, PNG)
- Automatic handling of XMP sidecar files
- Progress display and detailed statistics
- Flexible stack processing configuration

## Requirements

- Python 3.6 or higher
- Helicon Focus (for stacking)
- ExifTool (for reading metadata)

## Installation

1. Clone this repository
2. Install requirements: `pip install -r requirements.txt`
3. Install ExifTool: [Download ExifTool](https://exiftool.org)
4. Install Helicon Focus: [Download Helicon Focus](https://www.heliconsoft.com/heliconsoft-products/helicon-focus/)

## Available Commands

### 1. Import Only

Import images from source to destination, organizing by date:

```bash
python3 main.py import <source_dir> [destination_dir]
```

Example:

```bash
python3 main.py import /path/to/sd-card /path/to/photos
```

### 2. Import and Sort

Import images and sort them into stacks:

```bash
python3 main.py import-sort <source_dir> [destination_dir]
```

Example:

```bash
python3 main.py import-sort /path/to/sd-card /path/to/photos
```

### 3. Sort Only

Sort existing images in a directory into stacks:

```bash
python3 main.py sort <directory>
```

Example:

```bash
python3 main.py sort /path/to/photos/2025/2025-05-08
```

### 4. Stack Only

Process a directory with Helicon Focus:

```bash
python3 main.py stack <directory>
```

Example:

```bash
python3 main.py stack /path/to/photos/2025/2025-05-08/Stack_1
```

### 5. Sort and Stack

Sort images into stacks and process with Helicon Focus:

```bash
python3 main.py sort-stack <directory>
```

Example:

```bash
python3 main.py sort-stack /path/to/photos/2025/2025-05-08
```

### 6. Automatic Workflow

Import, sort, and stack images in one go:

```bash
python3 main.py auto <source_dir> [destination_dir]
```

Example:

```bash
python3 main.py auto /path/to/sd-card /path/to/photos
```

## Configuration

The application is configured via `config.json`. Here's a full example with all available options:

```json
{
    "import": {
        "default_destination": "/path/to/photos",
        "max_threads": 4,
        "skip_existing": true,
        "copy_xmp_files": true
    },
    "sorter": {
        "stack_interval": 1.0,
        "min_stack_size": 2,
        "stack_name_format": "Stack_{:03d}"
    },
    "helicon": {
        "method": "A",
        "radius": 8,
        "smoothing": 4,
        "quality": 3
    }
}
```

### Example Configuration

Here's a practical example for macro photography with an Olympus OM-1:

```json
{
    "import": {
        "default_destination": "~/Pictures/Macro",
        "max_threads": 8,
        "skip_existing": true,
        "copy_xmp_files": true
    },
    "sorter": {
        "stack_interval": 1,
        "min_stack_size": 2,
        "stack_name_format": "Stack_{:03d}"
    },
    "helicon_focus": {
       "radius": 3,
       "smoothing": 1,
       "jpeg_quality": 95,
       "output_format": "dng",
       "helicon_path": "/Applications/HeliconFocus.app/Contents/MacOS/HeliconFocus",
       "vertical_adjustment": 25,
       "horizontal_adjustment": 25,
       "rotation_adjustment": 25,
       "magnification_adjustment": 10,
       "brightness_adjustment": true,
       "interpolation_method": "LANCZOS3",
       "methods": {
            "A": true,
            "B": true,
            "C": true,
            "AB": true
        }
    }
}
```

### Configuration Options

#### Import Settings

- `default_destination`: Default path for imported images
- `max_threads`: Number of parallel copy operations (default: 4)
- `skip_existing`: Skip files that already exist (default: true)
- `copy_xmp_files`: Copy XMP sidecar files if they exist (default: true)

#### Sorter Settings

- `stack_interval`: Time interval between shots to separate stacks (seconds)
- `min_stack_size`: Minimum number of images to create a stack (default: 2)
- `stack_name_format`: Format string for stack directory names

#### Helicon Focus Settings

##### Basic Parameters

- `radius`: Radius parameter (1-8) - Higher values include more distant areas when calculating the depth map
- `smoothing`: Smoothing parameter (0-4) - Higher values reduce noise but may also reduce sharpness
- `jpeg_quality`: Output quality (1-100) - Only used when output_format is 'jpg'
- `output_format`: Output format ('dng', 'jpg', 'tif') - DNG preserves the most information
- `helicon_path`: Path to Helicon Focus executable

##### Image Alignment Parameters

- `vertical_adjustment`: Vertical shift adjustment (0-100, default: 25)
  - Controls the maximum vertical shift when aligning images
- `horizontal_adjustment`: Horizontal shift adjustment (0-100, default: 25)
  - Controls the maximum horizontal shift when aligning images
- `rotation_adjustment`: Rotation adjustment (0-100, default: 25)
  - Controls the maximum rotation angle when aligning images
- `magnification_adjustment`: Magnification adjustment (0-100, default: 10)
  - Controls the maximum scale change when aligning images
- `brightness_adjustment`: Brightness adjustment (0-100, default: 25)
  - Controls the brightness equalization between images

##### Interpolation Method

- `interpolation_method`: Image interpolation method (default: LANCZOS8)
  - `BILINEAR`: Bilinear interpolation (fastest, lowest quality)
  - `BICUBIC`: Bicubic interpolation (good balance of speed/quality)
  - `LANCZOS3`: Lanczos-3 interpolation (high quality)
  - `LANCZOS8`: Lanczos-8 interpolation (highest quality, slowest)

##### Stacking Methods

- `methods`: Methods to process (A, B, C, AB)
  - `A`: Better for sharp edges and high contrast (true/false)
  - `B`: Better for smooth transitions (true/false)
  - `C`: Combination of A and B characteristics (true/false)
  - `AB`: Creates a combination of methods A and B (true/false)

### Managing Configuration

View current configuration:

```bash
python3 main.py config --show
```

Set default import destination:

```bash
python3 main.py config --set-import-destination /path/to/photos
```

## Directory Structure

The importer creates a date-based directory structure:

```text
/path/to/photos/
    └── 2025/
        └── 2025-05-08/
            ├── Stack_001/
            │   ├── IMG_0001.CR3
            │   ├── IMG_0002.CR3
            │   └── stacked/
            │       └── stack.jpg
            └── Stack_002/
                ├── IMG_0003.CR3
                ├── IMG_0004.CR3
                └── stacked/
                    └── stack.jpg
```

## Examples

```bash
python3 main.py import /path/to/sd-card /path/to/photos
python3 main.py import-sort /path/to/sd-card /path/to/photos
python3 main.py sort /path/to/photos/2025/2025-05-08
python3 main.py stack /path/to/photos/2025/2025-05-08/Stack_1
python3 main.py sort-stack /path/to/photos/2025/2025-05-08
python3 main.py auto /path/to/sd-card /path/to/photos
python main.py sort ~/Pictures/OM1_RAWs --interval 2

# Process existing stacks
python main.py stack ~/Pictures/Stacks --output-format jpg --jpeg-quality 90

# Sort and stack directly
python main.py sort-and-stack ~/Pictures/OM1_RAWs --interval 1.5 --radius 4
```

## Supported Image Formats

### RAW Formats

- ORF (Olympus)
- NEF (Nikon)
- CR2 (Canon)
- ARW (Sony)
- RW2 (Panasonic)
- RAF (Fuji)
- DNG (Adobe)

### Standard Formats

- JPG/JPEG
- TIFF/TIF
- PNG

## Behavior

### Sorting

- Images are grouped based on their EXIF capture times
- Captures within the specified time interval are treated as one stack
- Stacks are organized as `Stack_XXX` folders (001, 002, etc.)
- XMP sidecar files are automatically moved with their images

### Stack Processing

- Processes stacks with Helicon Focus methods A, B, and C
- Optionally creates an A+B combination
- Skips already processed methods
- Shows progress and time statistics

## Troubleshooting

### No Stacks Created

- Check if images contain EXIF data
- Ensure the time interval is large enough
- Verify supported image formats

### Helicon Focus Errors

- Make sure Helicon Focus is installed
- Check the path to the Helicon Focus executable
- Verify output directory permissions

## Contributing 🤝

Contributions, issues, and feature requests are welcome!

## License 📝

This project is licensed under the MIT License - see the LICENSE file for details.
