// Subscription Management JavaScript with Vexor Integration

// Supabase Configuration (Matching app_supabase.py)
const SUPABASE_URL = "https://pwumamzbicapuiqkwrey.supabase.co";
// NOTA: En una app real, la ANON_KEY debería estar en un config.js o cargada de env.
// La obtenemos de lo que ya está en uso o la definimos aquí para la migración.
const SUPABASE_ANON_KEY = ""; // El usuario debe completar esto o lo sacamos de js/login.js si estuviera allí.

// Obtener token del localStorage
function getAuthToken() {
    return localStorage.getItem('access_token');
}

// Obtener datos del usuario
function getUserData() {
    const data = localStorage.getItem('user_data');
    return data ? JSON.parse(data) : null;
}

// Verificar si el usuario está autenticado
function isAuthenticated() {
    return !!getAuthToken();
}

// Redirigir a login si no está autenticado
function requireAuth() {
    if (!isAuthenticated()) {
        const currentUrl = window.location.href;
        localStorage.setItem('redirect_after_login', currentUrl);
        window.location.href = 'login.html';
        return false;
    }
    return true;
}

/**
 * Muestra un modal para elegir la plataforma de pago
 */
async function showPlatformSelector(planName, buttonElement) {
    // Si ya existe un modal, lo eliminamos
    const existingModal = document.getElementById('platform-selector-modal');
    if (existingModal) existingModal.remove();

    // Obtener info de moneda del usuario
    const currencyInfo = window.CurrencyHandler ? 
        window.CurrencyHandler.getUserCurrencyInfo() : 
        { platform: 'paypal', code: 'USD' };

    // Determinar qué plataforma resaltar como recomendada
    const isRecommendedPaypal = currencyInfo.platform === 'paypal';
    const isRecommendedMercadoPago = currencyInfo.platform === 'mercadopago';

    const modalHtml = `
        <div id="platform-selector-modal" class="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 backdrop-blur-sm">
            <div class="bg-white dark:bg-gray-800 rounded-2xl p-8 max-w-md w-full mx-4 shadow-2xl border border-gray-200 dark:border-gray-700">
                <h3 class="text-2xl font-bold text-gray-900 dark:text-white mb-2 text-center">Selecciona tu método de pago</h3>
                <p class="text-sm text-gray-600 dark:text-gray-400 mb-6 text-center">
                    ${currencyInfo.code !== 'USD' ? `Precios en ${currencyInfo.code}` : 'Precios en USD'}
                </p>
                <div class="grid grid-cols-1 gap-4">
                    <button onclick="window.createSubscription('${planName}', 'paypal')" class="flex items-center justify-center gap-3 p-4 bg-[#0070ba] hover:bg-[#005ea6] text-white rounded-xl transition-all font-bold ${isRecommendedPaypal ? 'ring-4 ring-yellow-400' : ''}">
                        <img src="https://www.paypalobjects.com/webstatic/mktg/logo/pp_cc_mark_37x23.jpg" alt="PayPal" class="h-6">
                        Pagar con PayPal (USD)
                        ${isRecommendedPaypal ? '<span class="ml-2 bg-yellow-400 text-yellow-900 px-2 py-1 rounded text-xs font-bold">Recomendado</span>' : ''}
                    </button>
                    <button onclick="window.createSubscription('${planName}', 'mercadopago')" class="flex items-center justify-center gap-3 p-4 bg-[#009ee3] hover:bg-[#008cc9] text-white rounded-xl transition-all font-bold ${isRecommendedMercadoPago ? 'ring-4 ring-yellow-400' : ''}">
                        <img src="https://vignette.wikia.nocookie.net/logopedia/images/2/22/Mercado_Pago_logo.png/revision/latest?cb=20180706173059" alt="Mercado Pago" class="h-6 invert">
                        Pagar con Mercado Pago (ARS)
                        ${isRecommendedMercadoPago ? '<span class="ml-2 bg-yellow-400 text-yellow-900 px-2 py-1 rounded text-xs font-bold">Recomendado</span>' : ''}
                    </button>
                </div>
                <button onclick="document.getElementById('platform-selector-modal').remove()" class="mt-6 w-full text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 text-sm font-medium">
                    Cancelar
                </button>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modalHtml);
}

// Crear suscripción y redirigir a la plataforma vía Vexor Edge Function
async function createSubscription(planName, platform = null, buttonElement = null) {
    // 1. Verificar autenticación
    if (!requireAuth()) return;

    // 2. Si no hay plataforma, mostrar selector
    if (!platform) {
        showPlatformSelector(planName, buttonElement);
        return;
    }

    // Cerrar modal si existe
    const modal = document.getElementById('platform-selector-modal');
    if (modal) modal.remove();

    const token = getAuthToken();
    const userData = getUserData();
    
    // 3. Mostrar loading
    const originalText = buttonElement ? buttonElement.textContent : 'Procesando...';
    if (buttonElement) {
        buttonElement.disabled = true;
        buttonElement.textContent = 'Iniciando checkout...';
        buttonElement.style.opacity = '0.6';
    }

    try {
        console.log(`Iniciando suscripción a ${planName} vía ${platform} para usuario ${userData?.id}`);

        // Llamada a Supabase Edge Function
        const response = await fetch(`${SUPABASE_URL}/functions/v1/vexor-payments`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                plan_name: planName,
                platform: platform,
                user_id: userData.id
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Error al iniciar el pago con Vexor');
        }

        const result = await response.json();
        
        if (result.success && result.approval_url) {
            // Guardamos el vexor_id localmente por si necesitamos verificarlo luego
            localStorage.setItem('pending_vexor_id', result.vexor_id);
            // Redirigir al checkout de Vexor (ya sea PayPal o Mercado Pago)
            window.location.href = result.approval_url;
        } else {
            throw new Error('No se recibió la URL de aprobación');
        }

    } catch (error) {
        console.error('Error Vexor:', error);
        alert(`Error al procesar el pago: ${error.message}`);
        if (buttonElement) {
            buttonElement.disabled = false;
            buttonElement.textContent = originalText;
            buttonElement.style.opacity = '1';
        }
    }
}

// Exponer función globalmente
window.createSubscription = createSubscription;

// Inicializar botones de suscripción
function initializeSubscriptionButtons() {
    document.querySelectorAll('[data-plan]').forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault();
            const planName = button.getAttribute('data-plan');
            createSubscription(planName, null, button);
        });
    });
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    initializeSubscriptionButtons();
    
    // Verificar si venimos de un pago exitoso
    if (window.location.pathname.includes('subscription-success')) {
        const vexorId = localStorage.getItem('pending_vexor_id');
        if (vexorId) {
            console.log('Pago completado exitosamente. Identificador Vexor:', vexorId);
            localStorage.removeItem('pending_vexor_id');
            // Aquí podrías llamar a una función para verificar el estado final
            // aunque el Webhook ya debería haber actualizado la base de datos.
        }
    }
});
