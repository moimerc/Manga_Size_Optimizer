import os
import shutil
import zipfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# ==================== Configuration ====================
# Target directory containing the folders to be archived
BASE_DIR = r"./input_folders"  # Replace with actual target path
MAX_WORKERS = 8

# Lock to prevent race conditions during folder deletion
delete_lock = threading.Lock()

def count_files(folder_path: str) -> int:
    """Counts the total number of files within a directory and its subdirectories."""
    n = 0
    for _, _, files in os.walk(folder_path):
        n += len(files)
    return n

def process_folder(folder_name: str) -> str:
    """
    Compresses a folder into a ZIP archive, verifies its integrity,
    and safely removes the original folder upon successful verification.
    """
    folder_path = os.path.join(BASE_DIR, folder_name)
    zip_path = os.path.join(BASE_DIR, folder_name + ".zip")

    if not os.path.isdir(folder_path):
        return f"Skipped (Not a folder): {folder_name}"

    # 1. Count original files
    try:
        original_count = count_files(folder_path)
        if original_count == 0:
            return f"Skipped (Empty folder): {folder_name}"
    except Exception as e:
        return f"Error (Counting): {folder_name} - {e}"

    # 2. Compress the folder (Runs in parallel)
    try:
        with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=1) as zf:
            for root, _, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, folder_path)
                    zf.write(file_path, arcname)
    except Exception as e:
        # Clean up incomplete zip file on failure
        if os.path.exists(zip_path):
            try:
                os.remove(zip_path)
            except OSError:
                pass
        return f"Compression Error: {folder_name} - {e}"

    # 3. Strict Verification
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            # Count only files (exclude directory entries)
            zip_count = len([n for n in zf.namelist() if not n.endswith('/')])
            bad_file = zf.testzip()
            if bad_file is not None:
                return f"Corruption Detected, Original Kept: {folder_name} ({bad_file})"
    except Exception as e:
        return f"Verification Failed, Original Kept: {folder_name} - {e}"

    if zip_count != original_count:
        return f"Count Mismatch ({zip_count}/{original_count}), Original Kept: {folder_name}"

    # 4. Safely remove original folder (Protected by Lock)
    time.sleep(0.2)
    with delete_lock:
        for attempt in range(6):
            try:
                shutil.rmtree(folder_path)
                return f"Success: {folder_name}.zip ({zip_count} files)"
            except OSError as e:
                # Handle Windows Error 32: Process cannot access the file because it is being used
                if getattr(e, 'winerror', None) == 32:
                    time.sleep(1.5)
                    continue
                else:
                    return f"Deletion Error: {folder_name} - {e}"
        return f"Deletion Failed (Locked), Original Kept: {folder_name}"

def main():
    if not os.path.exists(BASE_DIR):
        print(f"Directory not found: {BASE_DIR}")
        return

    folders = [
        i for i in os.listdir(BASE_DIR)
        if os.path.isdir(os.path.join(BASE_DIR, i))
    ]

    if not folders:
        print("No folders found to compress.")
        return

    print(f"Total {len(folders)} folders / Max Workers: {MAX_WORKERS}\n")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_folder, f): f for f in folders}
        for future in as_completed(futures):
            print(future.result())

    print("\nAll tasks completed.")

if __name__ == "__main__":
    main()