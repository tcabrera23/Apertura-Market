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
    const watchlistModal = document.getElementById('watchlistModal');
    const addWatchlistBtn = document.getElementById('addWatchlistBtn');
    const closeModalBtn = document.getElementById('closeModal');
    const cancelWatchlistBtn = document.getElementById('cancelWatchlistBtn');

    function closeWatchlistModal() {
        watchlistModal.style.display = 'none';
        document.getElementById('watchlistName').value = '';
        document.getElementById('assetSearch').value = '';
        document.getElementById('searchResults').style.display = 'none';
        document.getElementById('selectedAssets').innerHTML = '<p class="empty-message">No hay activos seleccionados</p>';
        selectedAssetsList = [];
        document.body.style.overflow = ''; // Restore scrolling
    }

    addWatchlistBtn.addEventListener('click', () => {
        watchlistModal.style.display = 'flex';
        document.getElementById('watchlistName').value = '';
        document.getElementById('assetSearch').value = '';
        document.getElementById('searchResults').style.display = 'none';
        document.getElementById('selectedAssets').innerHTML = '<p class="empty-message">No hay activos seleccionados</p>';
        selectedAssetsList = [];
        document.body.style.overflow = 'hidden'; // Prevent background scrolling
    });

    closeModalBtn.addEventListener('click', closeWatchlistModal);

    cancelWatchlistBtn.addEventListener('click', closeWatchlistModal);

    // Close modal when clicking outside
    watchlistModal.addEventListener('click', (e) => {
        if (e.target === watchlistModal) {
            closeWatchlistModal();
        }
    });

    // Close modal with Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && watchlistModal.style.display === 'flex') {
            closeWatchlistModal();
        }
    });

    // Initialize watchlist functionality
    initializeWatchlistModal();

    // Load custom watchlists
    loadCustomWatchlists();
});

// Watchlist management
let selectedAssetsList = [];
let searchTimeout = null;

function initializeWatchlistModal() {
    const assetSearch = document.getElementById('assetSearch');
    const searchResults = document.getElementById('searchResults');
    const saveBtn = document.getElementById('saveWatchlistBtn');

    // Search with debounce (2 seconds)
    assetSearch.addEventListener('input', (e) => {
        const query = e.target.value.trim();

        // Clear previous timeout
        if (searchTimeout) {
            clearTimeout(searchTimeout);
        }

        // Hide results if query is too short
        if (query.length < 2) {
            searchResults.style.display = 'none';
            return;
        }

        // Set new timeout (2 seconds)
        searchTimeout = setTimeout(() => {
            searchAssets(query);
        }, 2000);
    });

    // Close search results when clicking outside
    document.addEventListener('click', (e) => {
        if (!assetSearch.contains(e.target) && !searchResults.contains(e.target)) {
            searchResults.style.display = 'none';
        }
    });

    // Save watchlist
    saveBtn.addEventListener('click', async (e) => {
        e.preventDefault();
        console.log('Save button clicked');

        const watchlistName = document.getElementById('watchlistName').value.trim();
        console.log('Watchlist name:', watchlistName);
        console.log('Selected assets:', selectedAssetsList);

        if (!watchlistName) {
            alert('Por favor, ingresa un nombre para la lista');
            return;
        }

        if (selectedAssetsList.length === 0) {
            alert('Por favor, selecciona al menos un activo');
            return;
        }

        console.log('Calling saveWatchlist...');
        await saveWatchlist(watchlistName, selectedAssetsList);
    });
}

async function searchAssets(query) {
    const searchResults = document.getElementById('searchResults');

    try {
        searchResults.innerHTML = '<div style="padding: 1rem; text-align: center; color: var(--color-gray);">Buscando...</div>';
        searchResults.style.display = 'block';

        const response = await fetch(`${API_BASE_URL}/search-assets?query=${encodeURIComponent(query)}`);

        if (!response.ok) {
            throw new Error('Error en la búsqueda');
        }

        const results = await response.json();

        if (results.length === 0) {
            searchResults.innerHTML = '<div style="padding: 1rem; text-align: center; color: var(--color-gray);">No se encontraron resultados</div>';
            return;
        }

        // Display results
        searchResults.innerHTML = '';
        results.forEach(asset => {
            const item = document.createElement('div');
            item.className = 'search-result-item';
            item.innerHTML = `
                <span class="search-result-symbol">${asset.symbol}</span>
                <span class="search-result-name">${asset.name}</span>
                <span class="search-result-exchange">${asset.exchange || ''}</span>
            `;
            item.addEventListener('click', () => {
                selectAsset(asset);
                document.getElementById('assetSearch').value = '';
                searchResults.style.display = 'none';
            });
            searchResults.appendChild(item);
        });

    } catch (error) {
        console.error('Error searching assets:', error);
        searchResults.innerHTML = '<div style="padding: 1rem; text-align: center; color: #dc3545;">Error al buscar activos</div>';
    }
}

