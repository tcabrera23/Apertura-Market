// Account Page JavaScript
// Carga dinámicamente la información del usuario y su suscripción

const API_BASE_URL = 'http://localhost:8080/api';
const AUTH_API_BASE_URL = 'http://localhost:8080/auth';

// Obtener token del localStorage
function getAuthToken() {
    return localStorage.getItem('access_token');
}

// Cargar información del usuario
async function loadUserInfo() {
    const token = getAuthToken();
    if (!token) {
        // Redirigir al login si no hay token
        window.location.href = 'login.html';
        return;
    }

    try {
        // Obtener perfil del usuario
        const userResponse = await fetch(`http://localhost:8080/api/v1/user/me`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!userResponse.ok) {
            if (userResponse.status === 401) {
                // Token inválido, redirigir al login
                localStorage.removeItem('access_token');
                localStorage.removeItem('user_data');
                window.location.href = 'login.html';
                return;
            }
            throw new Error('Error al cargar información del usuario');
        }

        const userData = await userResponse.json();
        
        // Actualizar email
        document.getElementById('userEmail').textContent = userData.email || 'N/A';
        
        // Actualizar fecha de registro
        if (userData.created_at) {
            const memberSince = new Date(userData.created_at);
            document.getElementById('memberSince').textContent = memberSince.toLocaleDateString('es-ES', { 
                year: 'numeric', 
                month: 'long' 
            });
        }

        // Cargar suscripción
        await loadSubscription(token, userData.user_id);
        
    } catch (error) {
        console.error('Error loading user info:', error);
        showError('Error al cargar la información del usuario');
    }
}

// Cargar información de la suscripción
async function loadSubscription(token, userId) {
    try {
        const response = await fetch(`${API_BASE_URL}/subscriptions/current`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            if (response.status === 404) {
                // No hay suscripción, mostrar plan gratuito
                displayPlanInfo({
                    plan_name: 'free',
                    display_name: 'Plan Básico',
                    price: '0.00',
                    status: 'active',
                    trial_end: null,
                    current_period_end: null
                });
                return;
            }
            throw new Error('Error al cargar la suscripción');
        }

        const subscription = await response.json();
        displayPlanInfo(subscription);
        
    } catch (error) {
        console.error('Error loading subscription:', error);
        // Mostrar plan gratuito por defecto si hay error
        displayPlanInfo({
            plan_name: 'free',
            display_name: 'Plan Básico',
            price: '0.00',
            status: 'active',
            trial_end: null,
            current_period_end: null
        });
    }
}

// Mostrar información del plan
function displayPlanInfo(subscription) {
    const planNameEl = document.getElementById('currentPlanName');
    const planPriceEl = document.getElementById('currentPlanPrice');
    
    if (!planNameEl || !planPriceEl) return;

    // Determinar nombre del plan
    let displayName = subscription.display_name || subscription.plan_name || 'Plan Básico';
    let price = subscription.price || '0.00';
    
    // Verificar si está en trial
    const now = new Date();
    const trialEnd = subscription.trial_end ? new Date(subscription.trial_end) : null;
    const isInTrial = trialEnd && trialEnd > now;
    
    if (isInTrial) {
        const daysLeft = Math.ceil((trialEnd - now) / (1000 * 60 * 60 * 24));
        displayName = `${displayName} (Trial - ${daysLeft} días restantes)`;
    }
    
    planNameEl.textContent = displayName;
    
    if (price === '0.00' || price === 0) {
        planPriceEl.textContent = 'Gratis';
    } else {
        planPriceEl.textContent = `$${parseFloat(price).toFixed(2)}/mes`;
    }
}

// Cargar historial de alertas
async function loadAlertHistory() {
    const token = getAuthToken();
    if (!token) return;

    const container = document.getElementById('alertHistory');
    if (!container) return;

    try {
        const response = await fetch(`${API_BASE_URL}/alerts`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            if (response.status === 401) {
                window.location.href = 'login.html';
                return;
            }
            throw new Error('Error al cargar alertas');
        }

        const alerts = await response.json();
        
        if (alerts.length === 0) {
            container.innerHTML = '<div class="text-center py-8 text-gray-500 dark:text-gray-400"><p>No hay alertas en tu historial</p></div>';
            return;
        }

        container.innerHTML = alerts.map(alert => `
            <div class="p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                <div class="flex justify-between items-start">
                    <div>
                        <h4 class="font-semibold text-gray-900 dark:text-white">${alert.message || 'Alerta'}</h4>
                        <p class="text-sm text-gray-600 dark:text-gray-400 mt-1">${alert.ticker || 'N/A'} - ${alert.alert_type || 'N/A'}</p>
                        <p class="text-xs text-gray-500 dark:text-gray-500 mt-2">${new Date(alert.created_at).toLocaleDateString()}</p>
                    </div>
                    <span class="px-3 py-1 ${alert.is_read ? 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-400' : 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'} rounded-full text-xs font-semibold">
                        ${alert.is_read ? 'Leída' : 'Nueva'}
                    </span>
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Error loading alert history:', error);
        container.innerHTML = '<div class="text-center py-8 text-red-500"><p>Error al cargar el historial</p></div>';
    }
}

// Mostrar error
function showError(message) {
    // Puedes implementar un sistema de notificaciones aquí
    console.error(message);
    alert(message);
}

// Inicializar página
document.addEventListener('DOMContentLoaded', () => {
    loadUserInfo();
    loadAlertHistory();
});

