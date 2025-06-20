#!/usr/bin/env python3
"""Debug script to diagnose repo audit issues."""

import os
from pathlib import Path
import time

def main():
    print("=== Debug Audit Script ===")
    
    # 1. Check current location
    print(f"\n1. Current working directory: {os.getcwd()}")
    
    # 2. Check script location and project root
    script_path = Path(__file__)
    print(f"2. This script is at: {script_path}")
    
    if script_path.parent.name == "scripts":
        project_root = script_path.parent.parent
    else:
        project_root = script_path.parent
    
    print(f"3. Detected project root: {project_root}")
    
    # 3. Check if directories exist
    print("\n4. Checking directories:")
    for dir_name in ["scripts", "tests", "config", "output"]:
        dir_path = project_root / dir_name
        exists = "✓ EXISTS" if dir_path.exists() else "✗ MISSING"
        print(f"   {dir_name}/  {exists}")
    
    # 4. Count files in project
    print("\n5. Counting files in project...")
    file_count = 0
    dir_count = 0
    large_files = []
    
    try:
        for root, dirs, files in os.walk(project_root):
            # Skip hidden and system directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
            
            dir_count += len(dirs)
            file_count += len(files)
            
            # Track progress
            if file_count % 100 == 0 and file_count > 0:
                print(f"   ...scanned {file_count} files so far...")
            
            # Check for large files
            for file in files:
                try:
                    filepath = Path(root) / file
                    size = filepath.stat().st_size
                    if size > 10 * 1024 * 1024:  # Files > 10MB
                        large_files.append((str(filepath.relative_to(project_root)), size))
                except:
                    pass
    
    except Exception as e:
        print(f"   ERROR during scan: {e}")
        return
    
    print(f"\n6. Scan complete:")
    print(f"   Total directories: {dir_count}")
    print(f"   Total files: {file_count}")
    
    if large_files:
        print(f"\n7. Large files found (>10MB):")
        for path, size in large_files[:5]:  # Show top 5
            print(f"   {path}: {size/1024/1024:.1f} MB")
    
    # 5. Try to create output directory
    print("\n8. Testing output directory creation:")
    output_dir = project_root / "output"
    try:
        output_dir.mkdir(exist_ok=True)
        print("   ✓ Output directory ready")
    except Exception as e:
        print(f"   ✗ Error creating output directory: {e}")
    
    # 6. Test file creation
    print("\n9. Testing file write:")
    try:
        test_file = output_dir / "test_write.txt"
        test_file.write_text("Test write successful")
        print("   ✓ Can write to output directory")
        test_file.unlink()  # Clean up
    except Exception as e:
        print(f"   ✗ Error writing file: {e}")
    
    print("\n=== Debug complete ===")
    print("\nIf the file count is very high (>1000), the audit might take a while.")
    print("Consider moving or excluding large directories like node_modules, .git, etc.")

if __name__ == "__main__":
    main()