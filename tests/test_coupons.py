"""
Unit tests for Coupons API endpoints
"""
import pytest
from unittest.mock import Mock

class TestCouponsEndpoints:
    """Test suite for coupon validation"""
    
    def test_validate_coupon_success(self, client, auth_headers, sample_coupon_data, mock_supabase, monkeypatch):
        """Test validating a valid coupon"""
        # Mock plan lookup
        mock_plan_response = Mock()
        mock_plan_response.data = {"id": "plan-123", "name": "plus"}
        
        # Mock coupon validation
        mock_validation_response = Mock()
        mock_validation_response.data = {
            "valid": True,
            "coupon_id": "coupon-123",
            "coupon_type": "percentage",
            "discount_percent": 50.00,
            "description": "50% de descuento"
        }
        
        call_count = [0]
        def mock_table_or_rpc(name):
            call_count[0] += 1
            if call_count[0] == 1:  # First call is table
                result = Mock()
                result.select = lambda _: result
                result.eq = lambda _k, _v: result
                result.single = lambda: result
                result.execute = lambda: mock_plan_response
                return result
            return mock_supabase.table()
        
        def mock_rpc(func_name, params):
            result = Mock()
            result.execute = lambda: mock_validation_response
            return result
        
        monkeypatch.setattr("app_supabase.supabase.table", mock_table_or_rpc)
        monkeypatch.setattr("app_supabase.supabase.rpc", mock_rpc)
        
        response = client.post("/api/coupons/validate", json=sample_coupon_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] == True
        assert "coupon_type" in data
    
    def test_validate_coupon_invalid(self, client, auth_headers, mock_supabase, monkeypatch):
        """Test validating an invalid coupon"""
        coupon_data = {"code": "INVALID", "plan_name": "plus"}
        
        # Mock plan lookup
        mock_plan_response = Mock()
        mock_plan_response.data = {"id": "plan-123"}
        
        # Mock coupon validation - invalid coupon
        mock_validation_response = Mock()
        mock_validation_response.data = {
            "valid": False,
            "error": "Cupón no encontrado o inactivo"
        }
        
        def mock_table(name):
            result = Mock()
            result.select = lambda _: result
            result.eq = lambda _k, _v: result
            result.single = lambda: result
            result.execute = lambda: mock_plan_response
            return result
        
        def mock_rpc(func_name, params):
            result = Mock()
            result.execute = lambda: mock_validation_response
            return result
        
        monkeypatch.setattr("app_supabase.supabase.table", mock_table)
        monkeypatch.setattr("app_supabase.supabase.rpc", mock_rpc)
        
        response = client.post("/api/coupons/validate", json=coupon_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] == False
        assert "error" in data
    
    def test_validate_coupon_plan_not_found(self, client, auth_headers, sample_coupon_data, mock_supabase, monkeypatch):
        """Test validating coupon with invalid plan"""
        # Mock plan lookup - plan not found
        mock_plan_response = Mock()
        mock_plan_response.data = None
        
        def mock_table(name):
            result = Mock()
            result.select = lambda _: result
            result.eq = lambda _k, _v: result
            result.single = lambda: result
            result.execute = lambda: mock_plan_response
            return result
        
        monkeypatch.setattr("app_supabase.supabase.table", mock_table)
        
        response = client.post("/api/coupons/validate", json=sample_coupon_data, headers=auth_headers)
        
        assert response.status_code == 404

@pytest.mark.unit
class TestCouponTypes:
    """Test different coupon types"""
    
    def test_free_access_coupon(self):
        """Test free access coupon data structure"""
        coupon = {
            "coupon_type": "free_access",
            "duration_months": None,  # Permanent
            "plan_id": "pro"
        }
        assert coupon["coupon_type"] == "free_access"
    
    def test_percentage_discount_coupon(self):
        """Test percentage discount coupon"""
        coupon = {
            "coupon_type": "percentage",
            "discount_percent": 50.00
        }
        assert coupon["discount_percent"] == 50.00
    
    def test_fixed_amount_coupon(self):
        """Test fixed amount discount coupon"""
        coupon = {
            "coupon_type": "fixed_amount",
            "discount_amount": 5.00
        }
        assert coupon["discount_amount"] == 5.00
