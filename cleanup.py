from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Set


@dataclass
class CleanupResult:
    """Result of cleanup operation"""
    removed_count: int
    removed_paths: Set[Path]
    errors: List[tuple[Path, Exception]]


class DirectoryCleaner:
    """Handles cleaning of Python build artifacts and cache directories"""
    
    BUILD_ARTIFACTS = frozenset({
        "build",
        "dist",
        "webscout.egg-info"
    })

    def __init__(self, base_dir: str | Path) -> None:
        """Initialize with base directory path
        
        Args:
            base_dir: Base directory to clean
        """
        self.base_dir = Path(base_dir)
        if not self.base_dir.exists():
            raise ValueError(f"Directory does not exist: {self.base_dir}")
        if not self.base_dir.is_dir():
            raise ValueError(f"Path is not a directory: {self.base_dir}")

    def remove_directory(self, path: Path) -> Optional[Exception]:
        """Safely remove a directory
        
        Args:
            path: Directory path to remove
            
        Returns:
            Exception if removal failed, None if successful
        """
        try:
            shutil.rmtree(path)
            return None
        except Exception as e:
            return e

    def cleanup(self) -> CleanupResult:
        """Clean build artifacts and cache directories
        
        Returns:
            CleanupResult containing statistics and errors
        """
        removed_count: int = 0
        removed_paths: Set[Path] = set()
        errors: List[tuple[Path, Exception]] = []

        # Remove build artifacts
        for artifact in self.BUILD_ARTIFACTS:
            artifact_path = self.base_dir / artifact
            if artifact_path.exists():
                if error := self.remove_directory(artifact_path):
                    errors.append((artifact_path, error))
                    print(f"Error removing {artifact_path}: {error}")
                else:
                    removed_count += 1
                    removed_paths.add(artifact_path)
                    print(f"Removed build artifact: {artifact_path}")

        # Remove __pycache__ directories
        for path in self.base_dir.rglob("__pycache__"):
            if error := self.remove_directory(path):
                errors.append((path, error))
                print(f"Error removing {path}: {error}")
            else:
                removed_count += 1
                removed_paths.add(path)
                print(f"Removed __pycache__: {path}")

        return CleanupResult(
            removed_count=removed_count,
            removed_paths=removed_paths,
            errors=errors
        )


def main() -> None:
    """Main entry point"""
    base_dir = Path(r"C:\Users\hp\Desktop\Webscout")
    cleaner = DirectoryCleaner(base_dir)
    result = cleaner.cleanup()
    
    print(f"\nCleanup Summary:")
    print(f"Total directories removed: {result.removed_count}")
    if result.errors:
        print(f"Errors encountered: {len(result.errors)}")
        for path, error in result.errors:
            print(f"- {path}: {error}")


if __name__ == "__main__":
    main()
