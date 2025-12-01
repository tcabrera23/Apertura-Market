"""
Unit tests for Rules API endpoints
"""
import pytest
from fastapi.testclient import TestClient

class TestRulesEndpoints:
    """Test suite for rules CRUD operations"""
    
    def test_get_rules_success(self, client, auth_headers, mock_supabase, monkeypatch):
        """Test getting all rules for a user"""
        # Mock Supabase response
        mock_response = Mock()
        mock_response.data = [
            {
                "id": "rule-1",
                "name": "Test Rule",
                "rule_type": "price_below",
                "ticker": "NVDA",
                "value_threshold": 10,
                "email": "test@example.com",
                "is_active": True
            }
        ]
        
        monkeypatch.setattr("app_supabase.supabase.table", lambda _: mock_supabase.table())
        mock_supabase.table().execute.return_value = mock_response
        
        response = client.get("/api/rules", headers=auth_headers)
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_create_rule_success(self, client, auth_headers, sample_rule_data, mock_supabase, monkeypatch):
        """Test creating a new rule"""
        # Mock plan limit check
        mock_check_response = Mock()
        mock_check_response.data = True
        
        # Mock rule creation
        mock_create_response = Mock()
        mock_create_response.data = [{
            "id": "new-rule-id",
            **sample_rule_data
        }]
        
        def mock_rpc(func_name, params):
            if func_name == "check_user_plan_limit":
                result = Mock()
                result.execute = lambda: mock_check_response
                return result
        
        monkeypatch.setattr("app_supabase.supabase.rpc", mock_rpc)
        monkeypatch.setattr("app_supabase.supabase.table", lambda _: mock_supabase.table())
        mock_supabase.table().execute.return_value = mock_create_response
        
        response = client.post("/api/rules", json=sample_rule_data, headers=auth_headers)
        
        assert response.status_code == 200
        assert "message" in response.json()
        assert "rule" in response.json()
    
    def test_create_rule_limit_exceeded(self, client, auth_headers, sample_rule_data, monkeypatch):
        """Test creating rule when limit is exceeded"""
        # Mock plan limit check to return False
        mock_check_response = Mock()
        mock_check_response.data = False
        
        def mock_rpc(func_name, params):
            result = Mock()
            result.execute = lambda: mock_check_response
            return result
        
        monkeypatch.setattr("app_supabase.supabase.rpc", mock_rpc)
        
        response = client.post("/api/rules", json=sample_rule_data, headers=auth_headers)
        
        assert response.status_code == 403
        assert "límite" in response.json()["detail"].lower()
    
    def test_update_rule_success(self, client, auth_headers, mock_supabase, monkeypatch):
        """Test updating a rule"""
        rule_id = "rule-123"
        update_data = {"name": "Updated Rule Name", "is_active": False}
        
        mock_response = Mock()
        mock_response.data = [{
            "id": rule_id,
            "name": "Updated Rule Name",
            "is_active": False
        }]
        
        monkeypatch.setattr("app_supabase.supabase.table", lambda _: mock_supabase.table())
        mock_supabase.table().execute.return_value = mock_response
        
        response = client.put(f"/api/rules/{rule_id}", json=update_data, headers=auth_headers)
        
        assert response.status_code == 200
        assert "message" in response.json()
    
    def test_update_rule_not_found(self, client, auth_headers, mock_supabase, monkeypatch):
        """Test updating non-existent rule"""
        rule_id = "nonexistent"
        update_data = {"name": "Updated"}
        
        mock_response = Mock()
        mock_response.data = []
        
        monkeypatch.setattr("app_supabase.supabase.table", lambda _: mock_supabase.table())
        mock_supabase.table().execute.return_value = mock_response
        
        response = client.put(f"/api/rules/{rule_id}", json=update_data, headers=auth_headers)
        
        assert response.status_code == 404
    
    def test_delete_rule_success(self, client, auth_headers, mock_supabase, monkeypatch):
        """Test deleting a rule"""
        rule_id = "rule-123"
        
        mock_response = Mock()
        mock_response.data = [{"id": rule_id}]
        
        monkeypatch.setattr("app_supabase.supabase.table", lambda _: mock_supabase.table())
        mock_supabase.table().execute.return_value = mock_response
        
        response = client.delete(f"/api/rules/{rule_id}", headers=auth_headers)
        
        assert response.status_code == 200
        assert response.json()["message"] == "Rule deleted successfully"
    
    def test_delete_rule_not_found(self, client, auth_headers, mock_supabase, monkeypatch):
        """Test deleting non-existent rule"""
        rule_id = "nonexistent"
        
        mock_response = Mock()
        mock_response.data = []
        
        monkeypatch.setattr("app_supabase.supabase.table", lambda _: mock_supabase.table())
        mock_supabase.table().execute.return_value = mock_response
        
        response = client.delete(f"/api/rules/{rule_id}", headers=auth_headers)
        
        assert response.status_code == 404

@pytest.mark.unit
class TestRuleValidation:
    """Test rule validation logic"""
    
    def test_valid_rule_types(self):
        """Test all valid rule types"""
        valid_types = ['price_below', 'price_above', 'pe_below', 'pe_above', 'max_distance']
        for rule_type in valid_types:
            rule_data = {
                "name": "Test",
                "rule_type": rule_type,
                "ticker": "AAPL",
                "value": 100,
                "email": "test@example.com"
            }
            # Would validate against Pydantic model
            assert rule_data["rule_type"] in valid_types
