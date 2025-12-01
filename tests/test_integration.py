"""
Integration tests for BullAnalytics API
Tests complete user workflows and database interactions
"""
import pytest
from unittest.mock import Mock

@pytest.mark.integration
class TestUserWorkflow:
    """Test complete user workflows"""
    
    def test_create_rule_flow(self, client, auth_headers, sample_rule_data, mock_supabase, monkeypatch):
        """
        Integration test: User creates a rule
        Flow: Check limits → Create rule → Verify creation
        """
        # Setup mocks
        mock_limit_check = Mock()
        mock_limit_check.data = True
        
        mock_create_response = Mock()
        mock_create_response.data = [{
            "id": "rule-123",
            **sample_rule_data,
            "is_active": True,
            "created_at": "2025-11-30T20:00:00"
        }]
        
        mock_get_response = Mock()
        mock_get_response.data = mock_create_response.data
        
        call_count = [0]
        def mock_execute():
            call_count[0] += 1
            if call_count[0] == 1:  # First call is create
                return mock_create_response
            return mock_get_response  # Second call is get
        
        def mock_rpc(func_name, params):
            result = Mock()
            result.execute = lambda: mock_limit_check
            return result
        
        monkeypatch.setattr("app_supabase.supabase.table", lambda _: mock_supabase.table())
        monkeypatch.setattr("app_supabase.supabase.rpc", mock_rpc)
        mock_supabase.table().execute.side_effect = mock_execute
        
        # Step 1: Create rule
        create_response = client.post("/api/rules", json=sample_rule_data, headers=auth_headers)
        assert create_response.status_code == 200
        rule_id = create_response.json()["rule"]["id"]
        
        # Step 2: Verify rule was created
        get_response = client.get("/api/rules", headers=auth_headers)
        assert get_response.status_code == 200
        rules = get_response.json()
        assert len(rules) > 0
    
    def test_watchlist_management_flow(self, client, auth_headers, sample_watchlist_data, sample_asset_data, mock_supabase, monkeypatch):
        """
        Integration test: User manages watchlist
        Flow: Create watchlist → Add assets → Get watchlist → Delete watchlist
        """
        watchlist_id = "watchlist-123"
        
        # Mock create watchlist
        mock_create_watchlist = Mock()
        mock_create_watchlist.data = [{
            "id": watchlist_id,
            **sample_watchlist_data
        }]
        
        # Mock verify watchlist
        mock_verify_watchlist = Mock()
        mock_verify_watchlist.data = [{"id": watchlist_id}]
        
        # Mock add asset
        mock_add_asset = Mock()
        mock_add_asset.data = [{
            "id": "asset-1",
            "watchlist_id": watchlist_id,
            **sample_asset_data
        }]
        
        # Mock get watchlist with assets
        mock_get_watchlist = Mock()
        mock_get_watchlist.data = [{
            "id": watchlist_id,
            **sample_watchlist_data,
            "watchlist_assets": [
                {"id": "asset-1", **sample_asset_data}
            ]
        }]
        
        # Mock delete watchlist
        mock_delete_watchlist = Mock()
        mock_delete_watchlist.data = [{"id": watchlist_id}]
        
        call_count = [0]
        def mock_execute():
            call_count[0] += 1
            if call count[0] == 1:  # Create watchlist
                return mock_create_watchlist
            elif call_count[0] == 2:  # Verify watchlist
                return mock_verify_watchlist
            elif call_count[0] == 3:  # Add asset
                return mock_add_asset
            elif call_count[0] == 4:  # Get watchlist
                return mock_get_watchlist
            else:  # Delete watchlist
                return mock_delete_watchlist
        
        monkeypatch.setattr("app_supabase.supabase.table", lambda _: mock_supabase.table())
        mock_supabase.table().execute.side_effect = mock_execute
        
        # Step 1: Create watchlist
        create_response = client.post("/api/watchlists", json=sample_watchlist_data, headers=auth_headers)
        assert create_response.status_code == 200
        
        # Step 2: Add asset to watchlist
        add_asset_response = client.post(
            f"/api/watchlists/{watchlist_id}/assets",
            json=sample_asset_data,
            headers=auth_headers
        )
        assert add_asset_response.status_code == 200
        
        # Step 3: Get watchlist
        get_response = client.get("/api/watchlists", headers=auth_headers)
        assert get_response.status_code == 200
        watchlists = get_response.json()
        assert len(watchlists) > 0
        
        # Step 4: Delete watchlist
        delete_response = client.delete(f"/api/watchlists/{watchlist_id}", headers=auth_headers)
        assert delete_response.status_code == 200

@pytest.mark.integration
class TestAlertWorkflow:
    """Test alert-related workflows"""
    
    def test_view_and_mark_alerts(self, client, auth_headers, mock_supabase, monkeypatch):
        """
        Integration test: User views and marks alerts as read
        """
        alert_id = "alert-123"
        
        # Mock get alerts
        mock_get_alerts = Mock()
        mock_get_alerts.data = [
            {
                "id": alert_id,
                "ticker": "NVDA",
                "message": "NVDA below threshold",
                "is_read": False,
                "created_at": "2025-11-30T20:00:00"
            }
        ]
        
        # Mock mark as read
        mock_mark_read = Mock()
        mock_mark_read.data = [{
            "id": alert_id,
            "is_read": True,
            "read_at": "2025-11-30T20:05:00"
        }]
        
        call_count = [0]
        def mock_execute():
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_get_alerts
            return mock_mark_read
        
        monkeypatch.setattr("app_supabase.supabase.table", lambda _: mock_supabase.table())
        mock_supabase.table().execute.side_effect = mock_execute
        
        # Step 1: Get alerts
        get_response = client.get("/api/alerts", headers=auth_headers)
        assert get_response.status_code == 200
        alerts = get_response.json()
        assert len(alerts) > 0
        assert alerts[0]["is_read"] == False
        
        # Step 2: Mark alert as read
        mark_response = client.patch(f"/api/alerts/{alert_id}/read", headers=auth_headers)
        assert mark_response.status_code == 200

@pytest.mark.integration
class TestHealthCheck:
    """Test system health endpoints"""
    
    def test_health_check_healthy(self, client, mock_supabase, monkeypatch):
        """Test health check when system is healthy"""
        mock_response = Mock()
        mock_response.data = [{"count": 3}]
        
        monkeypatch.setattr("app_supabase.supabase.table", lambda _: mock_supabase.table())
        mock_supabase.table().execute.return_value = mock_response
        
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
        assert "timestamp" in data