function selectAsset(asset) {
    // Check if asset is already selected
    if (selectedAssetsList.some(a => a.symbol === asset.symbol)) {
        return;
    }

    selectedAssetsList.push(asset);
    updateSelectedAssetsDisplay();

    // Auto-fill watchlist name if empty
    const nameInput = document.getElementById('watchlistName');
    if (!nameInput.value.trim()) {
        nameInput.value = asset.name;
    }
}

function removeAsset(symbol) {
    selectedAssetsList = selectedAssetsList.filter(a => a.symbol !== symbol);
    updateSelectedAssetsDisplay();
}

function updateSelectedAssetsDisplay() {
    const container = document.getElementById('selectedAssets');

    if (selectedAssetsList.length === 0) {
        container.innerHTML = '<p class="empty-message">No hay activos seleccionados</p>';
        return;
    }

    container.innerHTML = '';
    selectedAssetsList.forEach(asset => {
        const div = document.createElement('div');
        div.className = 'selected-asset';
        div.innerHTML = `
            <div class="selected-asset-info">
                <div class="selected-asset-symbol">${asset.symbol}</div>
                <div class="selected-asset-name">${asset.name}</div>
            </div>
            <button class="btn-remove-asset" onclick="removeAsset('${asset.symbol}')">Eliminar</button>
        `;
        container.appendChild(div);
    });
}

// Make removeAsset available globally
window.removeAsset = removeAsset;

async function saveWatchlist(name, assets) {
    try {
        console.log('saveWatchlist called with:', { name, assets });

        // Convert assets to the format expected by the backend
        const assetsDict = {};
        assets.forEach(asset => {
            assetsDict[asset.symbol] = asset.name;
        });

        const requestBody = {
            name: name,
            assets: assetsDict
        };

        console.log('Request body:', requestBody);
        console.log('API URL:', `${API_BASE_URL}/watchlist`);

        const response = await fetch(`${API_BASE_URL}/watchlist`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });

        console.log('Response status:', response.status);
        console.log('Response ok:', response.ok);

        if (!response.ok) {
            const errorText = await response.text();
            console.error('Error response:', errorText);
            throw new Error(`Error al guardar la lista: ${errorText}`);
        }

        const result = await response.json();
        console.log('Watchlist created successfully:', result);

        // Close modal
        const modal = document.getElementById('watchlistModal');
        modal.style.display = 'none';
        document.body.style.overflow = '';

        // Reset form
        document.getElementById('watchlistName').value = '';
        document.getElementById('assetSearch').value = '';
        document.getElementById('searchResults').style.display = 'none';
        selectedAssetsList = [];
        updateSelectedAssetsDisplay();

        // Reload watchlists
        await loadCustomWatchlists();

        // Show success message
        alert(`Lista "${name}" creada exitosamente`);

    } catch (error) {
        console.error('Error saving watchlist:', error);
        alert('Error al guardar la lista. Por favor, intenta de nuevo.');
    }
}

