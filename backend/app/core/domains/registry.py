"""
Registry for Domain Specialist configurations.
"""
from typing import Dict, List, Optional
from .base import RoleFamilyConfig
from .software import SOFTWARE_CONFIG
from .analytics import ANALYTICS_CONFIG
from .core import CORE_CONFIG
from .higher_studies import HIGHER_STUDIES_CONFIG


DOMAIN_REGISTRY: Dict[str, RoleFamilyConfig] = {
    "software": SOFTWARE_CONFIG,
    "analytics": ANALYTICS_CONFIG,
    "core": CORE_CONFIG,
    "higher_studies": HIGHER_STUDIES_CONFIG
}


def get_domain_config(family_id: str) -> Optional[RoleFamilyConfig]:
    """Retrieve a specific domain configuration."""
    return DOMAIN_REGISTRY.get(family_id)


def get_all_domains() -> List[RoleFamilyConfig]:
    """List all available domains."""
    return list(DOMAIN_REGISTRY.values())
