#!/usr/bin/env python3
"""Simplified repo audit with progress reporting."""

import os
from pathlib import Path
import datetime

def main():
    print("Starting simplified repository audit...")
    
    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent if script_dir.name == "scripts" else script_dir
    output_dir = project_root / "output"
    
    # Create output directory
    output_dir.mkdir(exist_ok=True)
    
    print(f"Scanning: {project_root}")
    print("Progress: ", end="", flush=True)
    
    # Collect file data
    files_data = []
    skip_dirs = {'.git', '.venv', 'venv', '__pycache__', 'node_modules', '.idea', '.vscode'}
    
    file_count = 0
    for root, dirs, files in os.walk(project_root):
        # Skip certain directories
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        
        # Skip output directory itself
        if Path(root) == output_dir:
            continue
        
        for file in files:
            file_count += 1
            if file_count % 10 == 0:
                print(".", end="", flush=True)
            
            filepath = Path(root) / file
            relative_path = filepath.relative_to(project_root)
            
            # Skip hidden files
            if file.startswith('.'):
                continue
            
            try:
                stat = filepath.stat()
                files_data.append({
                    'path': str(relative_path),
                    'size': stat.st_size,
                    'extension': filepath.suffix
                })
            except:
                pass
    
    print(f"\nScanned {file_count} files")
    
    # Generate simple report
    report = []
    report.append("# Repository Audit Report (Simplified)")
    report.append(f"Generated: {datetime.datetime.now().isoformat()}")
    report.append(f"Repository: {project_root}\n")
    
    # Summary
    total_size = sum(f['size'] for f in files_data)
    report.append("## Summary")
    report.append(f"- Total files: {len(files_data)}")
    report.append(f"- Total size: {total_size:,} bytes ({total_size/1024/1024:.2f} MB)\n")
    
    # By extension
    by_ext = {}
    for f in files_data:
        ext = f['extension'] or 'no_extension'
        if ext not in by_ext:
            by_ext[ext] = {'count': 0, 'size': 0}
        by_ext[ext]['count'] += 1
        by_ext[ext]['size'] += f['size']
    
    report.append("## Files by Type")
    for ext, data in sorted(by_ext.items(), key=lambda x: x[1]['size'], reverse=True)[:10]:
        report.append(f"- {ext}: {data['count']} files ({data['size']/1024:.1f} KB)")
    
    # Python files without tests
    py_files = [f['path'] for f in files_data if f['extension'] == '.py']
    test_files = [f for f in py_files if 'test' in f.lower()]
    module_files = [f for f in py_files if not any(x in f for x in ['test', 'script', '__'])]
    
    report.append("\n## Python Files")
    report.append(f"- Total Python files: {len(py_files)}")
    report.append(f"- Test files: {len(test_files)}")
    report.append(f"- Module files: {len(module_files)}")
    
    # Write report
    report_path = output_dir / "repo_audit.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    print(f"\n✓ Audit complete!")
    print(f"Report saved to: {report_path}")
    
    # Show first few lines of report
    print("\nReport preview:")
    print("-" * 40)
    for line in report[:10]:
        print(line)
    print("-" * 40)

if __name__ == "__main__":
    main()