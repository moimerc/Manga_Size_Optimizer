import os
import zipfile
import tempfile
import shutil
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from PIL import Image, ImageOps

# ==================== Configuration ====================
# Set the target directory containing the ZIP archives
BASE_DIR = r"./input_archives"  # Replace with your target directory path
MAX_WORKERS = 4
TARGET_HEIGHT = 2400
WEBP_QUALITY = 80
SUPPORTED_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}

# Lock for safe file replacement across concurrent threads
replace_lock = threading.Lock()

def compress_image(src: str, dst: str) -> bool:
    """
    Compresses and resizes a single image file, saving it in WebP format.
    Handles orientation, transparency, and color mode conversions gracefully.
    """
    try:
        with Image.open(src) as im:
            im = ImageOps.exif_transpose(im)

            # Handle color modes and transparency
            if im.mode == "P":
                if "transparency" in im.info:
                    im = im.convert("RGBA")
                else:
                    im = im.convert("RGB")
            elif im.mode == "LA":
                im = im.convert("RGBA")
            elif im.mode not in ("RGB", "RGBA"):
                im = im.convert("RGB")

            w, h = im.size

            # Resize if the image height exceeds the target height
            if h > TARGET_HEIGHT:
                ratio = TARGET_HEIGHT / float(h)
                new_w = max(1, int(w * ratio))
                im = im.resize((new_w, TARGET_HEIGHT), Image.Resampling.LANCZOS)

            save_kwargs = {
                "format": "WEBP",
                "quality": WEBP_QUALITY,
                "method": 4,
            }
            if im.mode == "RGBA":
                save_kwargs["lossless"] = False

            im.save(dst, **save_kwargs)
            return os.path.exists(dst) and os.path.getsize(dst) > 0

    except Exception:
        return False

def process_zip(zip_name: str) -> str:
    """
    Extracts a ZIP archive, processes all supported images inside, 
    and repacks them into a new optimized ZIP archive.
    """
    zip_path = os.path.join(BASE_DIR, zip_name)
    if not os.path.isfile(zip_path):
        return f"Skipped (Not Found): {zip_name}"

    orig_size = os.path.getsize(zip_path)

    # Create a temporary directory within BASE_DIR to prevent system drive overflow
    temp_dir = tempfile.mkdtemp(prefix="img_batch_", dir=BASE_DIR)
    new_zip_path = zip_path + ".tmp"

    try:
        # 1. Extract ZIP archive
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(temp_dir)

        # 2. Process images
        img_count = 0
        for root, _, files in os.walk(temp_dir):
            for file in files:
                ext = Path(file).suffix.lower()
                if ext not in SUPPORTED_EXTS:
                    continue

                src_path = os.path.join(root, file)
                new_name = Path(file).with_suffix(".webp").name
                dst_path = os.path.join(root, new_name)
                tmp_path = dst_path + ".processing"

                if compress_image(src_path, tmp_path):
                    try:
                        os.remove(src_path)
                    except OSError:
                        pass
                    os.replace(tmp_path, dst_path)
                    img_count += 1
                else:
                    if os.path.exists(tmp_path):
                        try:
                            os.remove(tmp_path)
                        except OSError:
                            pass

        # 3. Create a new optimized ZIP archive
        with zipfile.ZipFile(new_zip_path, "w", compression=zipfile.ZIP_STORED) as zf:
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    full = os.path.join(root, file)
                    arcname = os.path.relpath(full, temp_dir)
                    zf.write(full, arcname)

        new_size = os.path.getsize(new_zip_path)

        # 4. Replace original file (Protected by a brief thread lock)
        with replace_lock:
            for attempt in range(8):
                try:
                    os.replace(new_zip_path, zip_path)
                    break
                except OSError:
                    time.sleep(0.8)
            else:
                return f"Failed to replace (Original kept): {zip_name}"

        ratio = (1 - new_size / orig_size) * 100 if orig_size > 0 else 0
        return (f"Success: {zip_name} "
                f"({img_count} imgs, "
                f"{orig_size/1024/1024:.1f}MB -> {new_size/1024/1024:.1f}MB, "
                f"{ratio:.0f}% reduction)")

    except Exception as e:
        return f"Error: {zip_name} - {e}"

    finally:
        # Cleanup temporary files
        shutil.rmtree(temp_dir, ignore_errors=True)
        if os.path.exists(new_zip_path):
            try:
                os.remove(new_zip_path)
            except OSError:
                pass

def main():
    if not os.path.isdir(BASE_DIR):
        print(f"Error: Target directory does not exist: {BASE_DIR}")
        return

    zips = [f for f in os.listdir(BASE_DIR) if f.lower().endswith(".zip")]
    if not zips:
        print("No ZIP files found in the target directory.")
        return

    print(f"Total {len(zips)} ZIP files found.")
    print(f"Config -> Target Height: {TARGET_HEIGHT}px | WebP Quality: {WEBP_QUALITY} | Workers: {MAX_WORKERS}")
    print("-" * 60)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_zip, z): z for z in zips}
        for future in as_completed(futures):
            print(future.result())

    print("-" * 60)
    print("All tasks completed successfully.")

if __name__ == "__main__":
    main()