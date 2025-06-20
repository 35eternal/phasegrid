#!/usr/bin/env python3
"""Repository audit script for Project PhaseGrid - Standalone version."""

import os
import re
import ast
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter
from typing import Dict, List, Set, Tuple

class RepoAuditor:
    def __init__(self, repo_root: str = None):
        # Use current directory if not specified
        if repo_root is None:
            repo_root = os.getcwd()
            
        self.repo_root = Path(repo_root)
        self.output_dir = self.repo_root / "output"
        self.output_dir.mkdir(exist_ok=True)
        
        # Audit results
        self.files_inventory = []
        self.duplicates = defaultdict(list)
        self.naming_issues = []
        self.dependencies = defaultdict(set)
        self.test_coverage = {}
        self.cleanup_tasks = []
        
    def audit(self):
        """Main audit orchestrator."""
        print("Starting repository audit...")
        print(f"Repository root: {self.repo_root}")
        
        self._scan_files()
        self._check_duplicates()
        self._check_naming_conventions()
        self._analyze_dependencies()
        self._assess_test_coverage()
        self._generate_cleanup_plan()
        self._write_report()
        
        print(f"✅ Audit complete. Report saved to: {self.output_dir / 'repo_audit.md'}")
        
    def _scan_files(self):
        """Inventory all Python files."""
        for root, dirs, files in os.walk(self.repo_root):
            # Skip hidden dirs and __pycache__
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
            
            # Skip output and credentials directories
            if 'output' in root or 'credentials' in root or '.git' in root:
                continue
            
            for file in files:
                if file.endswith('.py'):
                    filepath = Path(root) / file
                    try:
                        rel_path = filepath.relative_to(self.repo_root)
                    except ValueError:
                        continue
                    
                    # Get file stats
                    try:
                        stats = filepath.stat()
                        lines = self._count_lines(filepath)
                        
                        self.files_inventory.append({
                            'path': str(rel_path).replace('\\', '/'),
                            'size': stats.st_size,
                            'lines': lines,
                            'modified': datetime.fromtimestamp(stats.st_mtime).isoformat()
                        })
                    except Exception as e:
                        print(f"Warning: Could not analyze {filepath}: {e}")
                    
    def _count_lines(self, filepath: Path) -> int:
        """Count non-empty lines in file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return sum(1 for line in f if line.strip())
        except:
            return 0
            
    def _check_duplicates(self):
        """Find duplicate or similar files."""
        # Check by content hash
        from hashlib import md5
        
        content_hashes = defaultdict(list)
        
        for file_info in self.files_inventory:
            filepath = self.repo_root / file_info['path']
            try:
                with open(filepath, 'rb') as f:
                    content_hash = md5(f.read()).hexdigest()
                content_hashes[content_hash].append(file_info['path'])
            except:
                pass
                
        # Mark duplicates
        for hash_val, paths in content_hashes.items():
            if len(paths) > 1:
                self.duplicates['exact'].extend(paths[1:])  # Keep first, mark rest
                
        # Check for similar names
        name_groups = defaultdict(list)
        for file_info in self.files_inventory:
            base_name = Path(file_info['path']).stem.lower()
            # Remove version numbers and common suffixes
            cleaned = re.sub(r'(_v\d+|_old|_backup|_copy|\d+)$', '', base_name)
            name_groups[cleaned].append(file_info['path'])
            
        for name, paths in name_groups.items():
            if len(paths) > 1:
                self.duplicates['similar'].extend(paths)
                
    def _check_naming_conventions(self):
        """Check PEP8 naming conventions."""
        for file_info in self.files_inventory:
            path = Path(file_info['path'])
            filename = path.stem
            
            # Check snake_case
            if not re.match(r'^[a-z_][a-z0-9_]*$', filename):
                if filename not in ['__init__', '__main__']:
                    self.naming_issues.append({
                        'path': file_info['path'],
                        'issue': 'Not snake_case',
                        'suggestion': self._to_snake_case(filename)
                    })
                    
            # Check test file naming
            if 'test' in str(path.parent) and not filename.startswith('test_'):
                if filename != '__init__':
                    self.naming_issues.append({
                        'path': file_info['path'],
                        'issue': 'Test file should start with test_',
                        'suggestion': f"test_{filename}"
                    })
                
    def _to_snake_case(self, name: str) -> str:
        """Convert to snake_case."""
        # Handle CamelCase
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
        
    def _analyze_dependencies(self):
        """Build dependency graph."""
        for file_info in self.files_inventory:
            filepath = self.repo_root / file_info['path']
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Parse AST
                tree = ast.parse(content)
                
                # Extract imports
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            self.dependencies[file_info['path']].add(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            self.dependencies[file_info['path']].add(node.module)
                            
            except Exception as e:
                print(f"Warning: Could not parse {filepath}: {e}")
                
    def _assess_test_coverage(self):
        """Estimate test coverage."""
        # Find test files
        test_files = [f for f in self.files_inventory if 'test' in f['path']]
        src_files = [f for f in self.files_inventory 
                    if 'test' not in f['path'] 
                    and not f['path'].startswith('scripts/')
                    and f['path'] != '__init__.py']
        
        # Map tests to source files
        covered_modules = set()
        
        for test_file in test_files:
            test_name = Path(test_file['path']).stem
            # Extract module name from test_module pattern
            match = re.match(r'test_(.+)', test_name)
            if match:
                module_name = match.group(1)
                covered_modules.add(module_name)
                
        # Calculate coverage
        total_modules = len(src_files)
        covered_count = sum(1 for f in src_files if Path(f['path']).stem in covered_modules)
        
        self.test_coverage = {
            'total_modules': total_modules,
            'covered_modules': covered_count,
            'coverage_percent': (covered_count / total_modules * 100) if total_modules > 0 else 0,
            'uncovered': [f['path'] for f in src_files if Path(f['path']).stem not in covered_modules]
        }
        
    def _generate_cleanup_plan(self):
        """Create prioritized cleanup tasks."""
        # High priority
        if self.duplicates.get('exact'):
            self.cleanup_tasks.append({
                'priority': 'HIGH',
                'task': 'Remove exact duplicate files',
                'details': self.duplicates['exact']
            })
            
        # Check for column mismatch in code
        bet_id_files = []
        for file_path, deps in self.dependencies.items():
            filepath = self.repo_root / file_path
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'bet_id' in content and 'source_id' not in content:
                        bet_id_files.append(file_path)
            except:
                pass
                
        if bet_id_files:
            self.cleanup_tasks.append({
                'priority': 'HIGH',
                'task': 'Fix column mismatch: bet_id vs source_id',
                'details': bet_id_files
            })
            
        # Medium priority
        if self.duplicates.get('similar'):
            self.cleanup_tasks.append({
                'priority': 'MEDIUM',
                'task': 'Review similar files for consolidation',
                'details': list(set(self.duplicates['similar']))[:5]  # Limit output
            })
            
        if self.naming_issues:
            self.cleanup_tasks.append({
                'priority': 'MEDIUM',
                'task': 'Fix naming convention violations',
                'details': [f"{n['path']} -> {n['suggestion']}" for n in self.naming_issues[:5]]
            })
            
        # Low priority
        if self.test_coverage['coverage_percent'] < 90:
            self.cleanup_tasks.append({
                'priority': 'LOW',
                'task': f"Increase test coverage from {self.test_coverage['coverage_percent']:.1f}% to 90%",
                'details': self.test_coverage['uncovered'][:5]
            })
            
    def _write_report(self):
        """Generate markdown report."""
        report_path = self.output_dir / "repo_audit.md"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# Repository Audit Report\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Repository: {self.repo_root}\n\n")
            
            # File inventory
            f.write("## File Inventory\n")
            f.write(f"Total Python files: {len(self.files_inventory)}\n")
            f.write(f"Total lines of code: {sum(f['lines'] for f in self.files_inventory):,}\n\n")
            
            # Top files by size
            f.write("### Largest Files\n")
            sorted_files = sorted(self.files_inventory, key=lambda x: x['lines'], reverse=True)[:10]
            for file in sorted_files:
                f.write(f"- {file['path']} ({file['lines']} lines)\n")
            f.write("\n")
            
            # Duplicates
            f.write("## Duplicate Files\n")
            if self.duplicates.get('exact'):
                f.write("### Exact Duplicates\n")
                for dup in self.duplicates['exact']:
                    f.write(f"- {dup}\n")
                f.write("\n")
                
            if self.duplicates.get('similar'):
                f.write("### Similar Files\n")
                unique_similar = list(set(self.duplicates['similar']))[:10]
                for dup in unique_similar:
                    f.write(f"- {dup}\n")
                f.write("\n")
            
            if not self.duplicates.get('exact') and not self.duplicates.get('similar'):
                f.write("No duplicate files found.\n\n")
                
            # Naming issues
            if self.naming_issues:
                f.write("## Naming Convention Issues\n")
                for issue in self.naming_issues[:10]:
                    f.write(f"- {issue['path']}: {issue['issue']} (suggest: {issue['suggestion']})\n")
                f.write("\n")
            else:
                f.write("## Naming Conventions\n")
                f.write("All files follow PEP8 naming conventions.\n\n")
                
            # Dependencies
            f.write("## Dependency Analysis\n")
            
            # External dependencies
            all_deps = set()
            for deps in self.dependencies.values():
                all_deps.update(deps)
                
            # Common internal modules
            internal_modules = {'sheet_connector', 'slip_optimizer', 'bankroll_optimizer', 
                               'update_results', 'scripts', 'tests'}
            external_deps = [d for d in all_deps 
                           if not any(d.startswith(m) for m in internal_modules)]
            
            f.write(f"### External Dependencies ({len(external_deps)})\n")
            for dep in sorted(external_deps)[:20]:
                f.write(f"- {dep}\n")
            f.write("\n")
            
            # Module coupling
            f.write("### Module Coupling\n")
            coupling = [(m, len(deps)) for m, deps in self.dependencies.items()]
            coupling.sort(key=lambda x: x[1], reverse=True)
            
            for module, dep_count in coupling[:10]:
                f.write(f"- {module}: {dep_count} dependencies\n")
            f.write("\n")
            
            # Test coverage
            f.write("## Test Coverage\n")
            f.write(f"- Total modules: {self.test_coverage['total_modules']}\n")
            f.write(f"- Covered modules: {self.test_coverage['covered_modules']}\n")
            f.write(f"- Coverage: {self.test_coverage['coverage_percent']:.1f}%\n\n")
            
            if self.test_coverage['uncovered']:
                f.write("### Uncovered Modules\n")
                for module in self.test_coverage['uncovered'][:10]:
                    f.write(f"- {module}\n")
                f.write("\n")
                
            # Cleanup plan
            f.write("## Cleanup Plan\n")
            
            for priority in ['HIGH', 'MEDIUM', 'LOW']:
                tasks = [t for t in self.cleanup_tasks if t['priority'] == priority]
                if tasks:
                    f.write(f"### {priority} Priority\n")
                    for task in tasks:
                        f.write(f"**{task['task']}**\n")
                        for detail in task['details']:
                            f.write(f"- {detail}\n")
                        f.write("\n")
                        
            # Summary statistics
            f.write("## Summary Statistics\n")
            f.write(f"- Python files: {len(self.files_inventory)}\n")
            f.write(f"- Total LOC: {sum(f['lines'] for f in self.files_inventory):,}\n")
            f.write(f"- Average file size: {sum(f['lines'] for f in self.files_inventory) / len(self.files_inventory):.0f} lines\n")
            f.write(f"- Test files: {len([f for f in self.files_inventory if 'test' in f['path']])}\n")
            f.write(f"- Script files: {len([f for f in self.files_inventory if f['path'].startswith('scripts/')])}\n")


if __name__ == "__main__":
    # Run audit on current directory or specified path
    import sys
    
    if len(sys.argv) > 1:
        repo_path = sys.argv[1]
    else:
        repo_path = None
        
    auditor = RepoAuditor(repo_root=repo_path)
    auditor.audit()