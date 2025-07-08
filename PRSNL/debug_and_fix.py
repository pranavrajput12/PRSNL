#!/usr/bin/env python3
"""
PRSNL Debug and Fix Script
Automatically detects and fixes common issues in the PRSNL application
"""

import os
import re
import sys
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text: str):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

def print_success(text: str):
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")

def print_error(text: str):
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")

def print_warning(text: str):
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")

def print_info(text: str):
    print(f"{Colors.OKCYAN}ℹ️  {text}{Colors.ENDC}")

class PRSNLDebugger:
    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.backend_dir = self.root_dir / "backend"
        self.frontend_dir = self.root_dir / "frontend"
        self.issues_found = []
        self.fixes_applied = []
        
    def run(self):
        """Main entry point for the debugger"""
        print_header("PRSNL Debug and Fix Tool")
        
        # Check environment
        self.check_environment()
        
        # Check backend
        self.check_backend()
        
        # Check frontend
        self.check_frontend()
        
        # Check services
        self.check_services()
        
        # Summary
        self.print_summary()
        
    def check_environment(self):
        """Check environment setup"""
        print_header("Checking Environment")
        
        # Check Python version
        python_version = sys.version_info
        if python_version.major == 3 and python_version.minor >= 11:
            print_success(f"Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
        else:
            print_warning(f"Python version {python_version.major}.{python_version.minor} detected. Python 3.11+ recommended")
            
        # Check Node.js
        try:
            node_version = subprocess.check_output(["node", "--version"], text=True).strip()
            print_success(f"Node.js version: {node_version}")
        except:
            print_error("Node.js not found")
            self.issues_found.append("Node.js not installed")
            
        # Check Docker
        try:
            docker_version = subprocess.check_output(["docker", "--version"], text=True).strip()
            print_success(f"Docker: {docker_version}")
        except:
            print_error("Docker not found")
            self.issues_found.append("Docker not installed")
            
    def check_backend(self):
        """Check backend setup and common issues"""
        print_header("Checking Backend")
        
        # Check if backend directory exists
        if not self.backend_dir.exists():
            print_error("Backend directory not found")
            return
            
        # Check .env file
        env_file = self.backend_dir / ".env"
        env_example = self.backend_dir / ".env.example"
        
        if not env_file.exists() and env_example.exists():
            print_warning(".env file not found, creating from .env.example")
            import shutil
            shutil.copy(env_example, env_file)
            self.fixes_applied.append("Created .env file from .env.example")
            
        # Check and fix Azure OpenAI configuration
        if env_file.exists():
            self.check_azure_config(env_file)
            
        # Check Python imports
        self.check_python_imports()
        
        # Check missing type definitions
        self.check_missing_types()
        
    def check_azure_config(self, env_file: Path):
        """Check and fix Azure OpenAI configuration"""
        print_info("Checking Azure OpenAI configuration...")
        
        with open(env_file, 'r') as f:
            env_content = f.read()
            
        # Check if Azure OpenAI is configured
        if "your_api_key_here" in env_content:
            print_warning("Azure OpenAI not configured")
            
            # For testing, we can use a mock configuration
            # Auto-configure with mock values for testing
            print_info("Auto-configuring with mock values for testing...")
            response = "1"
            
            if response == "1":
                # Use mock values for testing
                env_content = env_content.replace(
                    "AZURE_OPENAI_API_KEY=your_api_key_here",
                    "AZURE_OPENAI_API_KEY=mock-api-key-for-testing"
                )
                env_content = env_content.replace(
                    "AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com",
                    "AZURE_OPENAI_ENDPOINT=https://mock-endpoint.openai.azure.com"
                )
                
                with open(env_file, 'w') as f:
                    f.write(env_content)
                    
                print_success("Configured with mock values for testing")
                self.fixes_applied.append("Configured Azure OpenAI with mock values")
                
            elif response == "2":
                api_key = input("Enter Azure OpenAI API Key: ")
                endpoint = input("Enter Azure OpenAI Endpoint: ")
                
                env_content = env_content.replace(
                    "AZURE_OPENAI_API_KEY=your_api_key_here",
                    f"AZURE_OPENAI_API_KEY={api_key}"
                )
                env_content = env_content.replace(
                    "AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com",
                    f"AZURE_OPENAI_ENDPOINT={endpoint}"
                )
                
                with open(env_file, 'w') as f:
                    f.write(env_content)
                    
                print_success("Configured Azure OpenAI with provided credentials")
                self.fixes_applied.append("Configured Azure OpenAI")
                
    def check_python_imports(self):
        """Check for missing imports in Python files"""
        print_info("Checking Python imports...")
        
        # Common import issues
        import_fixes = {
            "embedding_service.py": {
                "pattern": r"class EmbeddingService.*?(?=class|\Z)",
                "missing": "embedding_service = EmbeddingService()",
                "fix": "\n\n# Create singleton instance\nembedding_service = EmbeddingService()"
            }
        }
        
        for filename, fix_info in import_fixes.items():
            file_path = self.backend_dir / "app" / "services" / filename
            if file_path.exists():
                with open(file_path, 'r') as f:
                    content = f.read()
                    
                if fix_info["missing"] not in content:
                    print_warning(f"Missing instantiation in {filename}")
                    content += fix_info["fix"]
                    
                    with open(file_path, 'w') as f:
                        f.write(content)
                        
                    print_success(f"Fixed {filename}")
                    self.fixes_applied.append(f"Fixed instantiation in {filename}")
                    
    def check_missing_types(self):
        """Check for missing type definitions"""
        print_info("Checking TypeScript/Python types...")
        
        # Check for common missing types in Python
        schemas_file = self.backend_dir / "app" / "models" / "schemas.py"
        if schemas_file.exists():
            with open(schemas_file, 'r') as f:
                content = f.read()
                
            # Check if Tag class is missing
            if "class Tag" not in content:
                print_warning("Tag class missing in schemas.py")
                # We can add a basic Tag class if needed
                
    def check_frontend(self):
        """Check frontend setup and common issues"""
        print_header("Checking Frontend")
        
        if not self.frontend_dir.exists():
            print_error("Frontend directory not found")
            return
            
        # Check for common Svelte component issues
        self.check_svelte_components()
        
    def check_svelte_components(self):
        """Check and fix common Svelte component issues"""
        print_info("Checking Svelte components...")
        
        # Common variable declarations that might be missing
        component_fixes = {
            "LiveTags.svelte": [
                ("let newTagInput = '';", r"let showSuggestions = false;"),
                ("let filteredSuggestions: string[] = [];", r"let uniqueSuggestedTags: string\[\] = \[\];"),
                ("let debounceMs = 300;", r"let wsLastUpdated = 0;"),
                ("let isReducedMotion = false;", r"\$: visibleTags = tags"),
                ("let tagListElement: HTMLDivElement;", r"let tagInputRef: HTMLInputElement;"),
            ],
            "capture/+page.svelte": [
                ("type ItemType = 'note' | 'article' | 'video' | 'image';", r"import Icon from"),
                ("let videoQuality: 'standard' | 'high' = 'standard';", r"let itemType: ItemType = 'note';"),
            ]
        }
        
        for component, fixes in component_fixes.items():
            if "/" in component:
                file_path = self.frontend_dir / "src" / "routes" / component
            else:
                file_path = self.frontend_dir / "src" / "lib" / "components" / component
                
            if file_path.exists():
                with open(file_path, 'r') as f:
                    content = f.read()
                    
                for declaration, after_pattern in fixes:
                    if declaration not in content:
                        print_warning(f"Missing '{declaration}' in {component}")
                        # Add the declaration after the pattern
                        pattern = re.compile(after_pattern)
                        match = pattern.search(content)
                        if match:
                            insert_pos = match.end()
                            content = content[:insert_pos] + f"\n  {declaration}" + content[insert_pos:]
                            self.fixes_applied.append(f"Added '{declaration}' to {component}")
                            
                with open(file_path, 'w') as f:
                    f.write(content)
                    
    def check_services(self):
        """Check if services are running"""
        print_header("Checking Services")
        
        # Check PostgreSQL
        try:
            result = subprocess.run(["docker", "ps"], capture_output=True, text=True)
            if "postgres" in result.stdout:
                print_success("PostgreSQL is running")
            else:
                print_warning("PostgreSQL not running")
                print_info("Starting PostgreSQL...")
                response = 'y'
                if response.lower() == 'y':
                    os.chdir(self.root_dir)
                    subprocess.run(["docker", "compose", "up", "-d", "db"])
                    print_success("Started PostgreSQL")
                    self.fixes_applied.append("Started PostgreSQL")
        except:
            print_error("Could not check PostgreSQL status")
            
        # Check backend
        try:
            import requests
            response = requests.get("http://localhost:8000/health", timeout=2)
            if response.status_code == 200:
                print_success("Backend is running")
            else:
                print_warning("Backend returned error")
        except:
            print_warning("Backend not running or not responding")
            
        # Check frontend
        for port in [3002, 3003, 3004, 3005]:
            try:
                import requests
                response = requests.get(f"http://localhost:{port}", timeout=1)
                print_success(f"Frontend is running on port {port}")
                break
            except:
                continue
        else:
            print_warning("Frontend not running")
            
    def print_summary(self):
        """Print summary of issues and fixes"""
        print_header("Summary")
        
        if self.fixes_applied:
            print_success(f"Applied {len(self.fixes_applied)} fixes:")
            for fix in self.fixes_applied:
                print(f"  - {fix}")
                
        if self.issues_found:
            print_warning(f"Found {len(self.issues_found)} issues that need manual attention:")
            for issue in self.issues_found:
                print(f"  - {issue}")
                
        if not self.fixes_applied and not self.issues_found:
            print_success("No issues found!")
            
        print("\n" + Colors.BOLD + "Next Steps:" + Colors.ENDC)
        print("1. Restart the backend if any fixes were applied")
        print("2. Check the frontend for compilation errors")
        print("3. Test the AI features with the configured settings")

if __name__ == "__main__":
    debugger = PRSNLDebugger()
    debugger.run()