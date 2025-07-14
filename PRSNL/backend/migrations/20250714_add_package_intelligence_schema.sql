-- Migration: Add Package Intelligence Schema
-- Date: 2025-07-14
-- Description: Complete database schema for package intelligence system

-- Table for tracking package dependencies across projects
CREATE TABLE IF NOT EXISTS package_dependencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repo_id UUID REFERENCES github_repos(id) ON DELETE CASCADE,
    analysis_id UUID,
    package_name VARCHAR(255) NOT NULL,
    package_version VARCHAR(100),
    package_manager VARCHAR(50) NOT NULL, -- npm, pypi, cargo, maven, etc.
    dependency_type VARCHAR(50) DEFAULT 'runtime', -- runtime, dev, peer, optional
    file_source VARCHAR(500), -- package.json, requirements.txt, etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table for package metadata and health information
CREATE TABLE IF NOT EXISTS package_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    package_name VARCHAR(255) NOT NULL,
    package_manager VARCHAR(50) NOT NULL,
    latest_version VARCHAR(100),
    description TEXT,
    license VARCHAR(100),
    homepage VARCHAR(500),
    repository_url VARCHAR(500),
    downloads BIGINT DEFAULT 0,
    last_updated TIMESTAMP,
    deprecated BOOLEAN DEFAULT FALSE,
    maintenance_score FLOAT DEFAULT 0.0,
    metadata JSONB,
    cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(package_name, package_manager)
);

-- Table for security vulnerabilities
CREATE TABLE IF NOT EXISTS package_vulnerabilities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    package_name VARCHAR(255) NOT NULL,
    package_manager VARCHAR(50) NOT NULL,
    vulnerability_id VARCHAR(100) NOT NULL, -- CVE-ID, GHSA-ID, etc.
    severity VARCHAR(20) NOT NULL, -- low, moderate, high, critical
    title VARCHAR(500) NOT NULL,
    description TEXT,
    vulnerable_versions VARCHAR(200),
    patched_versions VARCHAR(200),
    published_date TIMESTAMP,
    source VARCHAR(100), -- nvd, github, rustsec, etc.
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(package_name, package_manager, vulnerability_id)
);

-- Table for license compliance tracking
CREATE TABLE IF NOT EXISTS package_licenses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repo_id UUID REFERENCES github_repos(id) ON DELETE CASCADE,
    analysis_id UUID,
    license_name VARCHAR(100) NOT NULL,
    license_type VARCHAR(50), -- permissive, copyleft, proprietary, etc.
    package_count INTEGER DEFAULT 1,
    risk_level VARCHAR(20) DEFAULT 'low', -- low, medium, high
    compliance_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table for package analysis summaries per project