async function loadCustomWatchlists() {
    try {
        const response = await fetch(`${API_BASE_URL}/watchlists`);

        if (!response.ok) {
            throw new Error('Error al cargar listas');
        }

        const watchlists = await response.json();
        const tabsContainer = document.getElementById('tabsContainer');

        // Remove existing custom watchlist tabs (keep default ones)
        const defaultTabs = ['tracking', 'portfolio', 'crypto', 'argentina'];
        const existingTabs = Array.from(tabsContainer.querySelectorAll('.tab-button'));
        existingTabs.forEach(tab => {
            const tabName = tab.getAttribute('data-tab');
            if (!defaultTabs.includes(tabName)) {
                tab.remove();
            }
        });

        // Remove existing custom watchlist tab contents
        const existingContents = document.querySelectorAll('.tab-content');
        existingContents.forEach(content => {
            const category = content.getAttribute('data-category');
            if (category && !defaultTabs.includes(category)) {
                content.remove();
            }
        });

        // Add tabs and content for each watchlist
        Object.keys(watchlists).forEach(watchlistName => {
            // Add tab button
            const tabButton = document.createElement('button');
            tabButton.className = 'tab-button';
            tabButton.setAttribute('data-tab', watchlistName);
            tabButton.textContent = watchlistName;
            tabsContainer.appendChild(tabButton);

            // Add tab content
            const tabContent = document.createElement('div');
            tabContent.className = 'tab-content';
            tabContent.id = `${watchlistName}-tab`;
            tabContent.setAttribute('data-category', watchlistName);

            tabContent.innerHTML = `
                <div class="section-header">
                    <h2 class="section-title">${watchlistName}</h2>
                    <button class="btn-refresh" data-refresh="${watchlistName}">
                        <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path
                                d="M17 10C17 13.866 13.866 17 10 17C6.134 17 3 13.866 3 10C3 6.134 6.134 3 10 3C12.8 3 15.2 4.8 16.3 7.3"
                                stroke="currentColor" stroke-width="2" stroke-linecap="round" />
                            <path d="M17 3V7H13" stroke="currentColor" stroke-width="2" stroke-linecap="round"
                                stroke-linejoin="round" />
                        </svg>
                        Actualizar
                    </button>
                </div>

                <div class="loading" id="${watchlistName}-loading">
                    <div class="spinner"></div>
                    <p>Cargando datos...</p>
                </div>

                <div class="table-container" id="${watchlistName}-table" style="display: none;">
                    <table class="data-table sortable">
                        <thead>
                            <tr>
                                <th class="sortable" data-sort="name">Activo <span class="sort-icon"></span></th>
                                <th class="sortable" data-sort="price">Precio Actual (USD) <span
                                        class="sort-icon"></span></th>
                                <th class="sortable" data-sort="pe">P/E Ratio <span class="sort-icon"></span></th>
                                <th class="sortable" data-sort="max">Máximo Histórico (USD) <span
                                        class="sort-icon"></span></th>
                                <th class="sortable" data-sort="diff">Diferencia vs. Máximo <span
                                        class="sort-icon"></span></th>
                            </tr>
                        </thead>
                        <tbody id="${watchlistName}-tbody">
                            <!-- Data will be inserted here -->
                        </tbody>
                    </table>
                </div>
            `;

            // Insert before the closing main tag
            const main = document.querySelector('.dashboard-main .container');
            main.appendChild(tabContent);

            // Add click handler for the new tab
            tabButton.addEventListener('click', () => {
                const tabName = tabButton.getAttribute('data-tab');

                // Remove active class from all buttons and contents
                document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(content => {
                    content.classList.remove('active');
                });

                // Add active class to clicked button and corresponding content
                tabButton.classList.add('active');
                const tabContentEl = document.getElementById(`${tabName}-tab`);
                tabContentEl.classList.add('active');

                // Load data if not already loaded
                if (!currentData[tabName]) {
                    loadAssets(tabName, false);
                }
            });

            // Add refresh button handler
            const refreshBtn = tabContent.querySelector(`[data-refresh="${watchlistName}"]`);
            if (refreshBtn) {
                refreshBtn.addEventListener('click', () => {
                    forceRefreshAssets(watchlistName);
                });
            }
        });

        // Re-initialize tabs to include new ones
        initializeTabs();

    } catch (error) {
        console.error('Error loading watchlists:', error);
    }
}

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

    // Check if this is a custom watchlist
    const defaultCategories = ['tracking', 'portfolio', 'crypto', 'argentina'];
    const isCustomWatchlist = !defaultCategories.includes(category);

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
        // Use different endpoint for custom watchlists
        const endpoint = isCustomWatchlist
            ? `${API_BASE_URL}/watchlist/${encodeURIComponent(category)}`
            : `${API_BASE_URL}/${category}-assets`;

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

    // Determine if this is a crypto category or if assets are crypto
    const isCryptoCategory = category === 'crypto';

    // Populate table
    data.forEach(asset => {
        // Check if asset is crypto by ticker pattern (ends with -USD) or if category is crypto
        const isCrypto = isCryptoCategory || (asset.ticker && asset.ticker.includes('-USD'));
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
