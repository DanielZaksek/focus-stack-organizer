# Focus Stack Organizer 📸

A tool for organizing and stacking focus stacking images with Helicon Focus. Perfect for macro and product photography with cameras like the Olympus OM-1 that support focus bracketing.

## Features 🌟

- Automatic sorting of images into focus stacks based on capture times
- Integration with Helicon Focus for batch processing
- Support for RAW formats (ORF, NEF, CR2, ARW, RW2, RAF, DNG) and standard formats (JPG, TIFF, PNG)
- Automatic handling of XMP sidecar files
- Progress display and detailed statistics
- Flexible stack processing configuration

## Roadmap 🎯

- [x] Basic focus stack sorting
- [x] Support for RAW formats
- [x] XMP sidecar file handling
- [x] Automatic stacking with HeliconFocus (methods A, B, C and A+B)
- [ ] Graphical User Interface (GUI)
- [ ] Drag & Drop functionality

## Prerequisites 📋

- Python 3.6 or higher
- [Helicon Focus](https://www.heliconsoft.com/heliconsoft-products/helicon-focus/)
- ExifTool for EXIF data processing

## Installation 🔧

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/focus-stack-organizer.git
   cd focus-stack-organizer
   ```

2. Install ExifTool:

   ```bash
   # macOS with Homebrew
   brew install exiftool

   # Linux (Debian/Ubuntu)
   sudo apt-get install exiftool

   # Windows
   # Download ExifTool from https://exiftool.org/
   ```

3. Install [Helicon Focus](https://www.heliconsoft.com/heliconsoft-products/helicon-focus/)

## Usage 🚀

The tool provides three main commands:

### 1. Sort Only

```bash
python main.py sort <source_dir> [options]

Options:
  --target-dir <dir>    Target directory for sorted stacks
  --interval <seconds>  Time interval between captures (default: 1.0)
```

### 2. Stack Only

```bash
python main.py stack <stack_dir> [options]

Options:
  --output-dir <dir>    Output directory for stacked images
  --radius <1-8>       Radius parameter for HeliconFocus (default: 3)
  --smoothing <0-4>    Smoothing parameter for HeliconFocus (default: 1)
  --jpeg-quality <1-100> JPEG quality (default: 95)
  --output-format <format> Output format (jpg, tif, dng) (default: dng)
  --no-ab             Skip A+B combination
```

### 3. Sort and Stack

```bash
python main.py sort-and-stack <source_dir> [options]

Options:
  Combines all options from 'sort' and 'stack'
```

## Examples

```bash
# Sort images with 2-second interval
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
