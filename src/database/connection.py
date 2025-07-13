"""Database connection management using SQLAlchemy."""

import logging
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine, Engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from .config import DatabaseConfig
from ..models.base import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manages database connections and sessions.
    
    Provides a centralized way to manage database connections with proper
    connection pooling and session management.
    """
    
    def __init__(self, config: DatabaseConfig):
        """
        Initialize the database manager.
        
        Args:
            config: Database configuration object
        """
        self.config = config
        self.engine: Optional[Engine] = None
        self.SessionLocal: Optional[sessionmaker] = None
        self._initialize_database()
    
    def _initialize_database(self) -> None:
        """Initialize database engine and session factory."""
        try:
            # Create engine with appropriate settings
            engine_kwargs = {
                'echo': self.config.echo,
                'pool_pre_ping': True,  # Verify connections before use
            }
            
            if self.config.is_sqlite():
                # SQLite-specific settings
                engine_kwargs.update({
                    'connect_args': {'check_same_thread': False},
                    'poolclass': StaticPool,
                })
            else:
                # PostgreSQL and other databases
                engine_kwargs.update({
                    'pool_size': self.config.pool_size,
                    'max_overflow': self.config.max_overflow,
                    'pool_timeout': self.config.pool_timeout,
                    'pool_recycle': self.config.pool_recycle,
                })
            
            self.engine = create_engine(self.config.db_url, **engine_kwargs)
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            # Create tables if configured to do so
            if self.config.create_tables:
                self.create_tables()
                
            logger.info(f"Database initialized successfully: {self.config.db_url}")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def create_tables(self) -> None:
        """Create all database tables."""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise
    
    def drop_tables(self) -> None:
        """Drop all database tables. Use with caution!"""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.warning("Database tables dropped successfully")
        except Exception as e:
            logger.error(f"Failed to drop database tables: {e}")
            raise
    
    def get_session(self) -> Session:
        """
        Get a new database session.
        
        Returns:
            SQLAlchemy session instance
        """
        if not self.SessionLocal:
            raise RuntimeError("Database not initialized")
        return self.SessionLocal()
    
    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """
        Provide a transactional scope around a series of operations.
        
        This is a context manager that provides a database session and
        automatically commits the transaction on success or rolls back on error.
        
        Yields:
            SQLAlchemy session instance
        """
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database transaction failed: {e}")
            raise
        finally:
            session.close()
    
    def health_check(self) -> bool:
        """
        Check if the database connection is healthy.
        
        Returns:
            True if database is accessible, False otherwise
        """
        try:
            with self.session_scope() as session:
                session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    def close(self) -> None:
        """Close the database engine and all connections."""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connections closed")


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def init_database(config: DatabaseConfig) -> DatabaseManager:
    """
    Initialize the global database manager.
    
    Args:
        config: Database configuration object
        
    Returns:
        Database manager instance
    """
    global _db_manager
    _db_manager = DatabaseManager(config)
    return _db_manager


def get_database_manager() -> DatabaseManager:
    """
    Get the global database manager instance.
    
    Returns:
        Database manager instance
        
    Raises:
        RuntimeError: If database manager has not been initialized
    """
    if _db_manager is None:
        raise RuntimeError("Database manager not initialized. Call init_database() first.")
    return _db_manager


def get_db_session() -> Session:
    """
    Get a new database session from the global database manager.
    
    Returns:
        SQLAlchemy session instance
    """
    return get_database_manager().get_session()


@contextmanager
def db_session_scope() -> Generator[Session, None, None]:
    """
    Get a transactional database session scope.
    
    Yields:
        SQLAlchemy session instance
    """
    with get_database_manager().session_scope() as session:
        yield session 