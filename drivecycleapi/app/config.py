"""Postgres API configuration."""

import os
from pydantic_settings import BaseSettings
from urllib.parse import quote


class Settings(BaseSettings):
    """Postgres-specific API settings."""

    postgres_user: str = os.getenv('POSTGRES_USER')
    postgres_pass: str = os.getenv('POSTGRES_PASSWORD')
    postgres_host_reader: str = os.getenv('POSTGRES_HOST')
    postgres_host_writer: str = os.getenv('POSTGRES_HOST')
    postgres_port: str = os.getenv('POSTGRES_PORT')
    postgres_dbname: str = os.getenv('POSTGRES_DB')

    db_min_conn_size: int = 10
    db_max_conn_size: int = 10
    db_max_queries: int = 50000
    db_max_inactive_conn_lifetime: float = 300

    @property
    def reader_connection_string(self):
        """Create reader psql connection string."""
        return f"postgresql://{self.postgres_user}:{quote(self.postgres_pass)}@{self.postgres_host_reader}:{self.postgres_port}/{self.postgres_dbname}"

    @property
    def writer_connection_string(self):
        """Create writer psql connection string."""
        return f"postgresql://{self.postgres_user}:{quote(self.postgres_pass)}@{self.postgres_host_writer}:{self.postgres_port}/{self.postgres_dbname}"
