# Focus Stack Organizer

Ein Tool zum Organisieren und Stapeln von Fokus-Stacking-Aufnahmen mit Helicon Focus.

## Features

- Automatische Sortierung von Bildern in Fokus-Stacks basierend auf Aufnahmezeiten
- Integration mit Helicon Focus für die Stapelverarbeitung
- Unterstützung für RAW-Formate (ORF, NEF, CR2, ARW, RW2, RAF, DNG) und Standardformate (JPG, TIFF, PNG)
- Automatische Verarbeitung von XMP-Sidecar-Dateien
- Fortschrittsanzeige und detaillierte Statistiken
- Flexible Konfiguration der Stapelverarbeitung

## Installation

1. Stellen Sie sicher, dass Python 3.6 oder höher installiert ist
2. Installieren Sie [Helicon Focus](https://www.heliconsoft.com/heliconsoft-products/helicon-focus/)
3. Installieren Sie exiftool für die EXIF-Datenverarbeitung

```bash
brew install exiftool  # macOS mit Homebrew
```

## Verwendung

Das Tool bietet drei Hauptbefehle:

### 1. Nur Sortieren

```bash
python main.py sort <quell_ordner> [optionen]

Optionen:
  --target-dir <ordner>  Zielordner für sortierte Stacks
  --interval <sekunden>  Zeitintervall zwischen Aufnahmen (Standard: 1.0)
```

### 2. Nur Stapeln

```bash
python main.py stack <stack_ordner> [optionen]

Optionen:
  --output-dir <ordner>  Ausgabeordner für gestapelte Bilder
  --radius <1-8>        Radius-Parameter für HeliconFocus (Standard: 3)
  --smoothing <0-4>     Glättungsparameter für HeliconFocus (Standard: 1)
  --jpeg-quality <1-100> JPEG-Qualität (Standard: 95)
  --output-format <format> Ausgabeformat (jpg, tif, dng) (Standard: dng)
  --no-ab              A+B Kombination überspringen
```

### 3. Sortieren und Stapeln

```bash
python main.py sort-and-stack <quell_ordner> [optionen]

Optionen:
  Kombiniert alle Optionen von 'sort' und 'stack'
```

## Beispiele

```bash
# Bilder sortieren mit 2-Sekunden-Intervall
python main.py sort ~/Bilder/OM1_RAWs --interval 2

# Vorhandene Stacks verarbeiten
python main.py stack ~/Bilder/Stacks --output-format jpg --jpeg-quality 90

# Sortieren und direkt stapeln
python main.py sort-and-stack ~/Bilder/OM1_RAWs --interval 1.5 --radius 4
```

## Unterstützte Bildformate

### RAW-Formate

- ORF (Olympus)
- NEF (Nikon)
- CR2 (Canon)
- ARW (Sony)
- RW2 (Panasonic)
- RAF (Fuji)
- DNG (Adobe)

### Standardformate

- JPG/JPEG
- TIFF/TIF
- PNG

## Verhalten

### Sortierung

- Bilder werden basierend auf ihren EXIF-Aufnahmezeiten gruppiert
- Aufnahmen innerhalb des spezifizierten Zeitintervalls werden als ein Stack behandelt
- Stacks werden als `Stack_XXX` Ordner organisiert (001, 002, etc.)
- XMP-Sidecar-Dateien werden automatisch mit ihren Bildern verschoben

### Stapelverarbeitung

- Verarbeitet Stacks mit Helicon Focus Methoden A, B und C
- Optional wird eine A+B Kombination erstellt
- Überspringt bereits verarbeitete Methoden
- Zeigt Fortschritt und Zeitstatistiken

## Fehlerbehebung

### Keine Stacks erstellt

- Prüfen Sie, ob die Bilder EXIF-Daten enthalten
- Stellen Sie sicher, dass das Zeitintervall groß genug ist
- Überprüfen Sie die unterstützten Bildformate

### Helicon Focus Fehler

- Stellen Sie sicher, dass Helicon Focus installiert ist
- Überprüfen Sie den Pfad zur Helicon Focus Executable
- Prüfen Sie die Berechtigungen des Ausgabeordners 📸

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
- Automatic focus stacking with HeliconFocus:
  - Processes each stack with methods A, B, and C
  - Creates an additional AB combination
  - Supports both RAW/DNG and TIFF formats
  - Saves results in a separate 'stacked' directory

## ⚙️ System Requirements

### Operating System

- macOS
- Linux

### Software

- Python 3.6 or higher
- exiftool (for reading EXIF data)
- HeliconFocus 8 or higher (for automatic stacking)
  - Must be installed in `/Applications/HeliconFocus.app` on macOS

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
python3 focus_stack_sorter.py <source_dir> [target_dir] [options]
```

### Parameters

- `<source_dir>`: Required - Directory containing the original images
- `[target_dir]`: Optional - Directory for sorted stacks

### Options

- `--interval <seconds>`: Optional - Maximum time interval between images in seconds (default: 1)
- `--stack`: Optional - Process stacks with HeliconFocus after organizing
- `--stack-only`: Optional - Process existing stacks with HeliconFocus without sorting
- `--resume`: Optional - Process only unprocessed stacks with HeliconFocus
- `--tiff`: Optional - Use TIFF format for HeliconFocus processing (default: RAW/DNG)
- `--no-ab`: Optional - Skip A+B combination in HeliconFocus processing

### Examples

Here are some common usage examples:

#### Basic Usage

```bash
# Sort images in current directory
python3 focus_stack_sorter.py .

# Sort images from source to target directory
python3 focus_stack_sorter.py ~/Pictures/OM1_RAWs ~/Stacks
```

#### Advanced Usage

```bash
# Sort and stack images with 2 second interval
python3 focus_stack_sorter.py ~/Pictures/OM1_RAWs --interval 2 --stack

# Process existing stacks without sorting
python3 focus_stack_sorter.py ~/Stacks --stack-only

# Resume interrupted stacking (only process unprocessed stacks)
python3 focus_stack_sorter.py ~/Stacks --resume
```

#### Combined Options

```bash
# Process existing unprocessed stacks without sorting
python3 focus_stack_sorter.py ~/Stacks --stack-only --resume

# Process unprocessed stacks in TIFF format without A+B combination
python3 focus_stack_sorter.py ~/Stacks --resume --tiff --no-ab
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

🎨 Processing stacks with HeliconFocus...
📦 Processing Stack_001 with Method A...
✅ Method A completed successfully
📦 Processing Stack_001 with Method B...
✅ Method B completed successfully
📦 Processing Stack_001 with Method C...
✅ Method C completed successfully
📦 Combining methods A and B...
✅ A+B combination completed successfully
...
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
- HeliconFocus must be installed in the default location for stacking
- Stacked results are saved in a 'stacked' subdirectory
- Each stack is processed with methods A, B, C, and A+B combination
- HeliconFocus runs in silent mode (no GUI)

## 🛠 Planned Features

- [x] Support for additional RAW formats and standard image formats
- [x] Configurable time interval for stack detection
- [x] Automatic stacking with HeliconFocus (methods A, B, C and A+B)
- [ ] Graphical User Interface (GUI)
- [ ] Drag & Drop functionality

## 🤝 Contributing

Suggestions for improvements and pull requests are welcome!

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## 👥 Author

Daniel Zaksek
