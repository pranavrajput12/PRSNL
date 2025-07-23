"""
Security Key Generation Utilities for PRSNL
===========================================

Provides secure key generation and validation for production deployments.

CRITICAL SECURITY NOTE:
Default keys in config.py are placeholders and MUST be replaced in production.
This utility generates cryptographically secure keys for:
- JWT signing (SECRET_KEY)
- Data encryption (ENCRYPTION_KEY)
- Session management
"""

import os
import secrets
import base64
from cryptography.fernet import Fernet
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

class SecurityKeyGenerator:
    """Generate and validate cryptographically secure keys"""
    
    # Known weak/default keys that should trigger security warnings
    INSECURE_KEYS = {
        "change-me-in-production-to-a-secure-random-value",
        "default-encryption-key-change-in-production",
        "your-secret-key-here",
        "insecure-key",
        "test-key",
        "dev-key",
        "demo-key",
        "secret",
        "password",
        "key"
    }
    
    @staticmethod
    def generate_secret_key(length: int = 64) -> str:
        """
        Generate a cryptographically secure secret key for JWT signing.
        
        Args:
            length: Key length in bytes (default: 64 for 512-bit security)
            
        Returns:
            Base64-encoded secure random key
        """
        # Generate cryptographically secure random bytes
        key_bytes = secrets.token_bytes(length)
        
        # Encode as base64 for easy storage in environment variables
        key_b64 = base64.urlsafe_b64encode(key_bytes).decode('utf-8')
        
        logger.info(f"Generated secure SECRET_KEY with {length * 8}-bit entropy")
        return key_b64
    
    @staticmethod
    def generate_encryption_key() -> str:
        """
        Generate a Fernet-compatible encryption key.
        
        Returns:
            Base64-encoded Fernet key (256-bit)
        """
        # Generate Fernet key (32 bytes / 256 bits)
        fernet_key = Fernet.generate_key()
        key_str = fernet_key.decode('utf-8')
        
        logger.info("Generated secure ENCRYPTION_KEY (Fernet-compatible, 256-bit)")
        return key_str
    
    @staticmethod
    def validate_key_security(key: str, key_name: str) -> Tuple[bool, List[str]]:
        """
        Validate that a key meets security requirements.
        
        Args:
            key: The key to validate
            key_name: Name of the key for logging (e.g., "SECRET_KEY")
            
        Returns:
            Tuple of (is_secure, list_of_warnings)
        """
        warnings = []
        is_secure = True
        
        # Check for known insecure keys
        if key.lower() in SecurityKeyGenerator.INSECURE_KEYS:
            warnings.append(f"{key_name} is using a known insecure default value")
            is_secure = False
        
        # Check key length
        if len(key) < 32:
            warnings.append(f"{key_name} is too short (minimum 32 characters)")
            is_secure = False
        
        # Check for obvious patterns
        if key.count("a") > len(key) * 0.5 or key.count("1") > len(key) * 0.5:
            warnings.append(f"{key_name} appears to use repetitive patterns")
            is_secure = False
        
        # Check for common weak patterns
        weak_patterns = ["12345", "abcde", "qwerty", "password", "secret"]
        for pattern in weak_patterns:
            if pattern in key.lower():
                warnings.append(f"{key_name} contains weak pattern: {pattern}")
                is_secure = False
        
        # Check entropy (basic)
        unique_chars = len(set(key))
        if unique_chars < len(key) * 0.3:  # Less than 30% unique characters
            warnings.append(f"{key_name} has low entropy ({unique_chars} unique chars)")
            is_secure = False
        
        return is_secure, warnings
    
    @staticmethod
    def audit_current_keys() -> Dict[str, Dict]:
        """
        Audit the current key configuration for security issues.
        
        Returns:
            Dictionary with security assessment for each key
        """
        from app.config import settings
        
        audit_results = {}
        critical_issues = 0
        
        # Audit SECRET_KEY
        secret_key = settings.SECRET_KEY
        is_secure, warnings = SecurityKeyGenerator.validate_key_security(secret_key, "SECRET_KEY")
        audit_results["SECRET_KEY"] = {
            "secure": is_secure,
            "warnings": warnings,
            "severity": "CRITICAL" if not is_secure else "OK",
            "length": len(secret_key)
        }
        if not is_secure:
            critical_issues += 1
        
        # Audit ENCRYPTION_KEY
        encryption_key = settings.ENCRYPTION_KEY
        is_secure, warnings = SecurityKeyGenerator.validate_key_security(encryption_key, "ENCRYPTION_KEY")
        audit_results["ENCRYPTION_KEY"] = {
            "secure": is_secure,
            "warnings": warnings,
            "severity": "CRITICAL" if not is_secure else "OK",
            "length": len(encryption_key)
        }
        if not is_secure:
            critical_issues += 1
        
        # Overall assessment
        audit_results["summary"] = {
            "total_keys_audited": 2,
            "critical_issues": critical_issues,
            "overall_status": "SECURE" if critical_issues == 0 else "INSECURE",
            "recommendation": "IMMEDIATE ACTION REQUIRED" if critical_issues > 0 else "Keys are secure"
        }
        
        return audit_results
    
    @staticmethod
    def generate_env_template() -> str:
        """
        Generate a .env template with secure keys.
        
        Returns:
            String containing .env template with generated secure keys
        """
        secret_key = SecurityKeyGenerator.generate_secret_key()
        encryption_key = SecurityKeyGenerator.generate_encryption_key()
        
        template = f"""# PRSNL Production Environment Configuration
# Generated on: {os.popen('date').read().strip()}
# 
# CRITICAL SECURITY NOTE:
# These keys have been generated with cryptographically secure random values.
# Store them securely and never commit them to version control.

# JWT Signing Key (512-bit entropy)
SECRET_KEY={secret_key}

# Data Encryption Key (Fernet-compatible, 256-bit)
ENCRYPTION_KEY={encryption_key}

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/prsnl

# Add other environment variables as needed...
"""
        
        return template
    
    @staticmethod
    def log_security_warning():
        """Log critical security warnings about insecure keys"""
        audit = SecurityKeyGenerator.audit_current_keys()
        
        if audit["summary"]["critical_issues"] > 0:
            logger.critical("🚨 CRITICAL SECURITY VULNERABILITY DETECTED!")
            logger.critical("=" * 60)
            
            for key_name, key_audit in audit.items():
                if key_name == "summary":
                    continue
                    
                if not key_audit["secure"]:
                    logger.critical(f"❌ {key_name}: INSECURE")
                    for warning in key_audit["warnings"]:
                        logger.critical(f"   - {warning}")
                    logger.critical("")
            
            logger.critical("🔥 IMMEDIATE ACTION REQUIRED:")
            logger.critical("1. Generate secure keys: python -c 'from app.utils.security_keys import SecurityKeyGenerator; print(SecurityKeyGenerator.generate_env_template())'")
            logger.critical("2. Update your .env file with the generated keys")
            logger.critical("3. Restart the application")
            logger.critical("4. Never use default keys in production!")
            logger.critical("=" * 60)
        else:
            logger.info("✅ Security key audit passed - all keys are secure")


