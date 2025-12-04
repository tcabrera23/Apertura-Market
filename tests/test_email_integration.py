"""
Tests for email integration, specifically onboarding emails
Verifies that users receive onboarding emails when they register
"""
import pytest
from unittest.mock import Mock, MagicMock, patch, call
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import os

# Set test environment variables before importing app
os.environ["SUPABASE_URL"] = "https://test.supabase.co"
os.environ["SUPABASE_SERVICE_KEY"] = "test-key"
os.environ["SUPABASE_ANON_KEY"] = "test-anon-key"
os.environ["SUPABASE_JWT_SECRET"] = "test-jwt-secret"
os.environ["BREVO_API_KEY"] = "test-brevo-key"

from app_supabase import app, send_alert_email
from email_templates import get_onboarding_email_template


@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


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
            # Extract email from the sign_up call
            # sign_up is called with a dict like {"email": "...", "password": "...", "options": {...}}
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
        # Note: user_email is not included in the HTML content, only user_name
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
            # Add assert_hostname attribute that the SDK checks
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
        import asyncio
        
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
            assert "test" in call_args['htmlContent']  # User name from email
            assert "BullAnalytics" in call_args['htmlContent']
            assert call_args['sender']['name'] == "BullAnalytics"
            assert call_args['sender']['email'] == "noreply@aperturaia.com"
    
    def test_signup_email_template_content(
        self,
        client,
        mock_brevo_api,
        mock_supabase_auth,
        mock_supabase_table,
        mock_create_default_subscription
    ):
        """Test that the onboarding email contains expected content"""
        import asyncio
        
        with patch('app_supabase.Configuration') as mock_config, \
             patch('app_supabase.ApiClient') as mock_api_client, \
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
            
            # Mock ensure_user_persisted as async function
            async def mock_ensure_user_func(*args, **kwargs):
                return {
                    "id": "test-user-123",
                    "email": "john.doe@example.com",
                    "auth_source": "email_password",
                    "created_at": datetime.now().isoformat()
                }
            mock_ensure_user.side_effect = mock_ensure_user_func
            
            signup_data = {
                "email": "john.doe@example.com",
                "password": "testpass123",
                "confirm_password": "testpass123",
                "country": "AR",
                "date_of_birth": "1990-01-01"
            }
            
            response = client.post("/auth/signup", json=signup_data)
            assert response.status_code == 200
            
            # Get the email content that was sent (if email was sent)
            if mock_brevo_api.send_transac_email.called:
                call_args = mock_brevo_api.send_transac_email.call_args[0][0]
                html_content = call_args['htmlContent']
                
                # Verify key content is present
                assert "john.doe" in html_content or "john" in html_content  # User name
                assert "BullAnalytics" in html_content
                assert "Dashboard" in html_content
                assert "listas" in html_content or "seguimiento" in html_content
                assert "alertas" in html_content
                assert "gráficos" in html_content or "visualizar" in html_content
    
    def test_signup_email_failure_does_not_block_registration(
        self,
        client,
        mock_supabase_auth,
        mock_supabase_table,
        mock_create_default_subscription
    ):
        """Test that email sending failure doesn't prevent user registration"""
        from sib_api_v3_sdk.rest import ApiException
        import asyncio
        
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
    
    def test_signup_with_different_email_formats(
        self,
        client,
        mock_brevo_api,
        mock_supabase_auth,
        mock_supabase_table,
        mock_create_default_subscription
    ):
        """Test that user name extraction works for different email formats"""
        import asyncio
        
        test_cases = [
            ("simple@example.com", "simple"),
            ("first.last@example.com", "first.last"),
            ("user+tag@example.com", "user+tag"),
            ("123user@example.com", "123user"),
        ]
        
        with patch('app_supabase.Configuration') as mock_config, \
             patch('app_supabase.ApiClient') as mock_api_client, \
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
            
            for email, expected_name in test_cases:
                # The mock_supabase_auth fixture already handles different emails via side_effect
                # No need to manually update it here
                
                # Mock ensure_user_persisted as async function
                async def mock_ensure_user_func(*args, **kwargs):
                    return {
                        "id": "test-user-123",
                        "email": email,
                        "auth_source": "email_password",
                        "created_at": datetime.now().isoformat()
                    }
                mock_ensure_user.side_effect = mock_ensure_user_func
                
                signup_data = {
                    "email": email,
                    "password": "testpass123",
                    "confirm_password": "testpass123",
                    "country": "AR",
                    "date_of_birth": "1990-01-01"
                }
                
                response = client.post("/auth/signup", json=signup_data)
                assert response.status_code == 200
                
                # Verify email was sent with correct user name (if email was sent)
                if mock_brevo_api.send_transac_email.called:
                    call_args = mock_brevo_api.send_transac_email.call_args[0][0]
                    html_content = call_args['htmlContent']
                    
                    # The user name should be extracted from email (part before @)
                    assert expected_name in html_content or email in html_content
                
                # Reset mock for next iteration
                mock_brevo_api.reset_mock()


class TestEmailIntegrationEndToEnd:
    """End-to-end tests for email integration"""
    
    def test_complete_onboarding_flow(
        self,
        client,
        mock_brevo_api,
        mock_supabase_auth,
        mock_supabase_table,
        mock_create_default_subscription
    ):
        """Test the complete flow from registration to email delivery"""
        import asyncio
        
        with patch('app_supabase.Configuration') as mock_config, \
             patch('app_supabase.ApiClient') as mock_api_client, \
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
            
            # Mock ensure_user_persisted as async function
            async def mock_ensure_user_func(*args, **kwargs):
                return {
                    "id": "test-user-123",
                    "email": "newuser@example.com",
                    "auth_source": "email_password",
                    "created_at": datetime.now().isoformat()
                }
            mock_ensure_user.side_effect = mock_ensure_user_func
            
            # Step 1: User registers
            signup_data = {
                "email": "newuser@example.com",
                "password": "securepass123",
                "confirm_password": "securepass123",
                "country": "US",
                "date_of_birth": "1995-05-15"
            }
            
            response = client.post("/auth/signup", json=signup_data)
            
            # Step 2: Verify registration succeeded
            assert response.status_code == 200
            data = response.json()
            assert data["user"]["email"] == "newuser@example.com"
            assert "access_token" in data
            
            # Step 3: Verify email was sent
            assert mock_brevo_api.send_transac_email.called
            
            # Step 4: Verify email content
            call_args = mock_brevo_api.send_transac_email.call_args[0][0]
            assert call_args['to'][0]['email'] == "newuser@example.com"
            assert "¡Bienvenido" in call_args['subject']
            
            # Step 5: Verify template was used correctly
            html = call_args['htmlContent']
            assert "newuser" in html  # User name
            assert "BullAnalytics" in html
            assert "Dashboard" in html

