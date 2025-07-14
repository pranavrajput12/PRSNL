"""
Package Intelligence Service

Analyzes package dependencies and security for various package managers.
Focuses on free and open source APIs only.
"""

import asyncio
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from urllib.parse import urljoin

import aiohttp
from app.services.cache import cache_service

logger = logging.getLogger(__name__)

@dataclass
class PackageInfo:
    """Information about a package"""
    name: str
    version: str
    manager: str  # npm, pypi, cargo, maven
    description: Optional[str] = None
    license: Optional[str] = None
    homepage: Optional[str] = None
    repository: Optional[str] = None
    downloads: Optional[int] = None
    last_updated: Optional[datetime] = None
    vulnerabilities: List[Dict[str, Any]] = None
    dependencies: List[str] = None
    deprecated: bool = False
    maintenance_score: Optional[float] = None

@dataclass
class SecurityVulnerability:
    """Security vulnerability information"""
    id: str
    severity: str  # low, moderate, high, critical
    title: str
    description: str
    vulnerable_versions: str
    patched_versions: Optional[str] = None
    cve_id: Optional[str] = None
    published_date: Optional[datetime] = None

class PackageIntelligenceService:
    """Service for analyzing package dependencies and security"""
    
    def __init__(self):
        self.session = None
        self.cache_ttl = 3600  # 1 hour cache for package info
        self.vuln_cache_ttl = 300  # 5 minutes for vulnerability data
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'PRSNL-CodeMirror/1.0'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def analyze_project_dependencies(
        self, 
        project_path: str, 
        package_files: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Analyze all package dependencies for a project.
        
        Args:
            project_path: Path to the project
            package_files: Dict of filename -> file_content for package files
        
        Returns:
            Comprehensive package analysis results
        """
        results = {
            'project_path': project_path,
            'analysis_timestamp': datetime.utcnow().isoformat(),
            'package_managers': {},
            'total_dependencies': 0,
            'total_vulnerabilities': 0,
            'security_summary': {
                'critical': 0,
                'high': 0,
                'moderate': 0,
                'low': 0
            },
            'license_summary': {},
            'maintenance_issues': [],
            'recommendations': []
        }
        
        # Analyze each package manager
        for filename, content in package_files.items():
            if filename == 'package.json':
                npm_results = await self._analyze_npm_dependencies(content)
                results['package_managers']['npm'] = npm_results
            elif filename == 'requirements.txt' or filename.endswith('.txt'):
                pypi_results = await self._analyze_pypi_dependencies(content)
                results['package_managers']['pypi'] = pypi_results
            elif filename == 'Cargo.toml':
                cargo_results = await self._analyze_cargo_dependencies(content)
                results['package_managers']['cargo'] = cargo_results
            elif filename == 'pom.xml':
                maven_results = await self._analyze_maven_dependencies(content)
                results['package_managers']['maven'] = maven_results
        
        # Aggregate results
        await self._aggregate_analysis_results(results)
        
        return results
    
    async def _analyze_npm_dependencies(self, package_json_content: str) -> Dict[str, Any]:
        """Analyze npm package.json dependencies"""
        try:
            package_data = json.loads(package_json_content)
            dependencies = {}
            
            # Combine all dependency types
            all_deps = {}
            all_deps.update(package_data.get('dependencies', {}))
            all_deps.update(package_data.get('devDependencies', {}))
            all_deps.update(package_data.get('peerDependencies', {}))
            
            # Analyze each dependency
            for package_name, version_spec in all_deps.items():
                package_info = await self._get_npm_package_info(package_name)
                if package_info:
                    dependencies[package_name] = package_info
            
            # Check for npm vulnerabilities
            vulnerabilities = await self._check_npm_vulnerabilities(all_deps)
            
            return {
                'manager': 'npm',
                'total_packages': len(all_deps),
                'dependencies': dependencies,
                'vulnerabilities': vulnerabilities,
                'package_json_info': {
                    'name': package_data.get('name'),
                    'version': package_data.get('version'),
                    'license': package_data.get('license'),
                    'repository': package_data.get('repository'),
                    'engines': package_data.get('engines')
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing npm dependencies: {e}")
            return {'manager': 'npm', 'error': str(e)}
    
    async def _analyze_pypi_dependencies(self, requirements_content: str) -> Dict[str, Any]:
        """Analyze Python requirements.txt dependencies"""
        try:
            dependencies = {}
            lines = requirements_content.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Parse package name and version
                package_match = re.match(r'^([a-zA-Z0-9_-]+)([>=<~!]=?[\d\.]+.*)?', line)
                if package_match:
                    package_name = package_match.group(1)
                    version_spec = package_match.group(2) or ''
                    
                    package_info = await self._get_pypi_package_info(package_name)
                    if package_info:
                        dependencies[package_name] = package_info
            
            # Check for Python vulnerabilities
            vulnerabilities = await self._check_pypi_vulnerabilities(list(dependencies.keys()))
            
            return {
                'manager': 'pypi',
                'total_packages': len(dependencies),
                'dependencies': dependencies,
                'vulnerabilities': vulnerabilities
            }
            
        except Exception as e:
            logger.error(f"Error analyzing PyPI dependencies: {e}")
            return {'manager': 'pypi', 'error': str(e)}
    
    async def _analyze_cargo_dependencies(self, cargo_toml_content: str) -> Dict[str, Any]:
        """Analyze Rust Cargo.toml dependencies"""
        try:
            # Simple TOML parsing for dependencies section
            dependencies = {}
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
                    package_name = line.split('=')[0].strip().strip('"')
                    package_info = await self._get_cargo_package_info(package_name)
                    if package_info:
                        dependencies[package_name] = package_info
            
            # Check for Rust vulnerabilities
            vulnerabilities = await self._check_cargo_vulnerabilities(list(dependencies.keys()))
            
            return {
                'manager': 'cargo',
                'total_packages': len(dependencies),
                'dependencies': dependencies,
                'vulnerabilities': vulnerabilities
            }
            
        except Exception as e:
            logger.error(f"Error analyzing Cargo dependencies: {e}")
            return {'manager': 'cargo', 'error': str(e)}
    
    async def _analyze_maven_dependencies(self, pom_xml_content: str) -> Dict[str, Any]:
        """Analyze Maven pom.xml dependencies"""
        try:
            # Simple XML parsing for dependencies
            dependencies = {}
            
            # Extract artifactId values (simplified approach)
            artifact_matches = re.findall(r'<artifactId>([^<]+)</artifactId>', pom_xml_content)
            
            for artifact_id in artifact_matches:
                package_info = await self._get_maven_package_info(artifact_id)
                if package_info:
                    dependencies[artifact_id] = package_info
            
            return {
                'manager': 'maven',
                'total_packages': len(dependencies),
                'dependencies': dependencies,
                'vulnerabilities': []  # Maven Central doesn't have free vulnerability API
            }
            
        except Exception as e:
            logger.error(f"Error analyzing Maven dependencies: {e}")
            return {'manager': 'maven', 'error': str(e)}
    
    async def _get_npm_package_info(self, package_name: str) -> Optional[PackageInfo]:
        """Get package information from npm registry"""
        cache_key = f"npm_package:{package_name}"
        
        # Check cache first
        cached_info = await cache_service.get(cache_key)
        if cached_info:
            return PackageInfo(**cached_info)
        
        try:
            url = f"https://registry.npmjs.org/{package_name}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    latest_version = data.get('dist-tags', {}).get('latest', '')
                    latest_info = data.get('versions', {}).get(latest_version, {})
                    
                    package_info = PackageInfo(
                        name=package_name,
                        version=latest_version,
                        manager='npm',
                        description=data.get('description'),
                        license=latest_info.get('license'),
                        homepage=data.get('homepage'),
                        repository=data.get('repository', {}).get('url') if isinstance(data.get('repository'), dict) else data.get('repository'),
                        last_updated=datetime.fromisoformat(data.get('time', {}).get(latest_version, '').replace('Z', '+00:00')) if data.get('time', {}).get(latest_version) else None,
                        deprecated=latest_info.get('deprecated', False)
                    )
                    
                    # Cache the result
                    await cache_service.set(cache_key, package_info.__dict__, ttl=self.cache_ttl)
                    return package_info
                    
        except Exception as e:
            logger.error(f"Error fetching npm package info for {package_name}: {e}")
        
        return None
    
    async def _get_pypi_package_info(self, package_name: str) -> Optional[PackageInfo]:
        """Get package information from PyPI"""
        cache_key = f"pypi_package:{package_name}"
        
        # Check cache first
        cached_info = await cache_service.get(cache_key)
        if cached_info:
            return PackageInfo(**cached_info)
        
        try:
            url = f"https://pypi.org/pypi/{package_name}/json"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    info = data.get('info', {})
                    
                    package_info = PackageInfo(
                        name=package_name,
                        version=info.get('version', ''),
                        manager='pypi',
                        description=info.get('summary'),
                        license=info.get('license'),
                        homepage=info.get('home_page'),
                        repository=info.get('project_url'),
                        last_updated=datetime.fromisoformat(data.get('releases', {}).get(info.get('version', ''), [{}])[-1].get('upload_time', '').replace('Z', '+00:00')) if data.get('releases') else None
                    )
                    
                    # Cache the result
                    await cache_service.set(cache_key, package_info.__dict__, ttl=self.cache_ttl)
                    return package_info
                    
        except Exception as e:
            logger.error(f"Error fetching PyPI package info for {package_name}: {e}")
        
        return None
    
    async def _get_cargo_package_info(self, package_name: str) -> Optional[PackageInfo]:
        """Get package information from crates.io"""
        cache_key = f"cargo_package:{package_name}"
        
        # Check cache first
        cached_info = await cache_service.get(cache_key)
        if cached_info:
            return PackageInfo(**cached_info)
        
        try:
            url = f"https://crates.io/api/v1/crates/{package_name}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    crate_info = data.get('crate', {})
                    
                    package_info = PackageInfo(
                        name=package_name,
                        version=crate_info.get('newest_version', ''),
                        manager='cargo',
                        description=crate_info.get('description'),
                        license=crate_info.get('license'),
                        homepage=crate_info.get('homepage'),
                        repository=crate_info.get('repository'),
                        downloads=crate_info.get('downloads'),
                        last_updated=datetime.fromisoformat(crate_info.get('updated_at', '').replace('Z', '+00:00')) if crate_info.get('updated_at') else None
                    )
                    
                    # Cache the result
                    await cache_service.set(cache_key, package_info.__dict__, ttl=self.cache_ttl)
                    return package_info
                    
        except Exception as e:
            logger.error(f"Error fetching Cargo package info for {package_name}: {e}")
        
        return None
    
    async def _get_maven_package_info(self, artifact_id: str) -> Optional[PackageInfo]:
        """Get package information from Maven Central (limited free API)"""
        cache_key = f"maven_package:{artifact_id}"
        
        # Check cache first
        cached_info = await cache_service.get(cache_key)
        if cached_info:
            return PackageInfo(**cached_info)
        
        try:
            # Use Maven Central search API (free but limited)
            url = f"https://search.maven.org/solrsearch/select?q=a:{artifact_id}&rows=1&wt=json"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    docs = data.get('response', {}).get('docs', [])
                    
                    if docs:
                        doc = docs[0]
                        package_info = PackageInfo(
                            name=artifact_id,
                            version=doc.get('latestVersion', ''),
                            manager='maven',
                            description=f"Group: {doc.get('g', '')}, Artifact: {doc.get('id', '')}",
                            last_updated=datetime.fromtimestamp(doc.get('timestamp', 0) / 1000) if doc.get('timestamp') else None
                        )
                        
                        # Cache the result
                        await cache_service.set(cache_key, package_info.__dict__, ttl=self.cache_ttl)
                        return package_info
                        
        except Exception as e:
            logger.error(f"Error fetching Maven package info for {artifact_id}: {e}")
        
        return None
    
    async def _check_npm_vulnerabilities(self, packages: Dict[str, str]) -> List[SecurityVulnerability]:
        """Check npm packages for vulnerabilities"""
        vulnerabilities = []
        
        # Note: npm audit API requires package-lock.json which we don't have
        # For now, we'll return empty list and add vulnerability checking later
        # when we have more package context
        
        return vulnerabilities
    
    async def _check_pypi_vulnerabilities(self, package_names: List[str]) -> List[SecurityVulnerability]:
        """Check PyPI packages for vulnerabilities using safety DB (if available)"""
        vulnerabilities = []
        
        # Note: PyUp.io Safety DB is now commercial
        # We can implement this later with OSV database or similar free alternatives
        
        return vulnerabilities
    
    async def _check_cargo_vulnerabilities(self, package_names: List[str]) -> List[SecurityVulnerability]:
        """Check Cargo packages for vulnerabilities using RustSec database"""
        vulnerabilities = []
        
        try:
            # RustSec advisory database (free)
            url = "https://forge.rust-lang.org/infra/rustsec.html"
            # Implementation would require fetching and parsing the RustSec database
            # For now, return empty list
            
        except Exception as e:
            logger.error(f"Error checking Cargo vulnerabilities: {e}")
        
        return vulnerabilities
    
    async def _aggregate_analysis_results(self, results: Dict[str, Any]):
        """Aggregate results from all package managers"""
        total_deps = 0
        total_vulns = 0
        license_counts = {}
        maintenance_issues = []
        recommendations = []
        
        for manager, data in results['package_managers'].items():
            if 'error' in data:
                continue
                
            total_deps += data.get('total_packages', 0)
            total_vulns += len(data.get('vulnerabilities', []))
            
            # Aggregate license information
            for pkg_name, pkg_info in data.get('dependencies', {}).items():
                if hasattr(pkg_info, 'license') and pkg_info.license:
                    license_counts[pkg_info.license] = license_counts.get(pkg_info.license, 0) + 1
                
                # Check for maintenance issues
                if hasattr(pkg_info, 'deprecated') and pkg_info.deprecated:
                    maintenance_issues.append(f"Deprecated package: {pkg_name} ({manager})")
                
                if hasattr(pkg_info, 'last_updated') and pkg_info.last_updated:
                    days_since_update = (datetime.utcnow() - pkg_info.last_updated.replace(tzinfo=None)).days
                    if days_since_update > 365:  # More than 1 year
                        maintenance_issues.append(f"Stale package: {pkg_name} (last updated {days_since_update} days ago)")
        
        # Update results
        results['total_dependencies'] = total_deps
        results['total_vulnerabilities'] = total_vulns
        results['license_summary'] = license_counts
        results['maintenance_issues'] = maintenance_issues
        
        # Generate recommendations
        if total_vulns > 0:
            recommendations.append(f"Found {total_vulns} potential security vulnerabilities - review and update packages")
        
        if len(maintenance_issues) > 0:
            recommendations.append(f"Found {len(maintenance_issues)} maintenance issues - consider updating stale packages")
        
        if not results['package_managers']:
            recommendations.append("No package managers detected - ensure package files are included in analysis")
        
        results['recommendations'] = recommendations
    
    async def persist_analysis_results(
        self, 
        repo_id: Optional[str], 
        analysis_id: str, 
        analysis_results: Dict[str, Any]
    ) -> bool:
        """Persist package analysis results to database"""
        
        try:
            from app.db.database import get_db_connection
            from uuid import UUID
            
            async with get_db_connection() as db:
                repo_uuid = UUID(repo_id) if repo_id else None
                analysis_uuid = UUID(analysis_id)
                
                # Store package dependencies
                for manager, data in analysis_results.get('package_managers', {}).items():
                    if 'error' in data or 'dependencies' not in data:
                        continue
                    
                    for pkg_name, pkg_info in data['dependencies'].items():
                        # Store dependency
                        await db.execute("""
                            INSERT INTO package_dependencies (
                                repo_id, analysis_id, package_name, package_version,
                                package_manager, dependency_type, file_source
                            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                            ON CONFLICT DO NOTHING
                        """, 
                            repo_uuid, analysis_uuid, pkg_name, 
                            getattr(pkg_info, 'version', ''), manager,
                            'runtime', f"{manager} package file"
                        )
                        
                        # Store/update package metadata
                        if hasattr(pkg_info, 'name'):
                            await db.execute("""
                                INSERT INTO package_metadata (
                                    package_name, package_manager, latest_version,
                                    description, license, homepage, repository_url,
                                    downloads, last_updated, deprecated, maintenance_score
                                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                                ON CONFLICT (package_name, package_manager)
                                DO UPDATE SET
                                    latest_version = EXCLUDED.latest_version,
                                    description = EXCLUDED.description,
                                    license = EXCLUDED.license,
                                    homepage = EXCLUDED.homepage,
                                    repository_url = EXCLUDED.repository_url,
                                    downloads = EXCLUDED.downloads,
                                    last_updated = EXCLUDED.last_updated,
                                    deprecated = EXCLUDED.deprecated,
                                    maintenance_score = EXCLUDED.maintenance_score,
                                    cached_at = CURRENT_TIMESTAMP
                            """,
                                pkg_info.name, pkg_info.manager, pkg_info.version,
                                pkg_info.description, pkg_info.license, 
                                pkg_info.homepage, pkg_info.repository,
                                pkg_info.downloads, pkg_info.last_updated,
                                pkg_info.deprecated, 
                                getattr(pkg_info, 'maintenance_score', 0.8)
                            )
                
                # Store license information
                license_summary = analysis_results.get('license_summary', {})
                for license_name, count in license_summary.items():
                    if license_name and repo_uuid:
                        await db.execute("""
                            INSERT INTO package_licenses (
                                repo_id, analysis_id, license_name, package_count, risk_level
                            ) VALUES ($1, $2, $3, $4, $5)
                            ON CONFLICT DO NOTHING
                        """,
                            repo_uuid, analysis_uuid, license_name, count,
                            'low'  # Default risk level, would be calculated based on license type
                        )
                
                # Create analysis summary
                if repo_uuid:
                    await db.execute("""
                        SELECT update_package_analysis_summary($1, $2)
                    """, repo_uuid, analysis_uuid)
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to persist package analysis results: {e}")
            return False

# Singleton instance
package_intelligence_service = PackageIntelligenceService()