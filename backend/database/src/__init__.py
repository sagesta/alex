"""
Database package for Alex Financial Planner
Provides database models, schemas, and Data API client
"""

from .client import DataAPIClient, get_database_client
from .litellm_model_factory import create_litellm_model
from .models import Database
from .schemas import (
    # Types
    RegionType,
    AssetClassType,
    SectorType,
    InstrumentType,
    JobType,
    JobStatus,
    AccountType,
    
    # Create schemas (for inputs)
    InstrumentCreate,
    UserCreate,
    AccountCreate,
    PositionCreate,
    JobCreate,
    JobUpdate,
    
    # Response schemas (for outputs)
    InstrumentResponse,
    PortfolioAnalysis,
    RebalanceRecommendation,
)

__all__ = [
    'Database',
    'DataAPIClient',
    'get_database_client',
    'create_litellm_model',
    'InstrumentCreate',
    'UserCreate',
    'AccountCreate',
    'PositionCreate',
    'JobCreate',
    'JobUpdate',
    'InstrumentResponse',
    'PortfolioAnalysis',
    'RebalanceRecommendation',
    'RegionType',
    'AssetClassType',
    'SectorType',
    'InstrumentType',
    'JobType',
    'JobStatus',
    'AccountType',
]