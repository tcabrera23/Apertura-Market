// BullAnalytics - Broker Connections Management

// API Configuration (use from dashboard.js)
const API_BASE_URL = window.API_BASE_URL || 'https://api.bullanalytics.io/api';

// Get auth token
function getAuthToken() {
    return localStorage.getItem('access_token');
}

// Check if user is premium
let isPremiumUser = false;

async function checkPremiumStatus() {
    try {
        const authToken = getAuthToken();
        if (!authToken) return false;

        const response = await fetch(`${API_BASE_URL}/subscriptions/current`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) return false;

        const data = await response.json();
        const planName = data.plan?.name?.toLowerCase() || 'free';
        
        isPremiumUser = planName === 'plus' || planName === 'pro';
        return isPremiumUser;
    } catch (error) {
        console.error('Error checking premium status:', error);
        return false;
    }
}

// Show/hide broker tab based on subscription
async function updateBrokerTabVisibility() {
    const isPremium = await checkPremiumStatus();
    const brokerTabBtn = document.getElementById('brokerTabBtn');
    
    if (brokerTabBtn) {
        brokerTabBtn.style.display = isPremium ? 'block' : 'none';
    }
}

// Initialize broker connections
async function initBrokerConnections() {
    await updateBrokerTabVisibility();
    
    if (!isPremiumUser) {
        console.log('Broker connections feature requires premium subscription');
        return;
    }

    setupBrokerEventListeners();
    await loadBrokerConnections();
}

// Setup event listeners
function setupBrokerEventListeners() {
    const addBrokerBtn = document.getElementById('addBrokerConnectionBtn');
    const closeBrokerModal = document.getElementById('closeBrokerModal');
    const cancelBrokerModal = document.getElementById('cancelBrokerModal');
    const saveBrokerConnection = document.getElementById('saveBrokerConnection');
    const brokerSelect = document.getElementById('brokerSelect');

    if (addBrokerBtn) {
        addBrokerBtn.addEventListener('click', openBrokerModal);
    }

    if (closeBrokerModal) {
        closeBrokerModal.addEventListener('click', closeBrokerModalFunc);
    }

    if (cancelBrokerModal) {
        cancelBrokerModal.addEventListener('click', closeBrokerModalFunc);
    }

    if (saveBrokerConnection) {
        saveBrokerConnection.addEventListener('click', createBrokerConnection);
    }

    if (brokerSelect) {
        brokerSelect.addEventListener('change', handleBrokerSelectChange);
    }
}

// Open broker modal
function openBrokerModal() {
    const modal = document.getElementById('brokerConnectionModal');
    if (modal) {
        modal.classList.remove('hidden');
        // Reset form
        document.getElementById('brokerSelect').value = '';
        document.getElementById('iolCredentials').classList.add('hidden');
        document.getElementById('binanceCredentials').classList.add('hidden');
    }
}