def main():
    """CLI utility for generating secure keys"""
    import argparse
    
    parser = argparse.ArgumentParser(description="PRSNL Security Key Generator")
    parser.add_argument("--audit", action="store_true", help="Audit current keys")
    parser.add_argument("--generate-env", action="store_true", help="Generate .env template")
    parser.add_argument("--secret-key", action="store_true", help="Generate SECRET_KEY only")
    parser.add_argument("--encryption-key", action="store_true", help="Generate ENCRYPTION_KEY only")
    
    args = parser.parse_args()
    
    if args.audit:
        print("🔍 Auditing current security keys...")
        audit = SecurityKeyGenerator.audit_current_keys()
        
        for key_name, key_audit in audit.items():
            if key_name == "summary":
                continue
            print(f"\n{key_name}:")
            print(f"  Status: {'✅ SECURE' if key_audit['secure'] else '❌ INSECURE'}")
            print(f"  Length: {key_audit['length']} characters")
            if key_audit['warnings']:
                print("  Warnings:")
                for warning in key_audit['warnings']:
                    print(f"    - {warning}")
        
        summary = audit["summary"]
        print(f"\n📊 Summary:")
        print(f"  Overall Status: {summary['overall_status']}")
        print(f"  Critical Issues: {summary['critical_issues']}")
        print(f"  Recommendation: {summary['recommendation']}")
        
    elif args.generate_env:
        print("🔐 Generating secure .env template...")
        template = SecurityKeyGenerator.generate_env_template()
        print(template)
        
    elif args.secret_key:
        print("🔑 Generating SECRET_KEY...")
        key = SecurityKeyGenerator.generate_secret_key()
        print(f"SECRET_KEY={key}")
        
    elif args.encryption_key:
        print("🔐 Generating ENCRYPTION_KEY...")
        key = SecurityKeyGenerator.generate_encryption_key()
        print(f"ENCRYPTION_KEY={key}")
        
    else:
        print("🔐 Generating both keys...")
        secret_key = SecurityKeyGenerator.generate_secret_key()
        encryption_key = SecurityKeyGenerator.generate_encryption_key()
        print(f"SECRET_KEY={secret_key}")
        print(f"ENCRYPTION_KEY={encryption_key}")


if __name__ == "__main__":
    main()