// Currency Handler - Detección de país y conversión de precios
// Maneja la visualización de precios en moneda local para usuarios internacionales

// Configuración de monedas soportadas
const SUPPORTED_CURRENCIES = {
    'AR': { code: 'ARS', symbol: '$', name: 'Peso Argentino', platform: 'mercadopago' },
    'UY': { code: 'UYU', symbol: '$', name: 'Peso Uruguayo', platform: 'mercadopago' },
    'CL': { code: 'CLP', symbol: '$', name: 'Peso Chileno', platform: 'mercadopago' },
    'BR': { code: 'BRL', symbol: 'R$', name: 'Real Brasileño', platform: 'mercadopago' },
    'MX': { code: 'MXN', symbol: '$', name: 'Peso Mexicano', platform: 'mercadopago' },
    'CO': { code: 'COP', symbol: '$', name: 'Peso Colombiano', platform: 'mercadopago' },
    'PE': { code: 'PEN', symbol: 'S/', name: 'Sol Peruano', platform: 'mercadopago' },
    // Resto del mundo usa PayPal con USD
    'DEFAULT': { code: 'USD', symbol: '$', name: 'US Dollar', platform: 'paypal' }
};

// Precios base en USD (deben coincidir con la base de datos)
const BASE_PRICES_USD = {
    'free': 0,
    'plus': 9.99,
    'pro': 19.99
};

// Cache para tasas de cambio
let exchangeRatesCache = null;
let lastFetchTime = null;
const CACHE_DURATION = 60 * 60 * 1000; // 1 hora

/**
 * Detecta el país del usuario usando una API de geolocalización
 */
async function detectUserCountry() {
    try {
        // Intentar primero con ipapi (gratuita, 1000 requests/día)
        const response = await fetch('https://ipapi.co/json/');
        if (response.ok) {
            const data = await response.json();
            return data.country_code || 'US';
        }
    } catch (error) {
        console.warn('Error detectando país con ipapi:', error);
    }

    // Fallback: detectar desde navegador o usar default
    const browserLanguage = navigator.language || navigator.userLanguage;
    if (browserLanguage.includes('es-AR')) return 'AR';
    if (browserLanguage.includes('es-UY')) return 'UY';
    if (browserLanguage.includes('es-CL')) return 'CL';
    if (browserLanguage.includes('pt-BR')) return 'BR';
    if (browserLanguage.includes('es-MX')) return 'MX';
    if (browserLanguage.includes('es-CO')) return 'CO';
    if (browserLanguage.includes('es-PE')) return 'PE';
    
    return 'US'; // Default
}

/**
 * Obtiene las tasas de cambio actuales
 */
async function getExchangeRates() {
    // Verificar si tenemos cache válido
    const now = Date.now();
    if (exchangeRatesCache && lastFetchTime && (now - lastFetchTime < CACHE_DURATION)) {
        return exchangeRatesCache;
    }

    try {
        // Usar API gratuita de tasas de cambio
        const response = await fetch('https://api.exchangerate-api.com/v4/latest/USD');
        const data = await response.json();
        
        if (data.rates) {
            exchangeRatesCache = data.rates;
            lastFetchTime = now;
            return data.rates;
        }
    } catch (error) {
        console.error('Error obteniendo tasas de cambio:', error);
    }

    // Fallback rates si falla la API (valores aproximados)
    return {
        ARS: 1000,
        UYU: 43,
        CLP: 950,
        BRL: 5.7,
        MXN: 18,
        COP: 4300,
        PEN: 3.7,
        USD: 1
    };
}

/**
 * Convierte un precio de USD a la moneda especificada
 */
async function convertPrice(priceUSD, targetCurrency) {
    if (targetCurrency === 'USD') {
        return priceUSD;
    }

    const rates = await getExchangeRates();
    const rate = rates[targetCurrency] || 1;
    const convertedPrice = priceUSD * rate;

    // Redondear según la moneda
    if (['CLP', 'COP', 'ARS'].includes(targetCurrency)) {
        // Monedas sin decimales
        return Math.round(convertedPrice);
    } else {
        // Otras monedas con 2 decimales
        return Math.round(convertedPrice * 100) / 100;
    }
}

/**
 * Formatea un precio con el símbolo de moneda correcto
 */
