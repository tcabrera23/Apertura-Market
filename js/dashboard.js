// Apertura Finance - Enhanced Dashboard JavaScript with Smart Caching

// API Configuration
const API_BASE_URL = 'http://localhost:8080/api';

// Smart Cache System
const CACHE_DURATION = 120000; // 2 minutes in milliseconds
const localCache = {
    data: {},
    timestamps: {}
};

// State management
let currentData = {};
let sortState = {};
let backgroundRefreshInterval = null;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    // Set current date
    setCurrentDate();

    // Initialize tabs
    initializeTabs();

    // Preload all data immediately (no loading state)
    preloadAllData();

    // Start background refresh every 2 minutes
    startBackgroundRefresh();

    // Set up refresh buttons
    document.querySelectorAll('[data-refresh]').forEach(btn => {
        btn.addEventListener('click', () => {
            const category = btn.getAttribute('data-refresh');
            forceRefreshAssets(category);
        });
    });

    // Add watchlist button
    document.getElementById('addWatchlistBtn').addEventListener('click', () => {
        document.getElementById('watchlistModal').style.display = 'flex';
    });

    document.getElementById('closeModal').addEventListener('click', () => {
        document.getElementById('watchlistModal').style.display = 'none';
    });
});

// Preload all data on startup
async function preloadAllData() {
    const categories = ['tracking', 'portfolio', 'crypto', 'argentina'];

    // Load all categories in parallel
    await Promise.all(categories.map(category => loadAssets(category, true)));

    console.log('✅ All data preloaded successfully');
}

// Start background refresh
function startBackgroundRefresh() {
    // Refresh every 2 minutes
    backgroundRefreshInterval = setInterval(() => {
        console.log('🔄 Background refresh started...');
        const categories = ['tracking', 'portfolio', 'crypto', 'argentina'];
        categories.forEach(category => {
            if (isCacheExpired(category)) {
                loadAssets(category, true);
            }
        });
    }, CACHE_DURATION);
}

// Check if cache is expired
function isCacheExpired(category) {
    if (!localCache.timestamps[category]) return true;
    return (Date.now() - localCache.timestamps[category]) > CACHE_DURATION;
}

// Force refresh (manual button click)
async function forceRefreshAssets(category) {
    // Clear cache for this category
    delete localCache.data[category];
    delete localCache.timestamps[category];

    // Reload with visual feedback
    const btn = document.querySelector(`[data-refresh="${category}"]`);
    const originalHTML = btn.innerHTML;
    btn.innerHTML = '<svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg" style="animation: spin 1s linear infinite;"><path d="M17 10C17 13.866 13.866 17 10 17C6.134 17 3 13.866 3 10C3 6.134 6.134 3 10 3C12.8 3 15.2 4.8 16.3 7.3" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><path d="M17 3V7H13" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg> Actualizando...';
    btn.disabled = true;

    await loadAssets(category, false);

    btn.innerHTML = originalHTML;
    btn.disabled = false;
}

// Set current date in Spanish format
function setCurrentDate() {
    const months = [
        'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
        'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'
    ];

    const now = new Date();
    const day = now.getDate();
    const month = months[now.getMonth()];
    const year = now.getFullYear();

    document.getElementById('currentDate').textContent = `Datos al ${day} de ${month} de ${year}`;
}

// Initialize tab functionality
function initializeTabs() {
    const tabButtons = document.querySelectorAll('.tab-button');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.getAttribute('data-tab');

            // Remove active class from all buttons and contents
            tabButtons.forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });

            // Add active class to clicked button and corresponding content
            button.classList.add('active');
            const tabContent = document.getElementById(`${tabName}-tab`);
            tabContent.classList.add('active');

            // Data should already be loaded from preload
            const category = tabContent.getAttribute('data-category');
            if (category && !currentData[category]) {
                loadAssets(category, false);
            }
        });
    });
}

// Load assets by category with smart caching
async function loadAssets(category, silent = false) {
    const loadingEl = document.getElementById(`${category}-loading`);
    const tableEl = document.getElementById(`${category}-table`);
    const tableBody = document.getElementById(`${category}-tbody`);

    // Check cache first
    if (localCache.data[category] && !isCacheExpired(category)) {
        // Use cached data immediately
        renderTable(category, localCache.data[category], tableBody, tableEl, loadingEl);
        return;
    }

    // Only show loading state if not silent and no cached data
    if (!silent && !localCache.data[category]) {
        loadingEl.style.display = 'flex';
        tableEl.style.display = 'none';
    }

    try {
        const endpoint = `${API_BASE_URL}/${category}-assets`;
        const response = await fetch(endpoint);

        if (!response.ok) {
            throw new Error('Error al cargar datos');
        }

        const data = await response.json();

        // Update cache
        localCache.data[category] = data;
        localCache.timestamps[category] = Date.now();
        currentData[category] = data;

        // Render table
        renderTable(category, data, tableBody, tableEl, loadingEl);

    } catch (error) {
        console.error(`Error loading ${category} assets:`, error);

        // If we have cached data, keep showing it
        if (localCache.data[category]) {
            console.log(`Using cached data for ${category} due to error`);
            renderTable(category, localCache.data[category], tableBody, tableEl, loadingEl);
        } else if (!silent) {
            loadingEl.innerHTML = `
                <p style="color: #dc3545;">❌ Error al cargar los datos. Por favor, verifica que el servidor esté ejecutándose.</p>
            `;
        }
    }
}

