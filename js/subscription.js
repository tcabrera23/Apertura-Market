// Subscription Management JavaScript
// Obtener token del localStorage
function getAuthToken() {
    return localStorage.getItem('access_token');
}

// Verificar si el usuario está autenticado
function isAuthenticated() {
    return !!getAuthToken();
}

// Redirigir a login si no está autenticado
function requireAuth() {
    if (!isAuthenticated()) {
        // Guardar la URL actual para redirigir después del login
        const currentUrl = window.location.href;
        localStorage.setItem('redirect_after_login', currentUrl);
        window.location.href = 'login.html';
        return false;
    }
    return true;
}

// Crear suscripción y redirigir a PayPal
async function createSubscription(planName, buttonElement = null) {
    // Verificar autenticación
    if (!requireAuth()) {
        return;
    }

    const token = getAuthToken();
    
    // Si se pasa un botón, mostrar loading
    if (buttonElement) {
        const originalText = buttonElement.textContent;
        buttonElement.disabled = true;
        buttonElement.textContent = 'Procesando...';
        buttonElement.style.opacity = '0.6';
    }

    try {
        // const API_BASE_URL = window.API_BASE_URL || 'http://localhost:8080/api'; // Development
        const API_BASE_URL = window.API_BASE_URL || 'https://api.bullanalytics.io/api'; // Production
        const response = await fetch(`${API_BASE_URL}/subscriptions/create`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                plan_name: planName
            })
        });

        if (!response.ok) {
            if (response.status === 401) {
                // Token inválido, redirigir al login
                localStorage.removeItem('access_token');
                localStorage.removeItem('user_data');
                alert('Tu sesión ha expirado. Por favor, inicia sesión nuevamente.');
                window.location.href = 'login.html';
                return;
            }

            const errorData = await response.json().catch(() => ({}));
            const errorMessage = errorData.detail || errorData.message || 'Error al crear suscripción';
            alert(`Error: ${errorMessage}`);
            if (buttonElement) {
                buttonElement.disabled = false;
                buttonElement.textContent = originalText || 'Proceder con PayPal';
                buttonElement.style.opacity = '1';
            }
            return;
        }

        const result = await response.json();
        
        if (result.success && result.approval_url) {
            // Redirigir a PayPal checkout
            window.location.href = result.approval_url;
        } else {
            throw new Error('No se recibió approval_url de PayPal');
        }

    } catch (error) {
        console.error('Error creando suscripción:', error);
        alert(`Error al procesar la suscripción: ${error.message}`);
        if (buttonElement) {
            buttonElement.disabled = false;
            buttonElement.textContent = originalText || 'Proceder con PayPal';
            buttonElement.style.opacity = '1';
        }
    }
}

// Exponer función globalmente
window.createSubscription = createSubscription;

// Verificar suscripción después del retorno de PayPal
async function verifySubscription() {
    const urlParams = new URLSearchParams(window.location.search);
    const subscriptionId = urlParams.get('subscription_id');
    const token = urlParams.get('token');

    if (!subscriptionId) {
        console.log('No se encontró subscription_id en la URL');
        return;
    }

    const authToken = getAuthToken();
    if (!authToken) {
        console.error('No hay token de autenticación');
        window.location.href = 'login.html';
        return;
    }

    try {
        // const API_BASE_URL = window.API_BASE_URL || 'http://localhost:8080/api'; // Development
        const API_BASE_URL = window.API_BASE_URL || 'https://api.bullanalytics.io/api'; // Production
        const response = await fetch(
            `${API_BASE_URL}/subscriptions/verify?subscription_id=${subscriptionId}`,
            {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${authToken}`
                }
            }
        );

        if (!response.ok) {
            throw new Error('Error verificando suscripción');
        }

        const result = await response.json();
        console.log('Suscripción verificada:', result);

        // Mostrar mensaje de éxito
        if (result.status === 'ACTIVE' || result.status === 'active') {
            // La suscripción está activa
            return {
                success: true,
                status: result.status
            };
        } else {
            // La suscripción está pendiente
            return {
                success: true,
                status: result.status,
                pending: true
            };
        }

    } catch (error) {
        console.error('Error verificando suscripción:', error);
        return {
            success: false,
            error: error.message
        };
    }
}

// Inicializar botones de suscripción
function initializeSubscriptionButtons() {
    // Buscar todos los botones con data-plan
    document.querySelectorAll('[data-plan]').forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault();
            const planName = button.getAttribute('data-plan');
            createSubscription(planName);
        });
    });
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    initializeSubscriptionButtons();
    
    // Si estamos en la página de éxito, verificar la suscripción
    if (window.location.pathname.includes('subscription-success')) {
        verifySubscription();
    }
});

