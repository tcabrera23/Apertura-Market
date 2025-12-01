"""
Test configuration and fixtures for BullAnalytics
"""
import pytest
import os
from fastapi.testclient import TestClient
from unittest.mock import Mock, MagicMock
from typing import Generator

# Set test environment variables
os.environ["SUPABASE_URL"] = "https://test.supabase.co"
os.environ["SUPABASE_SERVICE_KEY"] = "test-key"
os.environ["SUPABASE_ANON_KEY"] = "test-anon-key"

# Import app after setting env vars
from app_supabase import app, supabase, get_current_user

@pytest.fixture
def client() -> TestClient:
    """FastAPI test client"""
    return TestClient(app)

@pytest.fixture
def mock_user():
    """Mock authenticated user"""
    user = Mock()
    user.id = "test-user-123"
    user.email = "test@example.com"
    return user

@pytest.fixture
def mock_supabase(monkeypatch):
    """Mock Supabase client"""
    mock_client = MagicMock()
    
    # Mock table responses
    mock_table = MagicMock()
    mock_client.table.return_value = mock_table
    mock_table.select.return_value = mock_table
    mock_table.insert.return_value = mock_table
    mock_table.update.return_value = mock_table
    mock_table.delete.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.order.return_value = mock_table
    mock_table.limit.return_value = mock_table
    mock_table.single.return_value = mock_table
    
    # Mock execute
    mock_execute = MagicMock()
    mock_execute.data = []
    mock_table.execute.return_value = mock_execute
    
    # Mock RPC
    mock_client.rpc.return_value = mock_table
    
    return mock_client

@pytest.fixture
def auth_headers(mock_user):
    """Authentication headers for requests"""
    return {"Authorization": "Bearer test-token"}

@pytest.fixture(autouse=True)
def override_get_current_user(mock_user):
    """Override authentication dependency"""
    async def mock_get_current_user():
        return mock_user
    
    app.dependency_overrides[get_current_user] = mock_get_current_user
    yield
    app.dependency_overrides.clear()

@pytest.fixture
def sample_rule_data():
    """Sample rule data for testing"""
    return {
        "name": "Test Alert - NVIDIA below 10%",
        "rule_type": "price_below",
        "ticker": "NVDA",
        "value": 10,
        "email": "test@example.com"
    }

@pytest.fixture
def sample_watchlist_data():
    """Sample watchlist data for testing"""
    return {
        "name": "Tech Stocks",
        "description": "My favorite tech companies"
    }

@pytest.fixture
def sample_asset_data():
    """Sample asset data for testing"""
    return {
        "ticker": "AAPL",
        "asset_name": "Apple Inc."
    }

@pytest.fixture
def sample_coupon_data():
    """Sample coupon data for testing"""
    return {
        "code": "TEST50",
        "plan_name": "plus"
    }
