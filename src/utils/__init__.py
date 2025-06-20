"""
Utility functions and helpers
"""

from .config import Config, get_settings, setup_logging
from .report_generator import ReportGenerator

__all__ = [
    "Config",
    "get_settings",
    "setup_logging",
    "ReportGenerator",
]

# Utility functions that might be used across modules
def get_project_root():
    """Get the project root directory"""
    from pathlib import Path
    return Path(__file__).parent.parent.parent

def ensure_directories():
    """Ensure all required directories exist"""
    import os
    from .config import get_settings
    
    settings = get_settings()
    directories = [
        settings.temp_dir,
        settings.cache_dir,
        os.path.join(settings.cache_dir, "models"),
        os.path.join(settings.cache_dir, "embeddings"),
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)