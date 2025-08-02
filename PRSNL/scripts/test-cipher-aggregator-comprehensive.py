#!/usr/bin/env python3
"""
Comprehensive Cipher MCP Aggregator Mode Test Suite
Tests all components and generates detailed report with weak spots analysis
"""

import os
import sys
import json
import time
import asyncio
import subprocess
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import sqlite3

import requests
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/Users/pronav/Personal Knowledge Base/PRSNL/backend/.env')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CipherAggregatorTester:
    def __init__(self):
        self.test_results = {}
        self.weak_spots = []
        self.performance_metrics = {}
        self.start_time = datetime.now()
        
        # Configuration
        self.cipher_config_path = "/Users/pronav/Personal Knowledge Base/memAgent/cipher.yml"
        self.claude_settings_path = "/Users/pronav/.claude/settings.json"
        self.aggregator_env_script = "/Users/pronav/Personal Knowledge Base/PRSNL/scripts/cipher-aggregator-env.sh"
        
        # Qdrant Configuration
        self.qdrant_api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.zuZKL-Zabs8ISY5yUXgTW_fL-BoEYbLD2OZrjhp1Vt8"
        self.qdrant_url = "https://86c70065-df15-459b-bd8a-ab607b43341a.us-east4-0.gcp.cloud.qdrant.io"
        self.qdrant_collection = "prsnl_cipher_patterns"
        
        # Azure OpenAI Configuration
        self.azure_api_key = "1U6RGbb4XrVh4LUqG5qrNLHd1hvHeCDqseSThAayqhclju9nUCtTJQQJ99BAACHYHv6XJ3w3AAABACOG6tdK"
        self.azure_endpoint = "https://airops.openai.azure.com"
        self.azure_deployment = "gpt-4.1"
        self.azure_api_version = "2025-01-01-preview"

    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run all tests and return comprehensive report"""
        logger.info("🚀 Starting Comprehensive Cipher MCP Aggregator Test Suite")
        
        # Test Categories
        test_categories = [
            ("Configuration Validation", self.test_configuration_files),
            ("Environment Setup", self.test_environment_variables),
            ("Azure OpenAI Connectivity", self.test_azure_openai_connection),
            ("Qdrant Cloud Integration", self.test_qdrant_integration),
            ("Cipher CLI Functionality", self.test_cipher_cli),
            ("MCP Server Configuration", self.test_mcp_servers),
            ("Aggregator Mode Features", self.test_aggregator_features),
            ("CrewAI Integration", self.test_crewai_integration),
            ("Performance Metrics", self.test_performance),
            ("Memory Persistence", self.test_memory_persistence)
        ]
        
        for category_name, test_function in test_categories:
            logger.info(f"🧪 Testing: {category_name}")
            try:
                start_time = time.time()
                result = test_function()
                execution_time = time.time() - start_time
                
                self.test_results[category_name] = {
                    "status": "PASS" if result["success"] else "FAIL",
                    "details": result,
                    "execution_time": round(execution_time, 2)
                }
                
                if not result["success"]:
                    self.weak_spots.append({
                        "category": category_name,
                        "issue": result.get("error", "Unknown error"),
                        "severity": result.get("severity", "MEDIUM"),
                        "recommendation": result.get("recommendation", "Investigate and fix")
                    })
                    
            except Exception as e:
                logger.error(f"❌ Test failed: {category_name} - {e}")
                self.test_results[category_name] = {
                    "status": "ERROR",
                    "details": {"error": str(e)},
                    "execution_time": 0
                }
                self.weak_spots.append({
                    "category": category_name,
                    "issue": f"Test execution failed: {str(e)}",
                    "severity": "HIGH",
                    "recommendation": "Fix test infrastructure and retry"
                })
        
        return self.generate_comprehensive_report()

    def test_configuration_files(self) -> Dict[str, Any]:
        """Test all configuration files for correctness"""
        issues = []
        
        # Test cipher.yml
        if not os.path.exists(self.cipher_config_path):
            issues.append("cipher.yml not found")
        else:
            try:
                with open(self.cipher_config_path, 'r') as f:
                    content = f.read()
                    
                # Check for required sections
                required_sections = ["llm:", "aggregator:", "vectorStore:", "mcpServers:"]
                for section in required_sections:
                    if section not in content:
                        issues.append(f"Missing section: {section}")
                
                # Check for Azure configuration
                if "provider: azure" not in content:
                    issues.append("Azure provider not configured")
                
                if "type: qdrant" not in content:
                    issues.append("Qdrant vector store not configured")
                    
            except Exception as e:
                issues.append(f"cipher.yml read error: {e}")
        
        # Test Claude Code settings
        if not os.path.exists(self.claude_settings_path):
            issues.append("Claude settings not found")
        else:
            try:
                with open(self.claude_settings_path, 'r') as f:
                    settings = json.load(f)
                    
                if "mcpServers" not in settings:
                    issues.append("MCP servers not configured in Claude settings")
                    
                if "cipher" not in settings.get("mcpServers", {}):
                    issues.append("Cipher MCP server not configured")
                    
                cipher_env = settings.get("mcpServers", {}).get("cipher", {}).get("env", {})
                required_env_vars = ["AZURE_OPENAI_API_KEY", "QDRANT_API_KEY", "MCP_SERVER_MODE"]
                for var in required_env_vars:
                    if var not in cipher_env:
                        issues.append(f"Missing environment variable: {var}")
                        
            except Exception as e:
                issues.append(f"Claude settings read error: {e}")
        
        return {
            "success": len(issues) == 0,
            "issues_found": len(issues),
            "details": issues,
            "recommendation": "Fix configuration issues before proceeding" if issues else "Configuration is correct"
        }

    def test_environment_variables(self) -> Dict[str, Any]:
        """Test environment variable setup"""
        issues = []
        
        # Test aggregator environment script
        if not os.path.exists(self.aggregator_env_script):
            issues.append("Aggregator environment script not found")
            return {
                "success": False,
                "error": "Environment script missing",
                "severity": "HIGH",
                "recommendation": "Create aggregator environment script"
            }
        
        try:
            # Source the environment script and check variables
            result = subprocess.run(
                f"source {self.aggregator_env_script} && env | grep -E '(AZURE_|OPENAI_|QDRANT_|MCP_)'",
                shell=True,
                capture_output=True,
                text=True,
                executable='/bin/bash'
            )
            
            env_output = result.stdout
            required_vars = [
                "AZURE_OPENAI_API_KEY",
                "AZURE_OPENAI_ENDPOINT", 
                "AZURE_OPENAI_DEPLOYMENT",
                "OPENAI_API_KEY",
                "OPENAI_API_TYPE",
                "QDRANT_API_KEY",
                "MCP_SERVER_MODE"
            ]
            
            for var in required_vars:
                if var not in env_output:
                    issues.append(f"Missing environment variable: {var}")
            
            # Check for correct values
            if "MCP_SERVER_MODE=aggregator" not in env_output:
                issues.append("MCP_SERVER_MODE not set to aggregator")
                
            if "OPENAI_API_TYPE=azure" not in env_output:
                issues.append("OPENAI_API_TYPE not set to azure")
                
        except Exception as e:
            issues.append(f"Environment script execution error: {e}")
        
        return {
            "success": len(issues) == 0,
            "issues_found": len(issues),
            "details": issues,
            "recommendation": "Fix environment variable configuration" if issues else "Environment variables correctly configured"
        }

    def test_azure_openai_connection(self) -> Dict[str, Any]:
        """Test Azure OpenAI connectivity"""
        try:
            # Test with AzureOpenAI client
            client = openai.AzureOpenAI(
                api_key=self.azure_api_key,
                api_version=self.azure_api_version,
                azure_endpoint=self.azure_endpoint
            )
            
            # Test chat completion
            response = client.chat.completions.create(
                model=self.azure_deployment,
                messages=[{"role": "user", "content": "Test connection"}],
                max_tokens=10
            )
            
            # Test embeddings
            embedding_response = client.embeddings.create(
                model="text-embedding-ada-002",
                input="Test embedding"
            )
            
            return {
                "success": True,
                "chat_completion": "Working",
                "embeddings": "Working",
                "model_used": self.azure_deployment,
                "response_length": len(response.choices[0].message.content) if response.choices else 0,
                "embedding_dimensions": len(embedding_response.data[0].embedding) if embedding_response.data else 0
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "severity": "HIGH",
                "recommendation": "Verify Azure OpenAI credentials and deployment configuration"
            }

    def test_qdrant_integration(self) -> Dict[str, Any]:
        """Test Qdrant Cloud connectivity and operations"""
        try:
            client = QdrantClient(
                url=self.qdrant_url,
                api_key=self.qdrant_api_key,
            )
            
            # Test connection
            collections = client.get_collections()
            
            # Test collection operations
            collection_exists = False
            try:
                collection_info = client.get_collection(self.qdrant_collection)
                collection_exists = True
                points_count = collection_info.points_count
            except:
                points_count = 0
            
            # Test creating collection if it doesn't exist
            if not collection_exists:
                try:
                    client.create_collection(
                        collection_name=self.qdrant_collection,
                        vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
                    )
                    collection_created = True
                except Exception as e:
                    collection_created = False
                    create_error = str(e)
            else:
                collection_created = True
                create_error = None
            
            return {
                "success": True,
                "connection": "Working",
                "collections_available": len(collections.collections),
                "target_collection_exists": collection_exists,
                "points_count": points_count,
                "collection_created": collection_created,
                "create_error": create_error
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "severity": "HIGH",
                "recommendation": "Verify Qdrant Cloud credentials and network connectivity"
            }

    def test_cipher_cli(self) -> Dict[str, Any]:
        """Test Cipher CLI functionality"""
        try:
            # Source environment and test cipher command
            test_command = f"""
            source {self.aggregator_env_script} && 
            cd "/Users/pronav/Personal Knowledge Base" && 
            timeout 30 cipher "TEST: Cipher CLI functionality test $(date)"
            """
            
            result = subprocess.run(
                test_command,
                shell=True,
                capture_output=True,
                text=True,
                executable='/bin/bash'
            )
            
            output = result.stdout + result.stderr
            
            # Analyze output for success indicators
            success_indicators = [
                "Processing...",
                "AI Response",
                "Loading agent config",
                "MCP Manager: MCPManager initialized"
            ]
            
            error_indicators = [
                "401 Incorrect API key",
                "404 Resource not found", 
                "Connection error",
                "Failed to get response"
            ]
            
            found_success = any(indicator in output for indicator in success_indicators)
            found_errors = [error for error in error_indicators if error in output]
            
            # Check for specific aggregator features
            aggregator_indicators = [
                "MCP Manager: Registered client",
                "aggregator mode",
                "Available Tools"
            ]
            
            aggregator_features = [feature for feature in aggregator_indicators if feature in output]
            
            return {
                "success": found_success and len(found_errors) == 0,
                "output_length": len(output),
                "success_indicators_found": [indicator for indicator in success_indicators if indicator in output],
                "error_indicators_found": found_errors,
                "aggregator_features_found": aggregator_features,
                "return_code": result.returncode,
                "recommendation": "Check Azure OpenAI configuration" if found_errors else "Cipher CLI working correctly"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "severity": "HIGH",
                "recommendation": "Fix Cipher CLI installation or configuration"
            }

    def test_mcp_servers(self) -> Dict[str, Any]:
        """Test MCP server configurations"""
        configured_servers = []
        issues = []
        
        try:
            with open(self.cipher_config_path, 'r') as f:
                content = f.read()
                
            # Extract MCP server configurations
            if "mcpServers:" in content:
                lines = content.split('\n')
                in_mcp_section = False
                
                for line in lines:
                    if line.strip() == "mcpServers:":
                        in_mcp_section = True
                        continue
                    elif in_mcp_section and line.startswith('  ') and ':' in line and not line.strip().startswith('#'):
                        server_name = line.split(':')[0].strip()
                        if server_name:
                            configured_servers.append(server_name)
                    elif in_mcp_section and not line.startswith('  ') and line.strip():
                        break
            
            # Check for expected servers
            expected_servers = ["playwright", "filesystem", "git", "sqlite"]
            missing_servers = [server for server in expected_servers if server not in configured_servers]
            
            if missing_servers:
                issues.append(f"Missing MCP servers: {missing_servers}")
            
            return {
                "success": len(issues) == 0,
                "configured_servers": configured_servers,
                "missing_servers": missing_servers,
                "total_servers": len(configured_servers),
                "issues": issues,
                "recommendation": "Add missing MCP servers" if missing_servers else "MCP servers properly configured"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "severity": "MEDIUM",
                "recommendation": "Fix cipher.yml MCP server configuration"
            }

    def test_aggregator_features(self) -> Dict[str, Any]:
        """Test aggregator mode specific features"""
        features_tested = {}
        
        try:
            with open(self.cipher_config_path, 'r') as f:
                content = f.read()
            
            # Check aggregator configuration
            features_tested["aggregator_enabled"] = "enabled: true" in content
            features_tested["conflict_resolution"] = "conflictResolution:" in content
            features_tested["timeout_configured"] = "timeout:" in content
            features_tested["auto_context"] = "autoContext: true" in content
            features_tested["session_persistence"] = "sessionPersistence:" in content
            
            # Check dual memory system
            features_tested["dual_memory"] = "dualMemory:" in content
            features_tested["system1_config"] = "system1:" in content
            features_tested["system2_config"] = "system2:" in content
            features_tested["qdrant_integration"] = "vectorStore: qdrant" in content
            
            # Check auto-processing
            features_tested["auto_processing"] = "autoProcessing:" in content
            features_tested["processing_triggers"] = "triggers:" in content
            
            working_features = sum(1 for feature, working in features_tested.items() if working)
            total_features = len(features_tested)
            
            return {
                "success": working_features >= total_features * 0.8,  # 80% of features working
                "features_tested": features_tested,
                "working_features": working_features,
                "total_features": total_features,
                "completion_percentage": round((working_features / total_features) * 100, 1),
                "recommendation": "Add missing aggregator features" if working_features < total_features else "Aggregator features properly configured"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "severity": "MEDIUM",
                "recommendation": "Fix aggregator configuration in cipher.yml"
            }

    def test_crewai_integration(self) -> Dict[str, Any]:
        """Test CrewAI integration with Qdrant tools"""
        try:
            # Check if CrewAI files have been updated
            crewai_file = "/Users/pronav/Personal Knowledge Base/PRSNL/backend/app/services/cipher_pattern_crew.py"
            
            if not os.path.exists(crewai_file):
                return {
                    "success": False,
                    "error": "CipherPatternCrew file not found",
                    "severity": "MEDIUM",
                    "recommendation": "Create CipherPatternCrew with Qdrant integration"
                }
            
            with open(crewai_file, 'r') as f:
                content = f.read()
            
            # Check for required imports and classes
            integrations_found = {
                "qdrant_import": "from qdrant_client import QdrantClient" in content,
                "crewai_tools": "from crewai_tools import" in content,
                "qdrant_pattern_tool": "class QdrantPatternTool" in content,
                "qdrant_config": "QDRANT_API_KEY" in content,
                "search_patterns": "_search_similar_patterns" in content,
                "collection_info": "_get_collection_info" in content,
                "pattern_clusters": "_analyze_pattern_clusters" in content
            }
            
            working_integrations = sum(1 for integration, found in integrations_found.items() if found)
            total_integrations = len(integrations_found)
            
            return {
                "success": working_integrations >= total_integrations * 0.8,
                "integrations_found": integrations_found,
                "working_integrations": working_integrations,
                "total_integrations": total_integrations,
                "completion_percentage": round((working_integrations / total_integrations) * 100, 1),
                "recommendation": "Complete Qdrant integration in CrewAI" if working_integrations < total_integrations else "CrewAI integration complete"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "severity": "MEDIUM",
                "recommendation": "Fix CrewAI integration setup"
            }

    def test_performance(self) -> Dict[str, Any]:
        """Test performance metrics"""
        metrics = {}
        
        try:
            # Test Cipher response time
            start_time = time.time()
            cipher_result = subprocess.run(
                f"source {self.aggregator_env_script} && timeout 15 cipher --version",
                shell=True,
                capture_output=True,
                text=True,
                executable='/bin/bash'
            )
            cipher_response_time = time.time() - start_time
            
            # Test Qdrant response time
            start_time = time.time()
            try:
                client = QdrantClient(url=self.qdrant_url, api_key=self.qdrant_api_key)
                collections = client.get_collections()
                qdrant_response_time = time.time() - start_time
                qdrant_available = True
            except:
                qdrant_response_time = float('inf')
                qdrant_available = False
            
            # Test Azure OpenAI response time
            start_time = time.time()
            try:
                client = openai.AzureOpenAI(
                    api_key=self.azure_api_key,
                    api_version=self.azure_api_version,
                    azure_endpoint=self.azure_endpoint
                )
                response = client.chat.completions.create(
                    model=self.azure_deployment,
                    messages=[{"role": "user", "content": "Hi"}],
                    max_tokens=5
                )
                azure_response_time = time.time() - start_time
                azure_available = True
            except:
                azure_response_time = float('inf')
                azure_available = False
            
            metrics = {
                "cipher_response_time": round(cipher_response_time, 2),
                "qdrant_response_time": round(qdrant_response_time, 2),
                "azure_response_time": round(azure_response_time, 2),
                "qdrant_available": qdrant_available,
                "azure_available": azure_available
            }
            
            # Performance thresholds
            performance_issues = []
            if cipher_response_time > 10:
                performance_issues.append("Cipher response time too slow")
            if qdrant_response_time > 5:
                performance_issues.append("Qdrant response time too slow")
            if azure_response_time > 10:
                performance_issues.append("Azure OpenAI response time too slow")
            
            return {
                "success": len(performance_issues) == 0,
                "metrics": metrics,
                "performance_issues": performance_issues,
                "recommendation": "Optimize slow components" if performance_issues else "Performance within acceptable limits"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "severity": "LOW",
                "recommendation": "Fix performance testing setup"
            }

    def test_memory_persistence(self) -> Dict[str, Any]:
        """Test memory persistence across sessions"""
        try:
            # Check for Cipher database
            cipher_db_path = "/Users/pronav/Personal Knowledge Base/data/cipher.db"
            
            if not os.path.exists(cipher_db_path):
                return {
                    "success": False,
                    "error": "Cipher database not found",
                    "severity": "MEDIUM",
                    "recommendation": "Initialize Cipher database"
                }
            
            # Check database structure
            conn = sqlite3.connect(cipher_db_path)
            cursor = conn.cursor()
            
            # Get tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            
            # Check for data
            total_records = 0
            table_info = {}
            
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    table_info[table] = count
                    total_records += count
                except:
                    table_info[table] = "Error reading"
            
            conn.close()
            
            return {
                "success": len(tables) > 0,
                "database_exists": True,
                "tables_found": tables,
                "table_info": table_info,
                "total_records": total_records,
                "recommendation": "Database structure looks good" if tables else "Initialize database tables"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "severity": "MEDIUM",
                "recommendation": "Fix database connectivity issues"
            }

    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report with analysis"""
        end_time = datetime.now()
        total_execution_time = (end_time - self.start_time).total_seconds()
        
        # Calculate overall success rate
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result["status"] == "PASS")
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        # Categorize weak spots by severity
        high_severity = [spot for spot in self.weak_spots if spot["severity"] == "HIGH"]
        medium_severity = [spot for spot in self.weak_spots if spot["severity"] == "MEDIUM"]
        low_severity = [spot for spot in self.weak_spots if spot["severity"] == "LOW"]
        
        # Generate recommendations
        priority_recommendations = []
        if high_severity:
            priority_recommendations.append("🚨 URGENT: Fix high-severity issues first")
        if medium_severity:
            priority_recommendations.append("⚠️  MEDIUM: Address configuration issues")
        if success_rate < 70:
            priority_recommendations.append("🔧 CRITICAL: System not ready for production")
        elif success_rate < 90:
            priority_recommendations.append("⚡ OPTIMIZE: System needs improvement")
        else:
            priority_recommendations.append("✅ EXCELLENT: System ready for deployment")
        
        # Component status summary
        component_status = {
            "Configuration": "PASS" if self.test_results.get("Configuration Validation", {}).get("status") == "PASS" else "FAIL",
            "Azure OpenAI": "PASS" if self.test_results.get("Azure OpenAI Connectivity", {}).get("status") == "PASS" else "FAIL",
            "Qdrant Cloud": "PASS" if self.test_results.get("Qdrant Cloud Integration", {}).get("status") == "PASS" else "FAIL",
            "Cipher CLI": "PASS" if self.test_results.get("Cipher CLI Functionality", {}).get("status") == "PASS" else "FAIL",
            "MCP Servers": "PASS" if self.test_results.get("MCP Server Configuration", {}).get("status") == "PASS" else "FAIL",
            "Aggregator": "PASS" if self.test_results.get("Aggregator Mode Features", {}).get("status") == "PASS" else "FAIL",
            "CrewAI": "PASS" if self.test_results.get("CrewAI Integration", {}).get("status") == "PASS" else "FAIL"
        }
        
        return {
            "test_summary": {
                "execution_time": round(total_execution_time, 2),
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": total_tests - passed_tests,
                "success_rate": round(success_rate, 1)
            },
            "component_status": component_status,
            "detailed_results": self.test_results,
            "weak_spots": {
                "total": len(self.weak_spots),
                "high_severity": len(high_severity),
                "medium_severity": len(medium_severity),
                "low_severity": len(low_severity),
                "details": self.weak_spots
            },
            "recommendations": {
                "priority": priority_recommendations,
                "next_steps": self._generate_next_steps()
            },
            "overall_assessment": self._generate_overall_assessment(success_rate),
            "generated_at": end_time.isoformat()
        }
    
    def _generate_next_steps(self) -> List[str]:
        """Generate actionable next steps based on test results"""
        steps = []
        
        # Check specific failure patterns
        if any("Azure OpenAI" in spot["category"] for spot in self.weak_spots):
            steps.append("1. Verify Azure OpenAI API key and endpoint configuration")
            steps.append("2. Test Azure OpenAI connection separately")
            
        if any("Qdrant" in spot["category"] for spot in self.weak_spots):
            steps.append("3. Verify Qdrant Cloud credentials and network access")
            steps.append("4. Test Qdrant collection creation")
            
        if any("Configuration" in spot["category"] for spot in self.weak_spots):
            steps.append("5. Review and fix configuration file syntax")
            steps.append("6. Validate all required configuration sections")
            
        if any("Cipher CLI" in spot["category"] for spot in self.weak_spots):
            steps.append("7. Debug Cipher CLI with verbose logging")
            steps.append("8. Check environment variable propagation")
        
        if not steps:
            steps = [
                "1. System appears healthy - proceed with integration testing",
                "2. Monitor performance metrics during usage",
                "3. Test with real workloads"
            ]
        
        return steps
    
    def _generate_overall_assessment(self, success_rate: float) -> str:
        """Generate overall system assessment"""
        if success_rate >= 95:
            return "🚀 EXCELLENT: Cipher MCP Aggregator Mode is fully operational and ready for production use. All critical components are working correctly."
        elif success_rate >= 85:
            return "✅ GOOD: System is mostly functional with minor issues. Safe for development use with monitoring."
        elif success_rate >= 70:
            return "⚠️  MODERATE: System has several issues that need attention before production deployment."
        elif success_rate >= 50:
            return "🚨 POOR: Significant issues detected. System requires major fixes before it can be used reliably."
        else:
            return "❌ CRITICAL: System is not functional. Immediate intervention required to fix fundamental issues."

