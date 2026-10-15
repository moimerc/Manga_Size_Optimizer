# Manga Size Optimizer

## Overview
A multi-threaded Python toolkit for reducing the size of image archives. It handles extraction, resizing, format conversion (to WebP), and repacking of image folders and ZIP files.

## Expected Directory Structure

Both scripts operate in batch mode over `BASE_DIR`, which must contain subfolders and/or ZIP archives — not loose image files.

```text
BASE_DIR/
├── target_item_1.zip
├── target_folder_2/
│   ├── 01.jpg
│   └── 02.jpg
└── target_item_3.zip
```

Set the `BASE_DIR` variable in each script to point to this root.

## Scripts

### `webp_converter.py`
Processes existing ZIP archives: extracts, resizes, and converts internal images to WebP.

* **Resizing**: Scales down images exceeding `TARGET_HEIGHT` (default 2400px) using Lanczos resampling.
* **Conversion**: Converts common image formats (JPG, PNG, BMP, TIFF, WebP) to WebP at `WEBP_QUALITY` (default 80).
* **Repacking**: Rebuilds the ZIP after conversion and replaces the original only once the new archive is fully written.

### `folder2zip.py`
Compresses raw image folders into ZIP archives.

* **Parallel archiving**: Compresses multiple folders concurrently with `ZIP_DEFLATED`.
* **Verification**: Confirms archive integrity via `testzip()` and file count matching.
* **Safe deletion**: Removes the source folder only if verification passes cleanly.

## Requirements
* Python 3.8+
* `Pillow>=9.1.0`

```bash
pip install Pillow
```

## Usage

1. Set `BASE_DIR` in the target script to your input directory.
2. Run:

```bash
python webp_converter.py   # Optimize existing ZIP archives
python folder2zip.py       # Pack folders into ZIP archives
```