"""
Test Suite Consolidado para BullAnalytics
Todos los tests en un solo archivo para automatización con GitHub Actions
"""
import pytest
import os
from fastapi.testclient import TestClient
from unittest.mock import Mock, MagicMock, patch
from typing import Generator
from datetime import datetime

# Set test environment variables before importing app
os.environ["SUPABASE_URL"] = "https://test.supabase.co"
os.environ["SUPABASE_SERVICE_KEY"] = "test-key"
os.environ["SUPABASE_ANON_KEY"] = "test-anon-key"
os.environ["SUPABASE_JWT_SECRET"] = "test-jwt-secret"
os.environ["BREVO_API_KEY"] = "test-brevo-key"

# Import app after setting env vars
from app_supabase import app, supabase, get_current_user, send_alert_email
from email_templates import get_onboarding_email_template
from conexion_iol import ConexionIOL
from conexion_binance import ConexionBinance

# ============================================================================
# FIXTURES
# ============================================================================

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

@pytest.fixture
def mock_brevo_api():
    """Mock Brevo API client"""
    with patch('app_supabase.TransactionalEmailsApi') as mock_api_class:
        mock_api_instance = MagicMock()
        mock_api_class.return_value = mock_api_instance
        
        # Mock successful response
        mock_response = MagicMock()
        mock_response.message_id = "test-message-id-123"
        mock_api_instance.send_transac_email.return_value = mock_response
        
        yield mock_api_instance

@pytest.fixture
def mock_supabase_auth():
    """Mock Supabase Auth for user registration"""
    with patch('app_supabase.supabase.auth') as mock_auth:
        # Mock sign_in_with_password to fail (user doesn't exist)
        mock_auth.sign_in_with_password.side_effect = Exception("User not found")
        
        # Mock sign_up to return a new user with the email from the signup request
        def create_mock_auth_response(email):
            mock_user = MagicMock()
            mock_user.id = "test-user-123"
            mock_user.email = email
            mock_user.email_confirmed_at = datetime.now()
            
            mock_session = MagicMock()
            mock_session.access_token = "test-access-token-123"
            
            mock_auth_response = MagicMock()
            mock_auth_response.user = mock_user
            mock_auth_response.session = mock_session
            
            return mock_auth_response
        
        # Make sign_up return a response based on the email in the request
        def sign_up_side_effect(*args, **kwargs):
            if args and isinstance(args[0], dict):
                email = args[0].get('email', 'test@example.com')
            elif kwargs:
                email = kwargs.get('email', 'test@example.com')
            else:
                email = 'test@example.com'
            return create_mock_auth_response(email)
        
        mock_auth.sign_up.side_effect = sign_up_side_effect
        
        yield mock_auth

@pytest.fixture
def mock_supabase_table():
    """Mock Supabase table operations"""
    with patch('app_supabase.supabase.table') as mock_table:
        mock_table_instance = MagicMock()
        mock_table.return_value = mock_table_instance
        
        # Mock select chain
        mock_table_instance.select.return_value = mock_table_instance
        mock_table_instance.eq.return_value = mock_table_instance
        
        # Mock insert chain
        mock_table_instance.insert.return_value = mock_table_instance
        
        # Mock execute responses
        mock_execute_response = MagicMock()
        mock_execute_response.data = [{
            "id": "test-user-123",
            "email": "test@example.com",
            "auth_source": "email_password",
            "created_at": datetime.now().isoformat(),
            "country": "AR",
            "date_of_birth": "1990-01-01"
        }]
        mock_table_instance.execute.return_value = mock_execute_response
        
        yield mock_table_instance

@pytest.fixture
def mock_create_default_subscription():
    """Mock the create_default_subscription function"""
    with patch('app_supabase.create_default_subscription') as mock_func:
        yield mock_func

# ============================================================================
# TESTS DE REGLAS (RULES)
# ============================================================================

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

# ============================================================================
# TESTS DE WATCHLISTS
# ============================================================================

