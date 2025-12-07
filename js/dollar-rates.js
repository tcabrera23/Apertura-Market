// Argentine dollar rates display
document.addEventListener('DOMContentLoaded', () => {
    // Detect if user is from Argentina (you can enhance this with IP geolocation)
    detectUserCountry();
});

async function detectUserCountry() {
    try {
        // Try to get user location from browser
        // For now, we'll always show it if on dashboard or if localStorage has the preference
        const showDollarRates = localStorage.getItem('showDollarRates');
        
        // Check if we're on dashboard
        const isDashboard = window.location.pathname.includes('dashboard.html');
        
        if (isDashboard && (showDollarRates === 'true' || showDollarRates === null)) {
            // Try IP-based geolocation (free API)
            try {
                const geoResponse = await fetch('https://ipapi.co/json/');
                const geoData = await geoResponse.json();
                
                if (geoData.country_code === 'AR') {
                    localStorage.setItem('showDollarRates', 'true');
                    await fetchAndDisplayDollarRates();
                } else if (showDollarRates === null) {
                    localStorage.setItem('showDollarRates', 'false');
                }
            } catch (e) {
                // If geolocation fails, show for everyone on dashboard
                if (showDollarRates === 'true') {
                    await fetchAndDisplayDollarRates();
                }
            }
        }
    } catch (error) {
        console.log('Error detecting user country:', error);
    }
}

async function fetchAndDisplayDollarRates() {
    try {
        // Fetch dollar rates from API
        const response = await fetch('https://dolarapi.com/v1/dolares');
        const rates = await response.json();
        
        // Get official and blue rates
        const oficial = rates.find(r => r.casa === 'oficial') || rates.find(r => r.nombre === 'Oficial');
        const blue = rates.find(r => r.casa === 'blue') || rates.find(r => r.nombre === 'Blue');
        
        if (oficial || blue) {
            displayDollarWidget(oficial, blue);
        }
    } catch (error) {
        console.error('Error fetching dollar rates:', error);
    }
}

function displayDollarWidget(oficial, blue) {
    // Get the dollar widget container in the dashboard header
    const container = document.getElementById('dollarWidgetContainer');
    if (!container) return;
    
    // Check if widget already exists
    if (document.getElementById('dollarWidget')) return;
    
    // Create widget container
    const widget = document.createElement('div');
    widget.id = 'dollarWidget';
    widget.className = 'flex items-center gap-2 sm:gap-3 px-3 sm:px-4 py-2 bg-gray-100 dark:bg-gray-700 rounded-lg text-xs sm:text-sm';
    
    let html = '<div class="flex items-center gap-2 sm:gap-3">';
    html += '<span class="text-gray-600 dark:text-gray-400 font-medium hidden sm:inline">💵 USD/ARS:</span>';
    html += '<span class="text-gray-600 dark:text-gray-400 font-medium sm:hidden">💵</span>';
    
    if (oficial) {
        html += `
            <div class="flex flex-col">
                <span class="text-[10px] sm:text-xs text-gray-500 dark:text-gray-400">Oficial</span>
                <span class="font-semibold text-gray-900 dark:text-white text-xs sm:text-sm">
                    $${oficial.compra?.toFixed(2) || oficial.venta?.toFixed(2) || 'N/A'}
                </span>
            </div>
        `;
    }
    
    if (blue) {
        html += `
            <div class="flex flex-col">
                <span class="text-[10px] sm:text-xs text-gray-500 dark:text-gray-400">Blue</span>
                <span class="font-semibold text-blue-600 dark:text-blue-400 text-xs sm:text-sm">
                    $${blue.compra?.toFixed(2) || blue.venta?.toFixed(2) || 'N/A'}
                </span>
            </div>
        `;
    }
    
    // Add close button
    html += `
        <button onclick="closeDollarWidget()" class="ml-1 sm:ml-2 p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors" title="Cerrar">
            <svg class="w-3 h-3 sm:w-4 sm:h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
        </button>
    `;
    
    html += '</div>';
    widget.innerHTML = html;
    
    // Append widget to container
    container.appendChild(widget);
}

// Make function available globally
window.closeDollarWidget = function() {
    const widget = document.getElementById('dollarWidget');
    if (widget) {
        widget.remove();
    }
    localStorage.setItem('showDollarRates', 'false');
};