function formatPrice(price, currencyCode) {
    const currencyInfo = Object.values(SUPPORTED_CURRENCIES).find(c => c.code === currencyCode) || SUPPORTED_CURRENCIES.DEFAULT;
    
    if (price === 0) {
        return 'Gratis';
    }

    // Formatear según la moneda
    if (['CLP', 'COP', 'ARS'].includes(currencyCode)) {
        // Sin decimales
        return `${currencyInfo.symbol}${Math.round(price).toLocaleString('es-AR')}`;
    } else {
        // Con decimales
        return `${currencyInfo.symbol}${price.toFixed(2)}`;
    }
}

/**
 * Actualiza todos los precios en la página
 */
async function updateAllPrices() {
    const countryCode = await detectUserCountry();
    const currencyInfo = SUPPORTED_CURRENCIES[countryCode] || SUPPORTED_CURRENCIES.DEFAULT;
    
    // Guardar info de moneda en localStorage para uso posterior
    localStorage.setItem('user_currency', JSON.stringify(currencyInfo));
    
    console.log(`País detectado: ${countryCode}, Moneda: ${currencyInfo.code}`);

    // Actualizar cada plan
    for (const [planName, priceUSD] of Object.entries(BASE_PRICES_USD)) {
        const convertedPrice = await convertPrice(priceUSD, currencyInfo.code);
        const formattedPrice = formatPrice(convertedPrice, currencyInfo.code);
        
        // Buscar elementos de precio por data-plan
        const priceElements = document.querySelectorAll(`[data-price-plan="${planName}"]`);
        priceElements.forEach(element => {
            element.textContent = formattedPrice;
        });

        // También actualizar precios en formato "XX.XX/mes" o "XX/mes"
        const priceWithPeriod = document.querySelectorAll(`[data-price-with-period="${planName}"]`);
        priceWithPeriod.forEach(element => {
            const period = element.getAttribute('data-period') || 'mes';
            if (priceUSD === 0) {
                element.innerHTML = 'Gratis';
            } else {
                const priceOnly = currencyInfo.code === 'USD' || currencyInfo.code === 'BRL' 
                    ? formatPrice(convertedPrice, currencyInfo.code).replace(/\.\d+$/, '') // Quitar decimales visuales
                    : formatPrice(convertedPrice, currencyInfo.code);
                element.innerHTML = `${priceOnly}<span class="text-lg font-normal">/${period}</span>`;
            }
        });
    }

    // Agregar indicador visual de moneda si es necesario
    if (currencyInfo.code !== 'USD') {
        addCurrencyIndicator(currencyInfo);
    }
}

/**
 * Agrega un indicador visual de la moneda detectada
 */
function addCurrencyIndicator(currencyInfo) {
    const existingIndicator = document.getElementById('currency-indicator');
    if (existingIndicator) {
        existingIndicator.remove();
    }

    const indicator = document.createElement('div');
    indicator.id = 'currency-indicator';
    indicator.className = 'fixed bottom-4 right-4 bg-green-500 text-white px-4 py-2 rounded-full shadow-lg text-sm font-medium z-50';
    indicator.innerHTML = `💰 Precios en ${currencyInfo.code}`;
    
    document.body.appendChild(indicator);

    // Auto-ocultar después de 5 segundos
    setTimeout(() => {
        indicator.style.transition = 'opacity 0.5s';
        indicator.style.opacity = '0';
        setTimeout(() => indicator.remove(), 500);
    }, 5000);
}

/**
 * Obtiene la plataforma de pago recomendada según el país
 */
function getRecommendedPlatform(countryCode) {
    const currencyInfo = SUPPORTED_CURRENCIES[countryCode] || SUPPORTED_CURRENCIES.DEFAULT;
    return currencyInfo.platform;
}

/**
 * Obtiene la información de moneda del usuario desde localStorage
 */
function getUserCurrencyInfo() {
    const stored = localStorage.getItem('user_currency');
    return stored ? JSON.parse(stored) : SUPPORTED_CURRENCIES.DEFAULT;
}

// Exponer funciones globalmente
window.CurrencyHandler = {
    detectUserCountry,
    getExchangeRates,
    convertPrice,
    formatPrice,
    updateAllPrices,
    getRecommendedPlatform,
    getUserCurrencyInfo,
    SUPPORTED_CURRENCIES,
    BASE_PRICES_USD
};

// Auto-inicializar cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', updateAllPrices);
} else {
    updateAllPrices();
}

