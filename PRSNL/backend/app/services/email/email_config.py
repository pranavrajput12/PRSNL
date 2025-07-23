"""
Email configuration for PRSNL
Only handling signup, login, and welcome scenarios for now
"""
from enum import Enum
from typing import Dict, Any

class EmailType(Enum):
    """Email types we currently support"""
    VERIFICATION = "verification"  # Signup verification
    WELCOME = "welcome"            # Post-verification welcome
    MAGIC_LINK = "magic_link"      # Passwordless login
    PASSWORD_RESET = "password_reset"  # Password reset
    
    # Future email types (not implemented yet)
    # FIRST_CAPTURE = "first_capture"
    # WEEKLY_REPORT = "weekly_report"
    # CODE_INSIGHT = "code_insight"
    # MILESTONE = "milestone"

# Email configuration for different types
EMAIL_CONFIG: Dict[EmailType, Dict[str, str]] = {
    EmailType.VERIFICATION: {
        "from": "noreply@fyi.prsnl.fyi",  # Transactional
        "from_name": "PRSNL Security"
    },
    EmailType.WELCOME: {
        "from": "hello@fyi.prsnl.fyi",
        "from_name": "PRSNL Brain Trust"
    },
    EmailType.MAGIC_LINK: {
        "from": "noreply@fyi.prsnl.fyi",  # Transactional
        "from_name": "PRSNL Security"
    },
    EmailType.PASSWORD_RESET: {
        "from": "noreply@fyi.prsnl.fyi",  # Transactional
        "from_name": "PRSNL Security"
    }
}

# Subject line templates
SUBJECT_TEMPLATES = {
    EmailType.VERIFICATION: "Verify your email for PRSNL",
    EmailType.WELCOME: "Your brain just got an upgrade 🧠",
    EmailType.MAGIC_LINK: "Your magic sign-in link for PRSNL",
    EmailType.PASSWORD_RESET: "Reset your PRSNL password"
}

# Brand voice guidelines for current email types
TONE_GUIDE = {
    EmailType.VERIFICATION: "Clear and secure, no fluff",
    EmailType.WELCOME: "Excited professor meeting a promising student",
    EmailType.MAGIC_LINK: "Efficient assistant, minimal friction",
    EmailType.PASSWORD_RESET: "Professional and reassuring, security-focused"
}