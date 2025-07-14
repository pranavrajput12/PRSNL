"""
Package Detection Utilities

Utilities for detecting and extracting package files from repositories.
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

def detect_package_files(repo_path: str) -> Dict[str, str]:
    """
    Detect and read package files in a repository.
    
    Args:
        repo_path: Path to the repository
    
    Returns:
        Dict of filename -> file content for detected package files
    """
    package_files = {}
    
    if not os.path.exists(repo_path):
        return package_files
    
    # Package file patterns to search for
    package_patterns = {
        # Node.js / npm
        'package.json': 'package.json',
        'package-lock.json': 'package-lock.json',
        'yarn.lock': 'yarn.lock',
        
        # Python
        'requirements.txt': 'requirements.txt',
        'requirements-dev.txt': 'requirements-dev.txt',
        'requirements-test.txt': 'requirements-test.txt',
        'setup.py': 'setup.py',
        'pyproject.toml': 'pyproject.toml',
        'Pipfile': 'Pipfile',
        
        # Rust
        'Cargo.toml': 'Cargo.toml',
        'Cargo.lock': 'Cargo.lock',
        
        # Java / Maven
        'pom.xml': 'pom.xml',
        
        # Java / Gradle
        'build.gradle': 'build.gradle',
        'build.gradle.kts': 'build.gradle.kts',
        
        # Go
        'go.mod': 'go.mod',
        'go.sum': 'go.sum',
        
        # .NET
        '*.csproj': '*.csproj',
        'packages.config': 'packages.config',
        
        # Ruby
        'Gemfile': 'Gemfile',
        'Gemfile.lock': 'Gemfile.lock',
        
        # PHP
        'composer.json': 'composer.json',
        'composer.lock': 'composer.lock'
    }
    
    # Search for package files
    for root, dirs, files in os.walk(repo_path):
        # Skip hidden directories and common ignore patterns
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'target', 'build']]
        
        for file in files:
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, repo_path)
            
            # Check for exact matches
            if file in package_patterns:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        package_files[relative_path] = content
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
            
            # Check for pattern matches (like *.csproj)
            elif file.endswith('.csproj'):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        package_files[relative_path] = content
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
    
    return package_files

def extract_dependencies_from_files(package_files: Dict[str, str]) -> Dict[str, List[str]]:
    """
    Extract dependency lists from package files.
    
    Args:
        package_files: Dict of filename -> content
    
    Returns:
        Dict of package_manager -> list of dependencies
    """
    dependencies = {}
    
    for filename, content in package_files.items():
        basename = os.path.basename(filename)
        
        if basename == 'package.json':
            npm_deps = extract_npm_dependencies(content)
            if npm_deps:
                dependencies['npm'] = npm_deps
        
        elif basename.startswith('requirements') and basename.endswith('.txt'):
            python_deps = extract_python_dependencies(content)
            if python_deps:
                dependencies['pypi'] = python_deps
        
        elif basename == 'Cargo.toml':
            rust_deps = extract_rust_dependencies(content)
            if rust_deps:
                dependencies['cargo'] = rust_deps
        
        elif basename == 'pom.xml':
            maven_deps = extract_maven_dependencies(content)
            if maven_deps:
                dependencies['maven'] = maven_deps
        
        elif basename == 'go.mod':
            go_deps = extract_go_dependencies(content)
            if go_deps:
                dependencies['go'] = go_deps
    
    return dependencies

def extract_npm_dependencies(package_json_content: str) -> List[str]:
    """Extract npm dependencies from package.json"""
    try:
        data = json.loads(package_json_content)
        deps = []
        
        # Collect all dependency types
        for dep_type in ['dependencies', 'devDependencies', 'peerDependencies', 'optionalDependencies']:
            if dep_type in data:
                deps.extend(data[dep_type].keys())
        
        return deps
    except Exception:
        return []

def extract_python_dependencies(requirements_content: str) -> List[str]:
    """Extract Python dependencies from requirements.txt"""
    deps = []
    
    for line in requirements_content.split('\n'):
        line = line.strip()
        if line and not line.startswith('#') and not line.startswith('-'):
            # Extract package name (before version specifier)
            match = re.match(r'^([a-zA-Z0-9_-]+)', line)
            if match:
                deps.append(match.group(1))
    
    return deps

def extract_rust_dependencies(cargo_toml_content: str) -> List[str]:
    """Extract Rust dependencies from Cargo.toml"""
    deps = []
    lines = cargo_toml_content.split('\n')
    in_deps_section = False
    
    for line in lines:
        line = line.strip()
        
        if line == '[dependencies]':
            in_deps_section = True
            continue
        elif line.startswith('[') and line != '[dependencies]':
            in_deps_section = False
            continue
        
        if in_deps_section and '=' in line and not line.startswith('#'):
            dep_name = line.split('=')[0].strip().strip('"')
            deps.append(dep_name)
    
    return deps

def extract_maven_dependencies(pom_xml_content: str) -> List[str]:
    """Extract Maven dependencies from pom.xml"""
    deps = []
    
    # Simple regex to extract artifactId values
    matches = re.findall(r'<artifactId>([^<]+)</artifactId>', pom_xml_content)
    deps.extend(matches)
    
    return deps

def extract_go_dependencies(go_mod_content: str) -> List[str]:
    """Extract Go dependencies from go.mod"""
    deps = []
    
    for line in go_mod_content.split('\n'):
        line = line.strip()
        if line.startswith('require '):
            # Extract module name
            match = re.search(r'require\s+([^\s]+)', line)
            if match:
                deps.append(match.group(1))
        elif line and not line.startswith('module ') and not line.startswith('go ') and not line.startswith('//'):
            # Handle multi-line require blocks
            match = re.match(r'^([^\s]+)\s+v', line)
            if match:
                deps.append(match.group(1))
    
    return deps

def get_package_manager_for_file(filename: str) -> Optional[str]:
    """
    Determine the package manager for a given package file.
    
    Args:
        filename: Name of the package file
    
    Returns:
        Package manager name or None
    """
    basename = os.path.basename(filename)
    
    if basename in ['package.json', 'package-lock.json', 'yarn.lock']:
        return 'npm'
    elif basename.startswith('requirements') and basename.endswith('.txt'):
        return 'pypi'
    elif basename in ['setup.py', 'pyproject.toml', 'Pipfile']:
        return 'pypi'
    elif basename in ['Cargo.toml', 'Cargo.lock']:
        return 'cargo'
    elif basename == 'pom.xml':
        return 'maven'
    elif basename in ['build.gradle', 'build.gradle.kts']:
        return 'gradle'
    elif basename in ['go.mod', 'go.sum']:
        return 'go'
    elif basename.endswith('.csproj') or basename == 'packages.config':
        return 'nuget'
    elif basename in ['Gemfile', 'Gemfile.lock']:
        return 'gem'
    elif basename in ['composer.json', 'composer.lock']:
        return 'composer'
    
    return None

def analyze_package_ecosystem(package_files: Dict[str, str]) -> Dict[str, Any]:
    """
    Analyze the package ecosystem of a project.
    
    Args:
        package_files: Dict of filename -> content
    
    Returns:
        Analysis of the package ecosystem
    """
    ecosystems = {}
    primary_languages = []
    
    for filename in package_files.keys():
        manager = get_package_manager_for_file(filename)
        if manager:
            if manager not in ecosystems:
                ecosystems[manager] = []
            ecosystems[manager].append(os.path.basename(filename))
    
    # Determine primary languages based on package managers
    language_mapping = {
        'npm': 'JavaScript/TypeScript',
        'pypi': 'Python',
        'cargo': 'Rust',
        'maven': 'Java',
        'gradle': 'Java/Kotlin',
        'go': 'Go',
        'nuget': 'C#/.NET',
        'gem': 'Ruby',
        'composer': 'PHP'
    }
    
    for manager in ecosystems.keys():
        if manager in language_mapping:
            primary_languages.append(language_mapping[manager])
    
    return {
        'ecosystems': ecosystems,
        'primary_languages': list(set(primary_languages)),
        'total_package_files': len(package_files),
        'polyglot_project': len(ecosystems) > 1
    }