// Render table with data
function renderTable(category, data, tableBody, tableEl, loadingEl) {
    // Clear table body
    tableBody.innerHTML = '';

    // Populate table
    const isCrypto = category === 'crypto';
    data.forEach(asset => {
        const row = createTableRow(asset, isCrypto);
        tableBody.appendChild(row);
    });

    // Set up sorting
    setupSorting(category);

    // Show table, hide loading
    loadingEl.style.display = 'none';
    tableEl.style.display = 'block';
}

// Create table row from asset data
function createTableRow(asset, isCrypto = false) {
    const row = document.createElement('tr');
    row.setAttribute('data-name', asset.name);
    row.setAttribute('data-price', asset.price);
    row.setAttribute('data-pe', asset.pe_ratio || 0);
    row.setAttribute('data-max', asset.all_time_high);
    row.setAttribute('data-diff', asset.diff_from_max);

    // Asset name
    const nameCell = document.createElement('td');
    nameCell.className = 'asset-name';
    nameCell.textContent = asset.name;
    row.appendChild(nameCell);

    // Current price
    const priceCell = document.createElement('td');
    priceCell.className = 'price';
    priceCell.textContent = formatCurrency(asset.price);
    row.appendChild(priceCell);

    // P/E Ratio (skip for crypto)
    if (!isCrypto) {
        const peCell = document.createElement('td');
        peCell.className = 'pe-ratio';
        peCell.textContent = asset.pe_ratio !== null ? asset.pe_ratio.toFixed(2) : 'N/A';
        row.appendChild(peCell);
    }

    // All-time high
    const maxCell = document.createElement('td');
    maxCell.className = 'max-price';
    maxCell.textContent = formatCurrency(asset.all_time_high);
    row.appendChild(maxCell);

    // Difference from max
    const diffCell = document.createElement('td');
    diffCell.className = 'difference';

    if (asset.diff_from_max >= -0.001) {
        diffCell.classList.add('positive');
        diffCell.innerHTML = '✅ ¡En Máximo Histórico!';
    } else {
        diffCell.classList.add('negative');
        diffCell.innerHTML = `📉 ${formatPercentage(asset.diff_from_max)}`;
    }

    row.appendChild(diffCell);

    return row;
}

// Setup table sorting
function setupSorting(category) {
    const table = document.getElementById(`${category}-table`);
    const headers = table.querySelectorAll('th.sortable');

    headers.forEach(header => {
        header.addEventListener('click', () => {
            const sortKey = header.getAttribute('data-sort');
            sortTable(category, sortKey, header);
        });
    });
}

// Sort table
function sortTable(category, sortKey, headerEl) {
    const tbody = document.getElementById(`${category}-tbody`);
    const rows = Array.from(tbody.querySelectorAll('tr'));

    // Determine sort direction
    const currentSort = sortState[category] || {};
    const isAscending = currentSort.key === sortKey ? !currentSort.ascending : true;
    sortState[category] = { key: sortKey, ascending: isAscending };

    // Clear all sort icons
    const table = headerEl.closest('table');
    table.querySelectorAll('.sort-icon').forEach(icon => {
        icon.textContent = '';
        icon.className = 'sort-icon';
    });

    // Set current sort icon
    const sortIcon = headerEl.querySelector('.sort-icon');
    sortIcon.textContent = isAscending ? ' ↑' : ' ↓';
    sortIcon.className = 'sort-icon active';

    // Sort rows
    rows.sort((a, b) => {
        let aVal = a.getAttribute(`data-${sortKey}`);
        let bVal = b.getAttribute(`data-${sortKey}`);

        // Convert to numbers if possible
        const aNum = parseFloat(aVal);
        const bNum = parseFloat(bVal);

        if (!isNaN(aNum) && !isNaN(bNum)) {
            return isAscending ? aNum - bNum : bNum - aNum;
        }

        // String comparison
        aVal = aVal || '';
        bVal = bVal || '';
        return isAscending ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
    });

    // Re-append rows in sorted order
    rows.forEach(row => tbody.appendChild(row));
}

// Format currency
function formatCurrency(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(value);
}

// Format percentage
function formatPercentage(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'percent',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(value);
}

// Add CSS for spinning animation
const style = document.createElement('style');
style.textContent = `
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
`;
document.head.appendChild(style);
