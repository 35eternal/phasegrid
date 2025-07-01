import os
import json
from pathlib import Path

def explore_project():
    """
    This function explores your project and shows important files.
    It's like having a map of your toy box!
    """
    
    print("🔍 Exploring your project structure...\n")
    
    # Get current directory
    current_dir = Path.cwd()
    print(f"📁 You are in: {current_dir}\n")
    
    # Important files to look for
    important_files = [
        "requirements.txt",
        "setup.py",
        "pyproject.toml",
        ".env",
        ".env.example",
        "config.yaml",
        "config.json",
        "README.md"
    ]
    
    # Important folders to check
    important_folders = [
        "scripts",
        ".github",
        "src",
        "tests",
        "docs",
        "config",
        "phasegrid",
        "alerts"
    ]
    
    # Check for important files
    print("📄 Important files found:")
    for file in important_files:
        if Path(file).exists():
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} (not found)")
    
    print("\n📂 Important folders found:")
    for folder in important_folders:
        if Path(folder).exists() and Path(folder).is_dir():
            print(f"  ✅ {folder}/")
            # Show Python files in scripts folder
            if folder == "scripts":
                py_files = list(Path(folder).glob("*.py"))
                if py_files:
                    print("     Python files in scripts:")
                    for py_file in py_files[:10]:  # Show max 10 files
                        print(f"       - {py_file.name}")
        else:
            print(f"  ❌ {folder}/ (not found)")
    
    # Check for GitHub workflows
    github_workflows = Path(".github/workflows")
    if github_workflows.exists():
        print("\n🔧 GitHub Workflows found:")
        for workflow in github_workflows.glob("*.yml"):
            print(f"  - {workflow.name}")
        for workflow in github_workflows.glob("*.yaml"):
            print(f"  - {workflow.name}")
    
    # List all Python files in current directory (not in venv)
    print("\n🐍 Python files in main directory:")
    py_count = 0
    for py_file in Path(".").glob("*.py"):
        if not str(py_file).startswith(("venv", "env", ".venv")):
            print(f"  - {py_file}")
            py_count += 1
            if py_count >= 10:
                print("  ... and more!")
                break
    
    print("\n✨ Exploration complete!")

if __name__ == "__main__":
    explore_project()