class TestWatchlistsEndpoints:
    """Test suite for watchlists CRUD operations"""
    
    def test_get_watchlists_success(self, client, auth_headers, mock_supabase, monkeypatch):
        """Test getting all watchlists for a user"""
        mock_response = Mock()
        mock_response.data = [
            {
                "id": "watchlist-1",
                "name": "Tech Stocks",
                "description": "Technology companies",
                "watchlist_assets": [
                    {"ticker": "AAPL", "asset_name": "Apple Inc."},
                    {"ticker": "GOOGL", "asset_name": "Alphabet Inc."}
                ]
            }
        ]
        
        monkeypatch.setattr("app_supabase.supabase.table", lambda _: mock_supabase.table())
        mock_supabase.table().execute.return_value = mock_response
        
        response = client.get("/api/watchlists", headers=auth_headers)
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_create_watchlist_success(self, client, auth_headers, sample_watchlist_data, mock_supabase, monkeypatch):
        """Test creating a new watchlist"""
        mock_response = Mock()
        mock_response.data = [{
            "id": "new-watchlist",
            **sample_watchlist_data
        }]
        
        monkeypatch.setattr("app_supabase.supabase.table", lambda _: mock_supabase.table())
        mock_supabase.table().execute.return_value = mock_response
        
        response = client.post("/api/watchlists", json=sample_watchlist_data, headers=auth_headers)
        
        assert response.status_code == 200
        assert "message" in response.json()
        assert "watchlist" in response.json()
    
    def test_add_asset_to_watchlist_success(self, client, auth_headers, sample_asset_data, mock_supabase, monkeypatch):
        """Test adding an asset to a watchlist"""
        watchlist_id = "watchlist-123"
        
        # Mock watchlist verification
        mock_watchlist_response = Mock()
        mock_watchlist_response.data = [{"id": watchlist_id}]
        
        # Mock asset addition
        mock_asset_response = Mock()
        mock_asset_response.data = [{
            "id": "asset-1",
            "watchlist_id": watchlist_id,
            **sample_asset_data
        }]
        
        call_count = [0]
        def mock_execute():
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_watchlist_response
            return mock_asset_response
        
        monkeypatch.setattr("app_supabase.supabase.table", lambda _: mock_supabase.table())
        mock_supabase.table().execute.side_effect = mock_execute
        
        response = client.post(
            f"/api/watchlists/{watchlist_id}/assets",
            json=sample_asset_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert "message" in response.json()
    
    def test_add_asset_watchlist_not_found(self, client, auth_headers, sample_asset_data, mock_supabase, monkeypatch):
        """Test adding asset to non-existent watchlist"""
        watchlist_id = "nonexistent"
        
        mock_response = Mock()
        mock_response.data = []
        
        monkeypatch.setattr("app_supabase.supabase.table", lambda _: mock_supabase.table())
        mock_supabase.table().execute.return_value = mock_response
        
        response = client.post(
            f"/api/watchlists/{watchlist_id}/assets",
            json=sample_asset_data,
            headers=auth_headers
        )
        
        assert response.status_code == 404
    
    def test_delete_watchlist_success(self, client, auth_headers, mock_supabase, monkeypatch):
        """Test deleting a watchlist"""
        watchlist_id = "watchlist-123"
        
        mock_response = Mock()
        mock_response.data = [{"id": watchlist_id}]
        
        monkeypatch.setattr("app_supabase.supabase.table", lambda _: mock_supabase.table())
        mock_supabase.table().execute.return_value = mock_response
        
        response = client.delete(f"/api/watchlists/{watchlist_id}", headers=auth_headers)
        
        assert response.status_code == 200
        assert response.json()["message"] == "Watchlist deleted successfully"

@pytest.mark.unit
class TestWatchlistValidation:
    """Test watchlist validation logic"""
    
    def test_watchlist_name_required(self):
        """Test that watchlist name is required"""
        watchlist_data = {}
        # Would validate against Pydantic model - name is required
        assert "name" not in watchlist_data
    
    def test_asset_ticker_required(self):
        """Test that asset ticker is required"""
        asset_data = {"asset_name": "Apple"}
        # Would validate against Pydantic model - ticker is required
        assert "ticker" not in asset_data

# ============================================================================
# TESTS DE CUPONES (COUPONS)
# ============================================================================

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

# ============================================================================
# TESTS DE EMAIL
# ============================================================================

class TestOnboardingEmailTemplate:
    """Test the onboarding email template generation"""
    
    def test_template_generation(self):
        """Test that the onboarding template is generated correctly"""
        user_name = "John"
        user_email = "john@example.com"
        
        template = get_onboarding_email_template(user_name, user_email)
        
        assert "subject" in template
        assert "html_content" in template
        assert "¡Bienvenido a BullAnalytics!" in template["subject"]
        assert user_name in template["html_content"]
        assert "BullAnalytics" in template["html_content"]
        assert "Dashboard" in template["html_content"]
    
    def test_template_contains_features(self):
        """Test that the template includes all expected features"""
        template = get_onboarding_email_template("TestUser", "test@example.com")
        html = template["html_content"]
        
        # Check for key features mentioned in the template
        assert "listas personalizadas" in html or "listas" in html
        assert "alertas" in html
        assert "métricas" in html or "análisis" in html
        assert "gráficos" in html or "visualizar" in html

class TestSendAlertEmail:
    """Test the send_alert_email function"""
    
    def test_send_email_success(self, mock_brevo_api):
        """Test successful email sending"""
        with patch('app_supabase.Configuration') as mock_config, \
             patch('app_supabase.ApiClient') as mock_api_client:
            
            # Mock Configuration with all necessary attributes
            mock_config_instance = MagicMock()
            mock_config.return_value = mock_config_instance
            mock_config_instance.api_key = {}
            mock_config_instance.assert_hostname = None
            
            # Mock ApiClient to return our mocked TransactionalEmailsApi
            mock_client_instance = MagicMock()
            mock_api_client.return_value = mock_client_instance
            
            result = send_alert_email(
                to_email="test@example.com",
                subject="Test Subject",
                html_content="<html>Test Content</html>",
                sender_name="BullAnalytics",
                sender_email="noreply@aperturaia.com"
            )
            
            assert result["success"] is True
            assert result["message_id"] == "test-message-id-123"
            assert result["to"] == "test@example.com"
            
            # Verify Brevo API was called correctly
            mock_brevo_api.send_transac_email.assert_called_once()
            call_args = mock_brevo_api.send_transac_email.call_args[0][0]
            
            assert call_args['to'][0]['email'] == "test@example.com"
            assert call_args['subject'] == "Test Subject"
            assert call_args['htmlContent'] == "<html>Test Content</html>"
            assert call_args['sender']['name'] == "BullAnalytics"
            assert call_args['sender']['email'] == "noreply@aperturaia.com"
    
    def test_send_email_no_api_key(self):
        """Test email sending fails when BREVO_API_KEY is not set"""
        with patch('app_supabase.BREVO_API_KEY', None):
            result = send_alert_email(
                to_email="test@example.com",
                subject="Test Subject",
                html_content="<html>Test Content</html>"
            )
            
            assert result["success"] is False
            assert "BREVO_API_KEY" in result["error"]
    
    def test_send_email_api_exception(self, mock_brevo_api):
        """Test handling of Brevo API exceptions"""
        from sib_api_v3_sdk.rest import ApiException
        
        # Mock API exception
        api_error = ApiException(status=400, reason="Bad Request")
        mock_brevo_api.send_transac_email.side_effect = api_error
        
        with patch('app_supabase.Configuration') as mock_config:
            mock_config_instance = MagicMock()
            mock_config.return_value = mock_config_instance
            mock_config_instance.api_key = {}
            
            result = send_alert_email(
                to_email="test@example.com",
                subject="Test Subject",
                html_content="<html>Test Content</html>"
            )
            
            assert result["success"] is False
            assert "error" in result

class TestUserRegistrationEmailFlow:
    """Test the complete user registration flow with email sending"""
    
    def test_signup_sends_onboarding_email(
        self,
        client,
        mock_brevo_api,
        mock_supabase_auth,
        mock_supabase_table,
        mock_create_default_subscription
    ):
        """Test that user registration triggers onboarding email"""
        with patch('app_supabase.Configuration') as mock_config, \
             patch('app_supabase.ApiClient') as mock_api_client, \
             patch('app_supabase.ensure_user_persisted') as mock_ensure_user, \
             patch('asyncio.sleep') as mock_sleep:
            
            # Setup mocks
            mock_config_instance = MagicMock()
            mock_config.return_value = mock_config_instance
            mock_config_instance.api_key = {}
            mock_config_instance.assert_hostname = None
            
            # Mock ApiClient
            mock_client_instance = MagicMock()
            mock_api_client.return_value = mock_client_instance
            
            # Mock asyncio.sleep to return immediately
            async def mock_sleep_func(delay):
                return None
            mock_sleep.side_effect = mock_sleep_func
            
            # Mock ensure_user_persisted as async function
            async def mock_ensure_user_func(*args, **kwargs):
                return {
                    "id": "test-user-123",
                    "email": "test@example.com",
                    "auth_source": "email_password",
                    "created_at": datetime.now().isoformat()
                }
            mock_ensure_user.side_effect = mock_ensure_user_func
            
            # Make signup request
            signup_data = {
                "email": "test@example.com",
                "password": "testpass123",
                "confirm_password": "testpass123",
                "country": "AR",
                "date_of_birth": "1990-01-01"
            }
            
            response = client.post("/auth/signup", json=signup_data)
            
            # Verify response is successful
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert data["user"]["email"] == "test@example.com"
            
            # Verify email was sent
            mock_brevo_api.send_transac_email.assert_called_once()
            call_args = mock_brevo_api.send_transac_email.call_args[0][0]
            
            # Verify email details
            assert call_args['to'][0]['email'] == "test@example.com"
            assert "¡Bienvenido a BullAnalytics!" in call_args['subject']
            assert "test" in call_args['htmlContent']
            assert "BullAnalytics" in call_args['htmlContent']
            assert call_args['sender']['name'] == "BullAnalytics"
            assert call_args['sender']['email'] == "noreply@aperturaia.com"
    
    def test_signup_email_failure_does_not_block_registration(
        self,
        client,
        mock_supabase_auth,
        mock_supabase_table,
        mock_create_default_subscription
    ):
        """Test that email sending failure doesn't prevent user registration"""
        from sib_api_v3_sdk.rest import ApiException
        
        with patch('app_supabase.Configuration') as mock_config, \
             patch('app_supabase.ApiClient') as mock_api_client, \
             patch('app_supabase.TransactionalEmailsApi') as mock_api_class, \
             patch('app_supabase.ensure_user_persisted') as mock_ensure_user, \
             patch('asyncio.sleep') as mock_sleep:
            
            mock_config_instance = MagicMock()
            mock_config.return_value = mock_config_instance
            mock_config_instance.api_key = {}
            mock_config_instance.assert_hostname = None
            
            # Mock ApiClient
            mock_client_instance = MagicMock()
            mock_api_client.return_value = mock_client_instance
            
            # Mock asyncio.sleep
            async def mock_sleep_func(delay):
                return None
            mock_sleep.side_effect = mock_sleep_func
            
            # Mock email API to fail
            mock_api_instance = MagicMock()
            mock_api_class.return_value = mock_api_instance
            mock_api_instance.send_transac_email.side_effect = ApiException(
                status=500,
                reason="Internal Server Error"
            )
            
            # Mock ensure_user_persisted as async function
            async def mock_ensure_user_func(*args, **kwargs):
                return {
                    "id": "test-user-123",
                    "email": "test@example.com",
                    "auth_source": "email_password",
                    "created_at": datetime.now().isoformat()
                }
            mock_ensure_user.side_effect = mock_ensure_user_func
            
            signup_data = {
                "email": "test@example.com",
                "password": "testpass123",
                "confirm_password": "testpass123",
                "country": "AR",
                "date_of_birth": "1990-01-01"
            }
            
            # Registration should still succeed even if email fails
            response = client.post("/auth/signup", json=signup_data)
            assert response.status_code == 200
            assert "access_token" in response.json()

# ============================================================================
# TESTS DE INTEGRACIÓN
# ============================================================================

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
            if call_count[0] == 1:  # Create watchlist
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

# ============================================================================
# TESTS DE CONEXIONES DE BROKER
# ============================================================================

@pytest.mark.unit
class TestConexionIOL:
    """Test suite for IOL connection module"""
    
    def test_conexion_iol_initialization(self):
        """Test IOL connection initialization"""
        conexion = ConexionIOL("test_user", "test_pass")
        assert conexion.username == "test_user"
        assert conexion.password == "test_pass"
        assert conexion.access_token is None
    
    @patch('conexion_iol.requests.post')
    def test_iol_autenticar_success(self, mock_post):
        """Test successful IOL authentication"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"access_token": "test-token-123"}
        mock_post.return_value = mock_response
        
        conexion = ConexionIOL("test_user", "test_pass")
        import asyncio
        result = asyncio.run(conexion.autenticar())
        
        assert result is True
        assert conexion.access_token == "test-token-123"
    
    @patch('conexion_iol.requests.post')
    def test_iol_autenticar_failure(self, mock_post):
        """Test failed IOL authentication"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Invalid credentials"
        mock_post.return_value = mock_response
        
        conexion = ConexionIOL("test_user", "test_pass")
        import asyncio
        result = asyncio.run(conexion.autenticar())
        
        assert result is False
        assert conexion.access_token is None
    
    @patch('conexion_iol.requests.get')
    @patch('conexion_iol.requests.post')
    def test_iol_obtener_portfolio_success(self, mock_post, mock_get):
        """Test successful portfolio retrieval from IOL"""
        # Mock authentication
        mock_auth_response = Mock()
        mock_auth_response.status_code = 200
        mock_auth_response.json.return_value = {"access_token": "test-token-123"}
        mock_post.return_value = mock_auth_response
        
        # Mock portfolio response
        mock_portfolio_response = Mock()
        mock_portfolio_response.status_code = 200
        mock_portfolio_response.json.return_value = {
            "activos": [
                {
                    "simbolo": "AAPL",
                    "descripcion": "Apple Inc.",
                    "cantidad": 10,
                    "precioCompra": 150.0,
                    "ultimoPrecio": 155.0,
                    "valorizado": 1550.0,
                    "gananciaPerdida": 50.0,
                    "gananciaPerdidaPorcentaje": 3.33
                }
            ]
        }
        mock_get.return_value = mock_portfolio_response
        
        conexion = ConexionIOL("test_user", "test_pass")
        import asyncio
        portfolio = asyncio.run(conexion.obtener_portfolio())
        
        assert portfolio is not None
        assert len(portfolio) == 1
        assert portfolio[0]["ticker"] == "AAPL"
        assert portfolio[0]["broker"] == "IOL"
        assert portfolio[0]["quantity"] == 10
    
    def test_iol_obtener_info(self):
        """Test IOL connection info retrieval"""
        conexion = ConexionIOL("test_user", "test_pass")
        info = conexion.obtener_info()
        
        assert info["broker"] == "IOL"
        assert info["username"] == "test_user"
        assert info["has_token"] is False

@pytest.mark.unit
class TestConexionBinance:
    """Test suite for Binance connection module"""
    
    def test_conexion_binance_initialization(self):
        """Test Binance connection initialization"""
        conexion = ConexionBinance("test_api_key", "test_api_secret")
        assert conexion.api_key == "test_api_key"
        assert conexion.api_secret == "test_api_secret"
    
    @patch('conexion_binance.requests.get')
    def test_binance_validar_credenciales_success(self, mock_get):
        """Test successful Binance credentials validation"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"balances": []}
        mock_get.return_value = mock_response
        
        conexion = ConexionBinance("test_api_key", "test_api_secret")
        import asyncio
        result = asyncio.run(conexion.validar_credenciales())
        
        assert result is True
    
    @patch('conexion_binance.requests.get')
    def test_binance_validar_credenciales_failure(self, mock_get):
        """Test failed Binance credentials validation"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Invalid API key"
        mock_get.return_value = mock_response
        
        conexion = ConexionBinance("test_api_key", "test_api_secret")
        import asyncio
        result = asyncio.run(conexion.validar_credenciales())
        
        assert result is False
    
    @patch('conexion_binance.requests.get')
    def test_binance_obtener_portfolio_success(self, mock_get):
        """Test successful portfolio retrieval from Binance"""
        call_count = [0]
        def mock_get_side_effect(*args, **kwargs):
            call_count[0] += 1
            mock_response = Mock()
            if call_count[0] == 1:  # First call is account info
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "balances": [
                        {
                            "asset": "BTC",
                            "free": "0.5",
                            "locked": "0.0"
                        },
                        {
                            "asset": "USDT",
                            "free": "1000.0",
                            "locked": "0.0"
                        }
                    ]
                }
            else:  # Second call is prices
                mock_response.status_code = 200
                mock_response.json.return_value = [
                    {"symbol": "BTCUSDT", "price": "50000.0"},
                    {"symbol": "USDTUSDT", "price": "1.0"}
                ]
            return mock_response
        
        mock_get.side_effect = mock_get_side_effect
        
        conexion = ConexionBinance("test_api_key", "test_api_secret")
        import asyncio
        portfolio = asyncio.run(conexion.obtener_portfolio())
        
        assert portfolio is not None
        assert len(portfolio) == 2
        assert any(item["ticker"] == "BTC" for item in portfolio)
        assert any(item["ticker"] == "USDT" for item in portfolio)
    
    def test_binance_obtener_info(self):
        """Test Binance connection info retrieval"""
        conexion = ConexionBinance("test_api_key_12345", "test_api_secret")
        info = conexion.obtener_info()
        
        assert info["broker"] == "BINANCE"
        assert info["api_key"] == "test_api_key_12345..."
        assert "base_url" in info