// Close broker modal
function closeBrokerModalFunc() {
    const modal = document.getElementById('brokerConnectionModal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

// Handle broker select change
function handleBrokerSelectChange(e) {
    const selectedBroker = e.target.value;
    const iolCredentials = document.getElementById('iolCredentials');
    const binanceCredentials = document.getElementById('binanceCredentials');

    if (selectedBroker === 'IOL') {
        iolCredentials.classList.remove('hidden');
        binanceCredentials.classList.add('hidden');
    } else if (selectedBroker === 'BINANCE') {
        iolCredentials.classList.add('hidden');
        binanceCredentials.classList.remove('hidden');
    } else {
        iolCredentials.classList.add('hidden');
        binanceCredentials.classList.add('hidden');
    }
}

// Create broker connection
async function createBrokerConnection() {
    const brokerName = document.getElementById('brokerSelect').value;

    if (!brokerName) {
        alert('Por favor selecciona un broker');
        return;
    }

    const authToken = getAuthToken();
    if (!authToken) {
        alert('Debes iniciar sesión');
        window.location.href = 'login.html';
        return;
    }

    let payload = {
        broker_name: brokerName
    };

    if (brokerName === 'IOL') {
        const username = document.getElementById('iolUsername').value;
        const password = document.getElementById('iolPassword').value;

        if (!username || !password) {
            alert('Por favor completa todos los campos');
            return;
        }

        payload.username = username;
        payload.password = password;
        payload.api_key = username; // IOL uses username as api_key internally
    } else if (brokerName === 'BINANCE') {
        const apiKey = document.getElementById('binanceApiKey').value;
        const apiSecret = document.getElementById('binanceApiSecret').value;

        if (!apiKey || !apiSecret) {
            alert('Por favor completa todos los campos');
            return;
        }

        payload.api_key = apiKey;
        payload.api_secret = apiSecret;
    }

    try {
        const saveBrokerBtn = document.getElementById('saveBrokerConnection');
        saveBrokerBtn.disabled = true;
        saveBrokerBtn.textContent = 'Conectando...';

        const response = await fetch(`${API_BASE_URL}/broker-connections`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Error al conectar broker');
        }

        alert('Broker conectado exitosamente!');
        closeBrokerModalFunc();
        await loadBrokerConnections();
    } catch (error) {
        console.error('Error creating broker connection:', error);
        alert(error.message || 'Error al conectar broker');
    } finally {
        const saveBrokerBtn = document.getElementById('saveBrokerConnection');
        saveBrokerBtn.disabled = false;
        saveBrokerBtn.textContent = 'Conectar';
    }
}

// Load broker connections
async function loadBrokerConnections() {
    const authToken = getAuthToken();
    if (!authToken) return;

    const loadingDiv = document.getElementById('broker-loading');
    const connectedBrokersDiv = document.getElementById('connectedBrokersList');

    try {
        if (loadingDiv) loadingDiv.style.display = 'flex';

        const response = await fetch(`${API_BASE_URL}/broker-connections`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error('Error al cargar conexiones');
        }

        const connections = await response.json();

        if (loadingDiv) loadingDiv.style.display = 'none';

        renderBrokerConnections(connections);

        // Load portfolios for all connections
        if (connections.length > 0) {
            await loadAllBrokerPortfolios(connections);
        }
    } catch (error) {
        console.error('Error loading broker connections:', error);
        if (loadingDiv) loadingDiv.style.display = 'none';
        if (connectedBrokersDiv) {
            connectedBrokersDiv.innerHTML = `
                <div class="text-center py-8 text-gray-500 dark:text-gray-400">
                    Error al cargar conexiones: ${error.message}
                </div>
            `;
        }
    }
}

// Render broker connections
function renderBrokerConnections(connections) {
    const connectedBrokersDiv = document.getElementById('connectedBrokersList');
    
    if (!connectedBrokersDiv) return;

    if (connections.length === 0) {
        connectedBrokersDiv.innerHTML = `
            <div class="text-center py-16 bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
                <svg class="w-16 h-16 mx-auto text-gray-400 dark:text-gray-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                </svg>
                <p class="text-gray-600 dark:text-gray-400 mb-4">No tienes brokers conectados</p>
                <button onclick="document.getElementById('addBrokerConnectionBtn').click()" 
                    class="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-gradient-to-r from-green-500 to-green-600 text-white hover:from-green-600 hover:to-green-700 transition-all">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
                    </svg>
                    Conectar Broker
                </button>
            </div>
        `;
        return;
    }

    const html = `
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            ${connections.map(conn => `
                <div class="bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700 p-4">
                    <div class="flex items-center justify-between mb-3">
                        <div class="flex items-center gap-3">
                            <div class="w-10 h-10 rounded-full bg-gradient-to-br from-green-500 to-green-600 flex items-center justify-center text-white font-bold">
                                ${conn.broker_name.substring(0, 2)}
                            </div>
                            <div>
                                <h4 class="font-bold text-gray-900 dark:text-white">${conn.broker_name}</h4>
                                <p class="text-sm text-gray-500 dark:text-gray-400">
                                    ${conn.is_active ? '<span class="text-green-500">● Activo</span>' : '<span class="text-red-500">● Inactivo</span>'}
                                </p>
                            </div>
                        </div>
                        <button onclick="deleteBrokerConnection('${conn.id}')" 
                            class="text-red-500 hover:text-red-700 dark:hover:text-red-400 transition-colors"
                            title="Eliminar conexión">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                            </svg>
                        </button>
                    </div>
                    ${conn.last_synced ? `
                        <p class="text-xs text-gray-500 dark:text-gray-400">
                            Última sincronización: ${new Date(conn.last_synced).toLocaleString('es-AR')}
                        </p>
                    ` : ''}
                    <button onclick="syncBrokerPortfolio('${conn.id}')" 
                        class="mt-3 w-full px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-all text-sm font-semibold">
                        Sincronizar Ahora
                    </button>
                </div>
            `).join('')}
        </div>
    `;

    connectedBrokersDiv.innerHTML = html;
}

// Delete broker connection
window.deleteBrokerConnection = async function(connectionId) {
    if (!confirm('¿Estás seguro de eliminar esta conexión?')) {
        return;
    }

    const authToken = getAuthToken();
    if (!authToken) return;

    try {
        const response = await fetch(`${API_BASE_URL}/broker-connections/${connectionId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error('Error al eliminar conexión');
        }

        alert('Conexión eliminada exitosamente');
        await loadBrokerConnections();
    } catch (error) {
        console.error('Error deleting broker connection:', error);
        alert(error.message || 'Error al eliminar conexión');
    }
};

// Sync broker portfolio
window.syncBrokerPortfolio = async function(connectionId) {
    const authToken = getAuthToken();
    if (!authToken) return;

    try {
        const response = await fetch(`${API_BASE_URL}/broker-connections/${connectionId}/portfolio`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error('Error al sincronizar portafolio');
        }

        const data = await response.json();
        
        // Reload all portfolios to show updated data
        await loadBrokerConnections();
        
        alert('Portafolio sincronizado exitosamente!');
    } catch (error) {
        console.error('Error syncing broker portfolio:', error);
        alert(error.message || 'Error al sincronizar portafolio');
    }
};

// Load all broker portfolios
async function loadAllBrokerPortfolios(connections) {
    const authToken = getAuthToken();
    if (!authToken) return;

    try {
        const portfolioPromises = connections
            .filter(conn => conn.is_active)
            .map(conn => 
                fetch(`${API_BASE_URL}/broker-connections/${conn.id}/portfolio`, {
                    method: 'GET',
                    headers: {
                        'Authorization': `Bearer ${authToken}`,
                        'Content-Type': 'application/json'
                    }
                })
                .then(res => res.ok ? res.json() : null)
                .catch(err => {
                    console.error(`Error loading portfolio for ${conn.broker_name}:`, err);
                    return null;
                })
            );

        const portfolios = await Promise.all(portfolioPromises);
        
        // Combine all portfolios
        const allAssets = portfolios
            .filter(p => p && p.portfolio)
            .flatMap(p => p.portfolio);

        renderBrokerPortfolio(allAssets);
    } catch (error) {
        console.error('Error loading broker portfolios:', error);
    }
}

// Render broker portfolio
function renderBrokerPortfolio(assets) {
    const portfolioContainer = document.getElementById('brokerPortfolioContainer');
    const portfolioTableBody = document.getElementById('brokerPortfolioTableBody');

    if (!portfolioContainer || !portfolioTableBody) return;

    if (assets.length === 0) {
        portfolioContainer.style.display = 'none';
        return;
    }

    portfolioContainer.style.display = 'block';

    const html = assets.map(asset => {
        const profitLossClass = asset.profit_loss >= 0 ? 'text-green-500' : 'text-red-500';
        const profitLossPctClass = asset.profit_loss_pct >= 0 ? 'text-green-500' : 'text-red-500';

        return `
            <tr class="hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                <td class="px-4 py-3">
                    <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-semibold bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200">
                        ${asset.broker}
                    </span>
                </td>
                <td class="px-4 py-3">
                    <div class="font-semibold text-gray-900 dark:text-white">${asset.name}</div>
                    <div class="text-sm text-gray-500 dark:text-gray-400">${asset.ticker}</div>
                </td>
                <td class="px-4 py-3 text-gray-900 dark:text-white">${asset.quantity.toLocaleString('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 8 })}</td>
                <td class="px-4 py-3 text-gray-900 dark:text-white">$${asset.avg_price.toLocaleString('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                <td class="px-4 py-3 text-gray-900 dark:text-white">$${asset.current_price.toLocaleString('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                <td class="px-4 py-3 font-semibold text-gray-900 dark:text-white">$${asset.market_value.toLocaleString('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                <td class="px-4 py-3">
                    <div class="font-semibold ${profitLossClass}">
                        $${asset.profit_loss.toLocaleString('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </div>
                    ${asset.profit_loss_pct !== 0 ? `
                        <div class="text-sm ${profitLossPctClass}">
                            (${asset.profit_loss_pct >= 0 ? '+' : ''}${asset.profit_loss_pct.toFixed(2)}%)
                        </div>
                    ` : ''}
                </td>
            </tr>
        `;
    }).join('');

    portfolioTableBody.innerHTML = html;
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    initBrokerConnections();
});



