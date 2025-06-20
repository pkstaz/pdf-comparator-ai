#!/usr/bin/env python3
"""
PDF Comparator AI - OpenShift Edition
"""

import os
import sys
import argparse
import uvicorn
from src.utils.config import Config, logger

def main():
    parser = argparse.ArgumentParser(
        description="PDF Comparator AI - Sistema inteligente con vLLM"
    )
    
    parser.add_argument(
        "interface",
        choices=["api", "streamlit"],
        default="api",
        nargs="?",
        help="Interfaz a ejecutar (default: api)"
    )
    
    parser.add_argument(
        "--host",
        default=os.getenv("HOST", "0.0.0.0"),
        help="Host para el servidor"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("PORT", "8000")),
        help="Puerto para el servidor"
    )
    
    args = parser.parse_args()
    
    # Validar configuración
    if not Config.validate_config():
        logger.error("Configuración inválida. Revisa las variables de entorno.")
        sys.exit(1)
    
    logger.info(f"""
    ╔══════════════════════════════════════════╗
    ║      🤖 PDF Comparator AI v2.0          ║
    ║        OpenShift + vLLM Edition          ║
    ╚══════════════════════════════════════════╝
    
    🚀 Iniciando: {args.interface}
    📍 Host: {args.host}:{args.port}
    🤖 Modelo: {Config.VLLM_MODEL_NAME}
    """)
    
    try:
        if args.interface == "api":
            from src.interfaces.api_server import app
            uvicorn.run(
                app,
                host=args.host,
                port=args.port,
                log_level=Config.LOG_LEVEL.lower(),
                access_log=True
            )
        elif args.interface == "streamlit":
            import subprocess
            subprocess.run([
                sys.executable, "-m", "streamlit", "run",
                "src/interfaces/streamlit_app.py",
                "--server.address", args.host,
                "--server.port", str(args.port),
                "--server.headless", "true"
            ])
    except KeyboardInterrupt:
        logger.info("Aplicación detenida por el usuario")
    except Exception as e:
        logger.error(f"Error fatal: {str(e)}")
        raise

if __name__ == "__main__":
    main()