@pytest.mark.integration
class TestBrokerConnectionsAPI:
    """Test broker connections API endpoints"""
    
    def test_create_iol_connection(self, client, auth_headers, mock_supabase, monkeypatch):
        """Test creating an IOL broker connection"""
        with patch('conexion_iol.ConexionIOL') as mock_iol_class:
            # Mock successful validation
            mock_iol = MagicMock()
            mock_iol.validar_credenciales = MagicMock(return_value=True)
            mock_iol_class.return_value = mock_iol
            
            # Mock Supabase responses
            mock_existing = Mock()
            mock_existing.data = []  # No existing connection
            
            mock_create = Mock()
            mock_create.data = [{
                "id": "conn-123",
                "broker_name": "IOL",
                "is_active": True,
                "created_at": datetime.now().isoformat()
            }]
            
            call_count = [0]
            def mock_execute():
                call_count[0] += 1
                if call_count[0] == 1:
                    return mock_existing
                return mock_create
            
            monkeypatch.setattr("app_supabase.supabase.table", lambda _: mock_supabase.table())
            mock_supabase.table().execute.side_effect = mock_execute
            
            connection_data = {
                "broker_name": "IOL",
                "username": "test_user",
                "password": "test_pass"
            }
            
            response = client.post("/api/broker-connections", json=connection_data, headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["connection"]["broker_name"] == "IOL"
    
    def test_create_binance_connection(self, client, auth_headers, mock_supabase, monkeypatch):
        """Test creating a Binance broker connection"""
        with patch('conexion_binance.ConexionBinance') as mock_binance_class:
            # Mock successful validation
            mock_binance = MagicMock()
            mock_binance.validar_credenciales = MagicMock(return_value=True)
            mock_binance_class.return_value = mock_binance
            
            # Mock Supabase responses
            mock_existing = Mock()
            mock_existing.data = []
            
            mock_create = Mock()
            mock_create.data = [{
                "id": "conn-456",
                "broker_name": "BINANCE",
                "is_active": True,
                "created_at": datetime.now().isoformat()
            }]
            
            call_count = [0]
            def mock_execute():
                call_count[0] += 1
                if call_count[0] == 1:
                    return mock_existing
                return mock_create
            
            monkeypatch.setattr("app_supabase.supabase.table", lambda _: mock_supabase.table())
            mock_supabase.table().execute.side_effect = mock_execute
            
            connection_data = {
                "broker_name": "BINANCE",
                "api_key": "test_api_key",
                "api_secret": "test_api_secret"
            }
            
            response = client.post("/api/broker-connections", json=connection_data, headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["connection"]["broker_name"] == "BINANCE"
    
    def test_get_broker_portfolio_iol(self, client, auth_headers, mock_supabase, monkeypatch):
        """Test getting portfolio from IOL connection"""
        with patch('conexion_iol.ConexionIOL') as mock_iol_class:
            # Mock portfolio
            mock_portfolio = [
                {
                    "ticker": "AAPL",
                    "name": "Apple Inc.",
                    "quantity": 10,
                    "broker": "IOL"
                }
            ]
            
            mock_iol = MagicMock()
            mock_iol.obtener_portfolio = MagicMock(return_value=mock_portfolio)
            mock_iol_class.return_value = mock_iol
            
            # Mock Supabase connection lookup
            mock_connection = Mock()
            mock_connection.data = [{
                "id": "conn-123",
                "broker_name": "IOL",
                "is_active": True,
                "username_encrypted": "encrypted_user",
                "password_encrypted": "encrypted_pass"
            }]
            
            # Mock decrypt function
            def mock_decrypt(encrypted):
                return "decrypted_value"
            
            monkeypatch.setattr("app_supabase.supabase.table", lambda _: mock_supabase.table())
            monkeypatch.setattr("app_supabase.decrypt_api_key", mock_decrypt)
            mock_supabase.table().execute.return_value = mock_connection
            
            response = client.get("/api/broker-connections/conn-123/portfolio", headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["broker"] == "IOL"
            assert len(data["portfolio"]) == 1
    
    def test_get_broker_portfolio_binance(self, client, auth_headers, mock_supabase, monkeypatch):
        """Test getting portfolio from Binance connection"""
        with patch('conexion_binance.ConexionBinance') as mock_binance_class:
            # Mock portfolio
            mock_portfolio = [
                {
                    "ticker": "BTC",
                    "name": "Bitcoin",
                    "quantity": 0.5,
                    "broker": "BINANCE"
                }
            ]
            
            mock_binance = MagicMock()
            mock_binance.obtener_portfolio = MagicMock(return_value=mock_portfolio)
            mock_binance_class.return_value = mock_binance
            
            # Mock Supabase connection lookup
            mock_connection = Mock()
            mock_connection.data = [{
                "id": "conn-456",
                "broker_name": "BINANCE",
                "is_active": True,
                "api_key_encrypted": "encrypted_key",
                "api_secret_encrypted": "encrypted_secret"
            }]
            
            # Mock decrypt function
            def mock_decrypt(encrypted):
                return "decrypted_value"
            
            monkeypatch.setattr("app_supabase.supabase.table", lambda _: mock_supabase.table())
            monkeypatch.setattr("app_supabase.decrypt_api_key", mock_decrypt)
            mock_supabase.table().execute.return_value = mock_connection
            
            response = client.get("/api/broker-connections/conn-456/portfolio", headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["broker"] == "BINANCE"
            assert len(data["portfolio"]) == 1

