"""
User interfaces for PDF Comparator AI
"""

# Import interface components when needed
# Avoid importing heavy dependencies at module level
__all__ = [
    "api_server",
    "streamlit_app",
    "gradio_app",
]

# Interface metadata
INTERFACES = {
    "api": {
        "name": "FastAPI REST API",
        "module": "api_server",
        "default_port": 8000,
    },
    "streamlit": {
        "name": "Streamlit Web UI",
        "module": "streamlit_app",
        "default_port": 8501,
    },
    "gradio": {
        "name": "Gradio Interface",
        "module": "gradio_app",
        "default_port": 7860,
    },
}

def get_interface(name: str):
    """
    Dynamically import and return the specified interface
    
    Args:
        name: Interface name (api, streamlit, gradio)
        
    Returns:
        Module object for the interface
    """
    if name not in INTERFACES:
        raise ValueError(f"Unknown interface: {name}")
    
    if name == "api":
        from . import api_server
        return api_server
    elif name == "streamlit":
        from . import streamlit_app
        return streamlit_app
    elif name == "gradio":
        from . import gradio_app
        return gradio_app