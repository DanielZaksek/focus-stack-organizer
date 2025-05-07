# Focus Stack Sorter 📸

A Python script for automatically organizing focus-stacking image series. Perfect for macro and product photography with cameras like the Olympus OM-1 that support focus bracketing.

## 🎯 Key Features

- Automatically detects focus bracketing series based on capture time
- Sorts related images into separate folders (`Stack_001`, `Stack_002`, etc.)
- Supports various image formats:
  - RAW: `.orf`, `.nef`, `.cr2`, `.arw`, `.rw2`, `.raf`, `.dng` (Olympus, Nikon, Canon, Sony, Panasonic, Fuji, Adobe)
  - Standard: `.jpg`, `.jpeg`, `.tiff`, `.tif`, `.png`
- Moves files and associated `.xmp` sidecar files
- Leaves single images untouched
- Detailed progress display and stack overview
- Optional target directory for sorted stacks

## ⚙️ System Requirements

### Operating System

- macOS
- Linux

### Software

- Python 3.6 or higher
- exiftool (for reading EXIF data)

## 📥 Installation

1. **Install Python and exiftool** (if not already installed)

   ```bash
   # macOS with Homebrew
   brew install python exiftool

   # Linux (Ubuntu/Debian)
   sudo apt update
   sudo apt install python3 python3-pip exiftool
   ```

2. **Download project**

   ```bash
   git clone https://github.com/DanielZaksek/focus-stack-organizer.git
   cd focus-stack-organizer
   ```

3. **Create and activate virtual environment**

   ```bash
   # Create virtual environment
   python3 -m venv venv

   # Activate virtual environment
   # On macOS/Linux:
   source venv/bin/activate
   # On Windows:
   # venv\Scripts\activate
   ```

## 🚀 Usage

### Basic Syntax

```bash
python3 focus_stack_sorter.py <source_dir> [target_dir]
```

### Parameters

- `<source_dir>`: Required - Directory containing the original images
- `[target_dir]`: Optional - Directory for sorted stacks
- `--interval <seconds>`: Optional - Maximum time interval between images in seconds (default: 1)

### Examples

1. **Create stacks in source directory**

   ```bash
   python3 focus_stack_sorter.py ~/Pictures/OM1_RAWs
   ```

2. **Create stacks in separate target directory**

   ```bash
   python3 focus_stack_sorter.py ~/Pictures/OM1_RAWs ~/Stacks
   ```

3. **Adjust time interval (2 seconds)**

   ```bash
   python3 focus_stack_sorter.py ~/Pictures/OM1_RAWs --interval 2
   ```

4. **Target directory and time interval (0.5 seconds)**

   ```bash
   python3 focus_stack_sorter.py ~/Pictures/OM1_RAWs ~/Stacks --interval 0.5
   ```

### Example Output

```bash
🔍 Analyzing directory: ~/Pictures/OM1_RAWs
💾 Searching for image files...
✅ 150 image files found.
📅 Reading EXIF data...
⚙️ Analyzing time intervals between 150 images...
💾 Processing file 150/150...

✅ Done: 12 stacks created.

📂 Stack overview:
Stack_001 → 15 images
Stack_002 → 12 images
Stack_003 → 8 images
...

📁 144 files moved.
📁 Target directory: ~/Stacks
```

## 📝 How It Works

1. The script scans the source directory for supported image files
2. It reads the EXIF capture time of each file using exiftool
3. Images taken within the specified time interval are recognized as a series (default: 1 second)
4. For each series (> 1 image), a new folder is created (`Stack_001`, etc.)
5. The images and their `.xmp` sidecar files are moved to the stack folders
6. Single images remain in the source directory

## ⚠️ Important Notes

- Back up your images before using the script
- The script moves files (no copies)
- Supports various RAW and standard image formats
- Associated `.xmp` files are automatically moved
- Make sure you have write permissions in the directories

## 🛠 Planned Features

- [x] Support for additional RAW formats and standard image formats
- [x] Configurable time interval for stack detection
- [ ] Graphical User Interface (GUI)
- [ ] Drag & Drop functionality
- [ ] Stack content preview

## 🤝 Contributing

Suggestions for improvements and pull requests are welcome!

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## 👥 Author

Daniel Zaksek
