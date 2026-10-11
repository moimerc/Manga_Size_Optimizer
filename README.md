# Manga Size Optimizer

## Project Overview

The **Manga Size Optimizer** is a multi-threaded Python toolkit for reducing the file size of image archives. It handles the extraction, resizing, format conversion (to WebP), and repacking of image directories and ZIP files.

## Components

### 1. `webp_converter.py`

Processes existing ZIP archives to resize and convert internal images.

* **Resizing & Conversion:** Scales down images exceeding a target height (default: 2400px) using Lanczos resampling.
* **WebP Output:** Converts JPG, PNG, and TIFF images to WebP format (default quality: 80). Preserves transparency and color modes during conversion.
* **Repacking:** Extracts the archive to a temporary directory, converts the contents, and repacks them into a new ZIP file.
* **Replacement:** Replaces the original ZIP archive only after the new archive is fully constructed and saved.

### 2. `folder2zip.py`

Compresses raw image directories into ZIP archives using parallel processing.

* **Parallel Archiving:** Compresses multiple directories concurrently using `ZIP_DEFLATED`.
* **Integrity Verification:** Uses `testzip()` and file count matching to verify the generated ZIP archive against the source directory.
* **Source Deletion:** Removes the original source folder only if the verification phase passes without errors or file count mismatches.

## Requirements

* **Python:** 3.8+
* **Dependencies:** `Pillow>=9.0.0`

```bash
pip install Pillow
```

## Usage

1. Open `webp_converter.py` or `folder2zip.py` and set the `BASE_DIR` variable to your target directory.
2. Run the script from the terminal:

**To process existing ZIP archives:**
```bash
python webp_converter.py
```

**To pack directories into ZIP archives:**
```bash
python folder2zip.py
```