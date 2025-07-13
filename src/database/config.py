"""Database configuration using Pydantic settings."""

from pathlib import Path
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseConfig(BaseSettings):
    """Database configuration settings."""
    
    # Database connection settings
    db_url: str = Field(
        default="sqlite:///./loans.db",
        description="Database URL. Use sqlite:/// for SQLite, postgresql:// for PostgreSQL"
    )
    
    # Database connection pool settings
    pool_size: int = Field(default=5, description="Database connection pool size")
    max_overflow: int = Field(default=10, description="Maximum connections beyond pool size")
    pool_timeout: int = Field(default=30, description="Timeout for getting connection from pool")
    pool_recycle: int = Field(default=3600, description="Time in seconds to recycle connections")
    
    # Database behavior settings
    echo: bool = Field(default=False, description="Enable SQLAlchemy query logging")
    create_tables: bool = Field(default=True, description="Create tables automatically on startup")
    
    # Backup and maintenance settings
    backup_enabled: bool = Field(default=True, description="Enable automatic database backups")
    backup_interval_hours: int = Field(default=24, description="Backup interval in hours")
    backup_retention_days: int = Field(default=7, description="Number of backup days to retain")
    
    @field_validator('db_url')
    @classmethod
    def validate_db_url(cls, v: str) -> str:
        """Validate database URL format."""
        if not v:
            raise ValueError("Database URL cannot be empty")
        
        # Ensure SQLite database directory exists
        if v.startswith("sqlite:///"):
            db_path = Path(v.replace("sqlite:///", ""))
            db_path.parent.mkdir(parents=True, exist_ok=True)
        
        return v
    
    @field_validator('pool_size')
    @classmethod
    def validate_pool_size(cls, v: int) -> int:
        """Validate pool size."""
        if v < 1:
            raise ValueError("Pool size must be at least 1")
        return v
    
    @field_validator('backup_interval_hours')
    @classmethod
    def validate_backup_interval(cls, v: int) -> int:
        """Validate backup interval."""
        if v < 1:
            raise ValueError("Backup interval must be at least 1 hour")
        return v
    
    @field_validator('backup_retention_days')
    @classmethod
    def validate_backup_retention(cls, v: int) -> int:
        """Validate backup retention."""
        if v < 1:
            raise ValueError("Backup retention must be at least 1 day")
        return v
    
    def get_database_path(self) -> Path:
        """Get the database file path for SQLite databases."""
        if self.db_url.startswith("sqlite:///"):
            return Path(self.db_url.replace("sqlite:///", ""))
        raise ValueError("Database path is only available for SQLite databases")
    
    def is_sqlite(self) -> bool:
        """Check if the database is SQLite."""
        return self.db_url.startswith("sqlite:")
    
    def is_postgresql(self) -> bool:
        """Check if the database is PostgreSQL."""
        return self.db_url.startswith("postgresql:")

    model_config = SettingsConfigDict(
        env_prefix="LOAN_DB_",
        case_sensitive=False,
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    ) 