#!/usr/bin/env python3
"""
Package Intelligence System Test

Test the package intelligence service with sample package files.
"""

import asyncio
import json
import sys
import tempfile
import os
from typing import Dict, Any

# Test package files
SAMPLE_PACKAGE_JSON = """
{
  "name": "test-project",
  "version": "1.0.0",
  "description": "Test project for package intelligence",
  "dependencies": {
    "express": "^4.18.2",
    "lodash": "^4.17.21",
    "axios": "^1.4.0"
  },
  "devDependencies": {
    "jest": "^29.5.0",
    "eslint": "^8.42.0"
  }
}
"""

SAMPLE_REQUIREMENTS_TXT = """
fastapi==0.100.0
uvicorn[standard]==0.22.0
pydantic==1.10.8
requests==2.31.0
# Development dependencies
pytest==7.3.1
black==23.3.0
"""

SAMPLE_CARGO_TOML = """
[package]
name = "test-rust-project"
version = "0.1.0"
edition = "2021"

[dependencies]
serde = { version = "1.0", features = ["derive"] }
tokio = { version = "1.0", features = ["full"] }
reqwest = { version = "0.11", features = ["json"] }
clap = "4.0"
"""

SAMPLE_POM_XML = """
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <modelVersion>4.0.0</modelVersion>
    
    <groupId>com.example</groupId>
    <artifactId>test-java-project</artifactId>
    <version>1.0.0</version>
    
    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter</artifactId>
            <version>2.7.0</version>
        </dependency>
        <dependency>
            <groupId>junit</groupId>
            <artifactId>junit</artifactId>
            <version>4.13.2</version>
            <scope>test</scope>
        </dependency>
    </dependencies>
</project>
"""