CREATE TABLE IF NOT EXISTS package_analysis_summary (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repo_id UUID REFERENCES github_repos(id) ON DELETE CASCADE,
    analysis_id UUID,
    total_dependencies INTEGER DEFAULT 0,
    total_vulnerabilities INTEGER DEFAULT 0,
    critical_vulnerabilities INTEGER DEFAULT 0,
    high_vulnerabilities INTEGER DEFAULT 0,
    moderate_vulnerabilities INTEGER DEFAULT 0,
    low_vulnerabilities INTEGER DEFAULT 0,
    package_managers TEXT[], -- Array of detected package managers
    license_issues INTEGER DEFAULT 0,
    maintenance_issues INTEGER DEFAULT 0,
    security_score FLOAT DEFAULT 0.0,
    recommendation_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_package_dependencies_repo_id ON package_dependencies(repo_id);
CREATE INDEX idx_package_dependencies_name_manager ON package_dependencies(package_name, package_manager);
CREATE INDEX idx_package_dependencies_analysis_id ON package_dependencies(analysis_id);

CREATE INDEX idx_package_metadata_name_manager ON package_metadata(package_name, package_manager);
CREATE INDEX idx_package_metadata_cached_at ON package_metadata(cached_at);
CREATE INDEX idx_package_metadata_deprecated ON package_metadata(deprecated);

CREATE INDEX idx_package_vulnerabilities_name_manager ON package_vulnerabilities(package_name, package_manager);
CREATE INDEX idx_package_vulnerabilities_severity ON package_vulnerabilities(severity);
CREATE INDEX idx_package_vulnerabilities_published ON package_vulnerabilities(published_date DESC);

CREATE INDEX idx_package_licenses_repo_id ON package_licenses(repo_id);
CREATE INDEX idx_package_licenses_analysis_id ON package_licenses(analysis_id);
CREATE INDEX idx_package_licenses_risk_level ON package_licenses(risk_level);

CREATE INDEX idx_package_analysis_summary_repo_id ON package_analysis_summary(repo_id);
CREATE INDEX idx_package_analysis_summary_analysis_id ON package_analysis_summary(analysis_id);
CREATE INDEX idx_package_analysis_summary_created ON package_analysis_summary(created_at DESC);

-- Views for easy querying
CREATE OR REPLACE VIEW package_security_overview AS
SELECT 
    pas.repo_id,
    pas.analysis_id,
    gr.name as repository_name,
    pas.total_dependencies,
    pas.total_vulnerabilities,
    pas.critical_vulnerabilities,
    pas.high_vulnerabilities,
    pas.security_score,
    array_to_string(pas.package_managers, ', ') as package_managers,
    pas.created_at
FROM package_analysis_summary pas
JOIN github_repos gr ON pas.repo_id = gr.id
ORDER BY pas.created_at DESC;

CREATE OR REPLACE VIEW high_risk_packages AS
SELECT 
    pd.repo_id,
    pd.package_name,
    pd.package_manager,
    pd.package_version,
    COUNT(pv.id) as vulnerability_count,
    MAX(CASE WHEN pv.severity = 'critical' THEN 1 ELSE 0 END) as has_critical,
    pm.deprecated,
    pm.maintenance_score
FROM package_dependencies pd
LEFT JOIN package_vulnerabilities pv ON pd.package_name = pv.package_name 
    AND pd.package_manager = pv.package_manager
LEFT JOIN package_metadata pm ON pd.package_name = pm.package_name 
    AND pd.package_manager = pm.package_manager
GROUP BY pd.repo_id, pd.package_name, pd.package_manager, pd.package_version, pm.deprecated, pm.maintenance_score
HAVING COUNT(pv.id) > 0 OR pm.deprecated = true OR pm.maintenance_score < 0.5
ORDER BY has_critical DESC, vulnerability_count DESC;

-- Function to update package analysis summary
CREATE OR REPLACE FUNCTION update_package_analysis_summary(
    p_repo_id UUID,
    p_analysis_id UUID
) RETURNS UUID AS $$
DECLARE
    summary_id UUID;
    dep_count INTEGER;
    vuln_stats RECORD;
    license_issues INTEGER;
    maintenance_issues INTEGER;
    managers TEXT[];
BEGIN
    -- Get dependency count
    SELECT COUNT(*) INTO dep_count
    FROM package_dependencies
    WHERE repo_id = p_repo_id AND analysis_id = p_analysis_id;
    
    -- Get vulnerability statistics
    SELECT 
        COUNT(*) as total_vulns,
        COUNT(CASE WHEN pv.severity = 'critical' THEN 1 END) as critical,
        COUNT(CASE WHEN pv.severity = 'high' THEN 1 END) as high,
        COUNT(CASE WHEN pv.severity = 'moderate' THEN 1 END) as moderate,
        COUNT(CASE WHEN pv.severity = 'low' THEN 1 END) as low
    INTO vuln_stats
    FROM package_dependencies pd
    LEFT JOIN package_vulnerabilities pv ON pd.package_name = pv.package_name 
        AND pd.package_manager = pv.package_manager
    WHERE pd.repo_id = p_repo_id AND pd.analysis_id = p_analysis_id;
    
    -- Get license issues
    SELECT COUNT(*) INTO license_issues
    FROM package_licenses
    WHERE repo_id = p_repo_id AND analysis_id = p_analysis_id AND risk_level IN ('medium', 'high');
    
    -- Get maintenance issues
    SELECT COUNT(*) INTO maintenance_issues
    FROM package_dependencies pd
    JOIN package_metadata pm ON pd.package_name = pm.package_name 
        AND pd.package_manager = pm.package_manager
    WHERE pd.repo_id = p_repo_id AND pd.analysis_id = p_analysis_id 
        AND (pm.deprecated = true OR pm.maintenance_score < 0.5);
    
    -- Get package managers
    SELECT array_agg(DISTINCT package_manager) INTO managers
    FROM package_dependencies
    WHERE repo_id = p_repo_id AND analysis_id = p_analysis_id;
    
    -- Insert or update summary
    INSERT INTO package_analysis_summary (
        repo_id, analysis_id, total_dependencies, total_vulnerabilities,
        critical_vulnerabilities, high_vulnerabilities, moderate_vulnerabilities, low_vulnerabilities,
        package_managers, license_issues, maintenance_issues,
        security_score, recommendation_count
    ) VALUES (
        p_repo_id, p_analysis_id, dep_count, vuln_stats.total_vulns,
        vuln_stats.critical, vuln_stats.high, vuln_stats.moderate, vuln_stats.low,
        managers, license_issues, maintenance_issues,
        GREATEST(0, 1.0 - (vuln_stats.critical * 0.4 + vuln_stats.high * 0.2 + maintenance_issues * 0.1)),
        (vuln_stats.total_vulns + license_issues + maintenance_issues)
    )
    ON CONFLICT (repo_id, analysis_id) 
    DO UPDATE SET
        total_dependencies = EXCLUDED.total_dependencies,
        total_vulnerabilities = EXCLUDED.total_vulnerabilities,
        critical_vulnerabilities = EXCLUDED.critical_vulnerabilities,
        high_vulnerabilities = EXCLUDED.high_vulnerabilities,
        moderate_vulnerabilities = EXCLUDED.moderate_vulnerabilities,
        low_vulnerabilities = EXCLUDED.low_vulnerabilities,
        package_managers = EXCLUDED.package_managers,
        license_issues = EXCLUDED.license_issues,
        maintenance_issues = EXCLUDED.maintenance_issues,
        security_score = EXCLUDED.security_score,
        recommendation_count = EXCLUDED.recommendation_count,
        created_at = CURRENT_TIMESTAMP
    RETURNING id INTO summary_id;
    
    RETURN summary_id;
END;
$$ LANGUAGE plpgsql;

-- Add unique constraints for analysis summaries
ALTER TABLE package_analysis_summary 
ADD CONSTRAINT unique_repo_analysis 
UNIQUE (repo_id, analysis_id);

-- Comments for documentation
COMMENT ON TABLE package_dependencies IS 'Tracks all package dependencies found in repositories';
COMMENT ON TABLE package_metadata IS 'Cached metadata and health information for packages';
COMMENT ON TABLE package_vulnerabilities IS 'Known security vulnerabilities for packages';
COMMENT ON TABLE package_licenses IS 'License compliance tracking per analysis';
COMMENT ON TABLE package_analysis_summary IS 'Aggregated package analysis results per repository';
COMMENT ON VIEW package_security_overview IS 'High-level security overview across repositories';
COMMENT ON VIEW high_risk_packages IS 'Packages with security or maintenance concerns';