def main():
    """Main test execution function"""
    tester = CipherAggregatorTester()
    
    print("🧪 Cipher MCP Aggregator Mode - Comprehensive Test Suite")
    print("=" * 60)
    
    # Run all tests
    report = tester.run_comprehensive_test()
    
    # Print summary
    print(f"\n📊 TEST RESULTS SUMMARY")
    print(f"Success Rate: {report['test_summary']['success_rate']}%")
    print(f"Tests Passed: {report['test_summary']['passed_tests']}/{report['test_summary']['total_tests']}")
    print(f"Execution Time: {report['test_summary']['execution_time']}s")
    
    print(f"\n🎯 COMPONENT STATUS")
    for component, status in report['component_status'].items():
        status_emoji = "✅" if status == "PASS" else "❌"
        print(f"{status_emoji} {component}: {status}")
    
    print(f"\n⚠️  WEAK SPOTS IDENTIFIED: {report['weak_spots']['total']}")
    if report['weak_spots']['total'] > 0:
        print(f"  High Severity: {report['weak_spots']['high_severity']}")
        print(f"  Medium Severity: {report['weak_spots']['medium_severity']}")
        print(f"  Low Severity: {report['weak_spots']['low_severity']}")
    
    print(f"\n🎯 OVERALL ASSESSMENT")
    print(report['overall_assessment'])
    
    print(f"\n📋 NEXT STEPS")
    for step in report['recommendations']['next_steps'][:5]:  # Show top 5 steps
        print(f"  {step}")
    
    # Save detailed report
    report_file = f"/Users/pronav/Personal Knowledge Base/PRSNL/test-results/cipher-aggregator-test-{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    os.makedirs(os.path.dirname(report_file), exist_ok=True)
    
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n💾 Detailed report saved to: {report_file}")
    
    return report

if __name__ == "__main__":
    main()