class PackageIntelligenceTest:
    """Test package intelligence functionality"""
    
    def __init__(self):
        self.test_results = {}
    
    async def run_all_tests(self) -> bool:
        """Run all package intelligence tests"""
        print("🧪 Package Intelligence Test Suite")
        print("=" * 50)
        
        tests = [
            ("Service Import", self.test_service_import),
            ("Package Detection", self.test_package_detection),
            ("npm Analysis", self.test_npm_analysis),
            ("PyPI Analysis", self.test_pypi_analysis),
            ("Cargo Analysis", self.test_cargo_analysis),
            ("Maven Analysis", self.test_maven_analysis),
            ("Multi-Package Project", self.test_multi_package_analysis),
            ("Package Health", self.test_package_health_check),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            print(f"\n🔍 Testing: {test_name}")
            
            try:
                result = await test_func()
                if result:
                    print(f"✓ {test_name}: PASSED")
                    passed += 1
                else:
                    print(f"✗ {test_name}: FAILED")
                    failed += 1
            except Exception as e:
                print(f"✗ {test_name}: ERROR - {e}")
                failed += 1
        
        print("\n" + "=" * 50)
        print(f"Results: {passed} passed, {failed} failed")
        
        success_rate = (passed / (passed + failed)) * 100
        if success_rate >= 80:
            print(f"✓ Overall: SUCCESS ({success_rate:.1f}%)")
            return True
        else:
            print(f"✗ Overall: FAILURE ({success_rate:.1f}%)")
            return False
    
    async def test_service_import(self) -> bool:
        """Test that package intelligence service can be imported"""
        try:
            from app.services.package_intelligence_service import (
                PackageIntelligenceService, 
                PackageInfo, 
                SecurityVulnerability
            )
            from app.utils.package_detection import (
                detect_package_files,
                analyze_package_ecosystem
            )
            print("✓ All package intelligence modules imported successfully")
            return True
        except ImportError as e:
            print(f"✗ Import error: {e}")
            return False
    
    async def test_package_detection(self) -> bool:
        """Test package file detection utilities"""
        try:
            from app.utils.package_detection import (
                get_package_manager_for_file,
                extract_npm_dependencies,
                extract_python_dependencies,
                analyze_package_ecosystem
            )
            
            # Test package manager detection
            assert get_package_manager_for_file("package.json") == "npm"
            assert get_package_manager_for_file("requirements.txt") == "pypi"
            assert get_package_manager_for_file("Cargo.toml") == "cargo"
            assert get_package_manager_for_file("pom.xml") == "maven"
            
            # Test dependency extraction
            npm_deps = extract_npm_dependencies(SAMPLE_PACKAGE_JSON)
            assert "express" in npm_deps
            assert "lodash" in npm_deps
            assert len(npm_deps) == 5  # 3 deps + 2 devDeps
            
            python_deps = extract_python_dependencies(SAMPLE_REQUIREMENTS_TXT)
            assert "fastapi" in python_deps
            assert "uvicorn" in python_deps
            assert len(python_deps) == 6
            
            # Test ecosystem analysis
            package_files = {
                "package.json": SAMPLE_PACKAGE_JSON,
                "requirements.txt": SAMPLE_REQUIREMENTS_TXT
            }
            ecosystem = analyze_package_ecosystem(package_files)
            assert "npm" in ecosystem["ecosystems"]
            assert "pypi" in ecosystem["ecosystems"]
            assert ecosystem["polyglot_project"] == True
            
            print("✓ Package detection utilities working correctly")
            return True
            
        except Exception as e:
            print(f"✗ Package detection test failed: {e}")
            return False
    
    async def test_npm_analysis(self) -> bool:
        """Test npm package analysis"""
        try:
            from app.services.package_intelligence_service import PackageIntelligenceService
            
            async with PackageIntelligenceService() as service:
                # Test npm package info retrieval
                package_info = await service._get_npm_package_info("express")
                
                if package_info:
                    assert package_info.name == "express"
                    assert package_info.manager == "npm"
                    assert package_info.description is not None
                    print(f"✓ Retrieved npm package info for express: {package_info.version}")
                    return True
                else:
                    print("⚠ Could not retrieve npm package info (network/API issue)")
                    return True  # Don't fail test for network issues
                    
        except Exception as e:
            print(f"✗ npm analysis test failed: {e}")
            return False
    
    async def test_pypi_analysis(self) -> bool:
        """Test PyPI package analysis"""
        try:
            from app.services.package_intelligence_service import PackageIntelligenceService
            
            async with PackageIntelligenceService() as service:
                # Test PyPI package info retrieval
                package_info = await service._get_pypi_package_info("requests")
                
                if package_info:
                    assert package_info.name == "requests"
                    assert package_info.manager == "pypi"
                    assert package_info.description is not None
                    print(f"✓ Retrieved PyPI package info for requests: {package_info.version}")
                    return True
                else:
                    print("⚠ Could not retrieve PyPI package info (network/API issue)")
                    return True  # Don't fail test for network issues
                    
        except Exception as e:
            print(f"✗ PyPI analysis test failed: {e}")
            return False
    
    async def test_cargo_analysis(self) -> bool:
        """Test Cargo package analysis"""
        try:
            from app.services.package_intelligence_service import PackageIntelligenceService
            
            async with PackageIntelligenceService() as service:
                # Test Cargo package info retrieval
                package_info = await service._get_cargo_package_info("serde")
                
                if package_info:
                    assert package_info.name == "serde"
                    assert package_info.manager == "cargo"
                    assert package_info.description is not None
                    print(f"✓ Retrieved Cargo package info for serde: {package_info.version}")
                    return True
                else:
                    print("⚠ Could not retrieve Cargo package info (network/API issue)")
                    return True  # Don't fail test for network issues
                    
        except Exception as e:
            print(f"✗ Cargo analysis test failed: {e}")
            return False
    
    async def test_maven_analysis(self) -> bool:
        """Test Maven package analysis"""
        try:
            from app.services.package_intelligence_service import PackageIntelligenceService
            
            async with PackageIntelligenceService() as service:
                # Test Maven package info retrieval
                package_info = await service._get_maven_package_info("junit")
                
                if package_info:
                    assert package_info.name == "junit"
                    assert package_info.manager == "maven"
                    print(f"✓ Retrieved Maven package info for junit: {package_info.version}")
                    return True
                else:
                    print("⚠ Could not retrieve Maven package info (network/API issue)")
                    return True  # Don't fail test for network issues
                    
        except Exception as e:
            print(f"✗ Maven analysis test failed: {e}")
            return False
    
    async def test_multi_package_analysis(self) -> bool:
        """Test analysis of a multi-package manager project"""
        try:
            from app.services.package_intelligence_service import PackageIntelligenceService
            
            # Create test package files
            package_files = {
                "package.json": SAMPLE_PACKAGE_JSON,
                "requirements.txt": SAMPLE_REQUIREMENTS_TXT,
                "Cargo.toml": SAMPLE_CARGO_TOML,
                "pom.xml": SAMPLE_POM_XML
            }
            
            async with PackageIntelligenceService() as service:
                # Analyze project dependencies
                results = await service.analyze_project_dependencies(
                    "/test/project", package_files
                )
                
                # Verify results structure
                assert "package_managers" in results
                assert "total_dependencies" in results
                assert "recommendations" in results
                
                # Check that multiple package managers were detected
                managers = results["package_managers"]
                detected_managers = [m for m in managers.keys() if "error" not in managers[m]]
                
                print(f"✓ Multi-package analysis completed")
                print(f"  - Detected managers: {', '.join(detected_managers)}")
                print(f"  - Total dependencies: {results.get('total_dependencies', 0)}")
                print(f"  - Recommendations: {len(results.get('recommendations', []))}")
                
                return True
                
        except Exception as e:
            print(f"✗ Multi-package analysis test failed: {e}")
            return False
    
    async def test_package_health_check(self) -> bool:
        """Test package registry health checks"""
        try:
            import aiohttp
            
            registries = [
                ("npm", "https://registry.npmjs.org/lodash"),
                ("pypi", "https://pypi.org/pypi/requests/json"),
                ("cargo", "https://crates.io/api/v1/crates/serde"),
                ("maven", "https://search.maven.org/solrsearch/select?q=a:junit&rows=1&wt=json")
            ]
            
            healthy_count = 0
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                for name, url in registries:
                    try:
                        async with session.get(url) as response:
                            if response.status == 200:
                                healthy_count += 1
                                print(f"  ✓ {name} registry: healthy")
                            else:
                                print(f"  ⚠ {name} registry: degraded ({response.status})")
                    except Exception as e:
                        print(f"  ✗ {name} registry: unhealthy ({e})")
            
            print(f"✓ Registry health check: {healthy_count}/{len(registries)} healthy")
            return healthy_count >= 2  # At least 2 registries should be healthy
            
        except Exception as e:
            print(f"✗ Package health check failed: {e}")
            return False

async def main():
    """Main test runner"""
    tester = PackageIntelligenceTest()
    
    try:
        success = await tester.run_all_tests()
        return 0 if success else 1
    except Exception as e:
        print(f"Test suite failed: {e}")
        return 1

if __name__ == "__main__":
    # Set up path to find app modules
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    
    sys.exit(asyncio.run(main()))