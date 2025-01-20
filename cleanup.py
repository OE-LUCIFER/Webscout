import os
import shutil

def remove_pycache(directory):
    """
    Recursively remove all __pycache__ directories from the given directory
    """
    removed_count = 0
    for root, dirs, files in os.walk(directory):
        if '__pycache__' in dirs:
            pycache_path = os.path.join(root, '__pycache__')
            try:
                shutil.rmtree(pycache_path)
                print(f"Removed: {pycache_path}")
                removed_count += 1
            except Exception as e:
                print(f"Error removing {pycache_path}: {e}")
    
    return removed_count

if __name__ == "__main__":
    webscout_dir = "webscout"
    count = remove_pycache(webscout_dir)
    print(f"\nTotal __pycache__ directories removed: {count}")
