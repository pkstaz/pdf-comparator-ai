import os
from typing import Dict, Any, Optional
from pydantic import BaseSettings, Field, validator
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    """Configuración de la aplicación usando Pydantic"""
    
    # App Settings
    app_name: str = Field("pdf-comparator-ai", env="APP_NAME")
    app_env: str = Field("development", env="APP_ENV")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    
    # vLLM Configuration
    vllm_endpoint: str = Field("http://vllm-service:8000", env="VLLM_ENDPOINT")
    vllm_model_name: str = Field("granite-3.1-8b-instruct", env="VLLM_MODEL_NAME")
    vllm_api_key: str = Field("EMPTY", env="VLLM_API_KEY")
    vllm_max_tokens: int = Field(2048, env="VLLM_MAX_TOKENS")
    vllm_temperature: float = Field(0.3, env="VLLM_TEMPERATURE")
    vllm_top_p: float = Field(0.95, env="VLLM_TOP_P")
    vllm_frequency_penalty: float = Field(0.0, env="VLLM_FREQUENCY_PENALTY")
    vllm_presence_penalty: float = Field(0.0, env="VLLM_PRESENCE_PENALTY")
    
    # Redis Configuration
    redis_host: str = Field("redis-service", env="REDIS_HOST")
    redis_port: int = Field(6379, env="REDIS_PORT")
    redis_password: Optional[str] = Field(None, env="REDIS_PASSWORD")
    redis_db: int = Field(0, env="REDIS_DB")
    redis_decode_responses: bool = Field(True, env="REDIS_DECODE_RESPONSES")
    
    # MinIO Configuration
    minio_endpoint: str = Field("minio-service:9000", env="MINIO_ENDPOINT")
    minio_access_key: str = Field("minioadmin", env="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field("minioadmin", env="MINIO_SECRET_KEY")
    minio_bucket_name: str = Field("pdf-documents", env="MINIO_BUCKET_NAME")
    minio_secure: bool = Field(False, env="MINIO_SECURE")
    
    # Analysis Settings
    max_pdf_size_mb: int = Field(50, env="MAX_PDF_SIZE_MB")
    default_chunk_size: int = Field(1000, env="DEFAULT_CHUNK_SIZE")
    chunk_overlap: int = Field(200, env="CHUNK_OVERLAP")
    similarity_threshold: float = Field(0.7, env="SIMILARITY_THRESHOLD")
    max_analysis_time_seconds: int = Field(300, env="MAX_ANALYSIS_TIME_SECONDS")
    supported_languages: list = Field(["es", "en", "pt"], env="SUPPORTED_LANGUAGES")
    
    # Feature Flags
    enable_caching: bool = Field(True, env="ENABLE_CACHING")
    enable_metrics: bool = Field(True, env="ENABLE_METRICS")
    enable_tracing: bool = Field(True, env="ENABLE_TRACING")
    enable_semantic_analysis: bool = Field(True, env="ENABLE_SEMANTIC_ANALYSIS")
    enable_structural_analysis: bool = Field(True, env="ENABLE_STRUCTURAL_ANALYSIS")
    
    # Monitoring
    metrics_port: int = Field(9090, env="METRICS_PORT")
    
    # Paths
    temp_dir: str = Field("/app/temp", env="TEMP_DIR")
    cache_dir: str = Field("/app/cache", env="CACHE_DIR")
    
    # Server Configuration
    host: str = Field("0.0.0.0", env="HOST")
    port: int = Field(8000, env="PORT")
    workers: int = Field(1, env="WORKERS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @validator("supported_languages", pre=True)
    def parse_languages(cls, v):
        if isinstance(v, str):
            return False

@lru_cache()
def get_settings() -> Settings:
    """Obtiene la configuración (cached)"""
    return Settings()

# Configuración de logging
def setup_logging(settings: Settings):
    """Configura el sistema de logging"""
    import logging.config
    
    LOGGING_CONFIG = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "json": {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": "%(asctime)s %(name)s %(levelname)s %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": settings.log_level,
                "formatter": "default" if settings.is_development else "json",
                "stream": "ext://sys.stdout"
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": settings.log_level,
                "formatter": "json",
                "filename": f"{settings.cache_dir}/app.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5
            }
        },
        "loggers": {
            "": {
                "level": settings.log_level,
                "handlers": ["console", "file"] if settings.is_production else ["console"]
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            }
        }
    }
    
    logging.config.dictConfig(LOGGING_CONFIG)
    logger.info(f"Logging configured with level: {settings.log_level}")

# Alias para compatibilidad
Config = get_settings() v.split(",")
        return v
    
    @validator("log_level")
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}")
        return v.upper()
    
    @property
    def redis_url(self) -> str:
        """Construye la URL de Redis"""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    @property
    def is_production(self) -> bool:
        """Verifica si está en producción"""
        return self.app_env.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Verifica si está en desarrollo"""
        return self.app_env.lower() == "development"
    
    def get_langchain_config(self) -> Dict[str, Any]:
        """Configuración para LangChain"""
        return {
            "llm": {
                "endpoint": self.vllm_endpoint,
                "model_name": self.vllm_model_name,
                "api_key": self.vllm_api_key,
                "temperature": self.vllm_temperature,
                "max_tokens": self.vllm_max_tokens,
                "top_p": self.vllm_top_p,
                "frequency_penalty": self.vllm_frequency_penalty,
                "presence_penalty": self.vllm_presence_penalty,
            },
            "embeddings": {
                "model_name": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                "cache_folder": self.cache_dir,
            },
            "text_splitter": {
                "chunk_size": self.default_chunk_size,
                "chunk_overlap": self.chunk_overlap,
            }
        }
    
    def validate_config(self) -> bool:
        """Valida la configuración esencial"""
        try:
            # Verificar conexión a vLLM
            if self.is_production:
                import httpx
                response = httpx.get(f"{self.vllm_endpoint}/health", timeout=5.0)
                if response.status_code != 200:
                    logger.error(f"vLLM health check failed: {response.status_code}")
                    return False
            
            # Verificar directorios
            for directory in [self.temp_dir, self.cache_dir]:
                os.makedirs(directory, exist_ok=True)
            
            logger.info("Configuration validated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return