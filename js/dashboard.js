// BullAnalytics - Enhanced Dashboard JavaScript with Smart Caching

// API Configuration
//const API_BASE_URL = 'http://localhost:8080/api'; // Development
const API_BASE_URL = 'https://api.bullanalytics.io/api'; // Production
// Expose to window for other scripts
window.API_BASE_URL = API_BASE_URL;

// Get auth token
function getAuthToken() {
    return localStorage.getItem('access_token');
}

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
        if (watchlistModal) {
            watchlistModal.classList.add('hidden');
            watchlistModal.classList.remove('flex');
        }
        const nameInput = document.getElementById('watchlistName');
        const searchInput = document.getElementById('assetSearch');
        const searchResults = document.getElementById('searchResults');
        const selectedAssets = document.getElementById('selectedAssets');

        if (nameInput) nameInput.value = '';
        if (searchInput) searchInput.value = '';
        if (searchResults) {
            searchResults.classList.add('hidden');
            searchResults.classList.remove('block');
        }
        if (selectedAssets) {
            selectedAssets.innerHTML = '<p class="text-center text-gray-500 dark:text-gray-400 italic">No hay activos seleccionados</p>';
        }
        selectedAssetsList = [];
        document.body.style.overflow = ''; // Restore scrolling
    }

    if (addWatchlistBtn) {
        addWatchlistBtn.addEventListener('click', () => {
            if (watchlistModal) {
                watchlistModal.classList.remove('hidden');
                watchlistModal.classList.add('flex');
            }
            const nameInput = document.getElementById('watchlistName');
            const searchInput = document.getElementById('assetSearch');
            const searchResults = document.getElementById('searchResults');
            const selectedAssets = document.getElementById('selectedAssets');

            if (nameInput) nameInput.value = '';
            if (searchInput) searchInput.value = '';
            if (searchResults) {
                searchResults.classList.add('hidden');
                searchResults.classList.remove('block');
            }
            if (selectedAssets) {
                selectedAssets.innerHTML = '<p class="text-center text-gray-500 dark:text-gray-400 italic">No hay activos seleccionados</p>';
            }
            selectedAssetsList = [];
            document.body.style.overflow = 'hidden'; // Prevent background scrolling
        });
    }

    if (closeModalBtn) {
        closeModalBtn.addEventListener('click', closeWatchlistModal);
    }

    if (cancelWatchlistBtn) {
        cancelWatchlistBtn.addEventListener('click', closeWatchlistModal);
    }

    // Close modal when clicking outside
    if (watchlistModal) {
        watchlistModal.addEventListener('click', (e) => {
            if (e.target === watchlistModal) {
                closeWatchlistModal();
            }
        });
    }

    // Close modal with Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && !watchlistModal.classList.contains('hidden')) {
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
            searchResults.classList.add('hidden');
            searchResults.classList.remove('block');
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
            searchResults.classList.add('hidden');
            searchResults.classList.remove('block');
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
        searchResults.innerHTML = '<div class="p-4 text-center text-gray-500 dark:text-gray-400">Buscando...</div>';
        searchResults.classList.remove('hidden');
        searchResults.classList.add('block');

        const response = await fetch(`${API_BASE_URL}/search-assets?query=${encodeURIComponent(query)}`);

        if (!response.ok) {
            throw new Error('Error en la búsqueda');
        }

        const results = await response.json();

        if (results.length === 0) {
            searchResults.innerHTML = '<div class="p-4 text-center text-gray-500 dark:text-gray-400">No se encontraron resultados</div>';
            return;
        }

        // Display results
        searchResults.innerHTML = '';
        results.forEach(asset => {
            const item = document.createElement('div');
            item.className = 'p-3 cursor-pointer border-b border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors';
            item.innerHTML = `
                <span class="font-semibold text-gray-900 dark:text-white mr-2">${asset.symbol}</span>
                <span class="text-gray-600 dark:text-gray-400 text-sm">${asset.name}</span>
                <span class="text-gray-400 dark:text-gray-500 text-xs ml-2">${asset.exchange || ''}</span>
            `;
            item.addEventListener('click', () => {
                selectAsset(asset);
                document.getElementById('assetSearch').value = '';
                searchResults.classList.add('hidden');
                searchResults.classList.remove('block');
            });
            searchResults.appendChild(item);
        });

    } catch (error) {
        console.error('Error searching assets:', error);
        searchResults.innerHTML = '<div class="p-4 text-center text-red-500">Error al buscar activos</div>';
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
        container.innerHTML = '<p class="text-center text-gray-500 dark:text-gray-400 italic">No hay activos seleccionados</p>';
        return;
    }

    container.innerHTML = '';
    selectedAssetsList.forEach(asset => {
        const div = document.createElement('div');
        div.className = 'flex justify-between items-center p-3 bg-white dark:bg-gray-700 rounded-lg mb-2 border border-gray-200 dark:border-gray-600';
        div.innerHTML = `
            <div class="flex-1">
                <div class="font-semibold text-gray-900 dark:text-white">${asset.symbol}</div>
                <div class="text-sm text-gray-600 dark:text-gray-400">${asset.name}</div>
            </div>
            <button class="px-3 py-1 bg-red-500 text-white rounded text-sm hover:bg-red-600 transition-colors" onclick="removeAsset('${asset.symbol}')">Eliminar</button>
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

        const token = getAuthToken();
        if (!token) {
            alert('Por favor, inicia sesión para crear listas');
            window.location.href = 'login.html';
            return;
        }

        const requestBody = {
            name: name,
            assets: assetsDict,
            description: ""
        };

        console.log('Request body:', requestBody);
        console.log('API URL:', `${API_BASE_URL}/watchlists`);

        const response = await fetch(`${API_BASE_URL}/watchlists`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
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
        modal.classList.add('hidden');
        modal.classList.remove('flex');
        document.body.style.overflow = '';

        // Reset form
        document.getElementById('watchlistName').value = '';
        document.getElementById('assetSearch').value = '';
        const searchResults = document.getElementById('searchResults');
        searchResults.classList.add('hidden');
        searchResults.classList.remove('block');
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

// Delete watchlist
async function deleteWatchlist(watchlistId, watchlistName) {
    try {
        const token = getAuthToken();
        if (!token) {
            alert('Por favor, inicia sesión para eliminar listas');
            return;
        }
        
        const response = await fetch(`${API_BASE_URL}/watchlists/${watchlistId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Error al eliminar la lista: ${errorText}`);
        }
        
        // Remove tab and content
        const tabButton = document.querySelector(`.tab-button[data-tab="${watchlistName}"]`);
        const tabContent = document.getElementById(`${watchlistName}-tab`);
        
        if (tabButton) tabButton.remove();
        if (tabContent) tabContent.remove();
        
        // Reload watchlists to refresh the list
        await loadCustomWatchlists();
        
        alert(`Lista "${watchlistName}" eliminada exitosamente`);
    } catch (error) {
        console.error('Error deleting watchlist:', error);
        alert('Error al eliminar la lista. Por favor, intenta de nuevo.');
    }
}

// Open edit watchlist modal
function openEditWatchlistModal(watchlistId, watchlistName, watchlistAssets) {
    const modal = document.getElementById('watchlistModal');
    const nameInput = document.getElementById('watchlistName');
    const selectedAssets = document.getElementById('selectedAssets');
    const saveBtn = document.getElementById('saveWatchlistBtn');
    const modalTitle = modal.querySelector('h3');
    
    // Change modal title
    if (modalTitle) {
        modalTitle.textContent = 'Editar Lista';
    }
    
    // Set watchlist name
    if (nameInput) {
        nameInput.value = watchlistName;
        nameInput.setAttribute('data-watchlist-id', watchlistId);
    }
    
    // Load existing assets
    selectedAssetsList = [];
    if (watchlistAssets && Array.isArray(watchlistAssets)) {
        watchlistAssets.forEach(asset => {
            selectedAssetsList.push({
                symbol: asset.ticker || asset.ticker,
                name: asset.asset_name || asset.name || asset.ticker
            });
        });
    }
    updateSelectedAssetsDisplay();
    
    // Change save button text and behavior
    if (saveBtn) {
        saveBtn.textContent = 'Guardar Cambios';
        saveBtn.onclick = async () => {
            await updateWatchlist(watchlistId, nameInput.value.trim(), selectedAssetsList);
        };
    }
    
    // Show modal
    if (modal) {
        modal.classList.remove('hidden');
        modal.classList.add('flex');
        document.body.style.overflow = 'hidden';
    }
}

// Update watchlist
async function updateWatchlist(watchlistId, newName, assets) {
    try {
        if (!newName) {
            alert('Por favor, ingresa un nombre para la lista');
            return;
        }
        
        const token = getAuthToken();
        if (!token) {
            alert('Por favor, inicia sesión para editar listas');
            return;
        }
        
        // Convert assets to dict format
        const assetsDict = {};
        assets.forEach(asset => {
            assetsDict[asset.symbol] = asset.name;
        });
        
        // Update watchlist name (if changed)
        // Note: We'll need to add an update endpoint or handle this differently
        // For now, we'll delete and recreate if name changed, or just update assets
        
        // First, get current watchlist to check if name changed
        const getResponse = await fetch(`${API_BASE_URL}/watchlists`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!getResponse.ok) {
            throw new Error('Error al obtener la lista');
        }
        
        const watchlists = await getResponse.json();
        const currentWatchlist = watchlists.find(w => w.id === watchlistId);
        
        if (!currentWatchlist) {
            throw new Error('Lista no encontrada');
        }
        
        // Update watchlist name if changed
        if (newName !== currentWatchlist.name) {
            const updateResponse = await fetch(`${API_BASE_URL}/watchlists/${watchlistId}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    name: newName
                })
            });
            
            if (!updateResponse.ok) {
                throw new Error('Error al actualizar el nombre de la lista');
            }
        }
        
        // Get current assets
        const currentAssets = (currentWatchlist.watchlist_assets || []).map(a => a.ticker);
        const newAssets = assets.map(a => a.symbol.toUpperCase());
        
        // Find assets to remove
        const assetsToRemove = currentAssets.filter(ticker => !newAssets.includes(ticker));
        const assetsToAdd = assets.filter(asset => !currentAssets.includes(asset.symbol.toUpperCase()));
        
        // Remove assets
        for (const ticker of assetsToRemove) {
            try {
                await fetch(`${API_BASE_URL}/watchlists/${watchlistId}/assets/${ticker}`, {
                    method: 'DELETE',
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
            } catch (e) {
                console.warn('Error deleting asset:', e);
            }
        }
        
        // Add new assets
        for (const asset of assetsToAdd) {
            try {
                await fetch(`${API_BASE_URL}/watchlists/${watchlistId}/assets`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({
                        ticker: asset.symbol,
                        asset_name: asset.name
                    })
                });
            } catch (e) {
                console.warn('Error adding asset:', e);
            }
        }
        
        // Close modal
        const modal = document.getElementById('watchlistModal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
        }
        document.body.style.overflow = '';
        
        // Reset form
        document.getElementById('watchlistName').value = '';
        document.getElementById('watchlistName').removeAttribute('data-watchlist-id');
        document.getElementById('assetSearch').value = '';
        const searchResults = document.getElementById('searchResults');
        searchResults.classList.add('hidden');
        selectedAssetsList = [];
        updateSelectedAssetsDisplay();
        
        // Reset save button
        const saveBtn = document.getElementById('saveWatchlistBtn');
        if (saveBtn) {
            saveBtn.textContent = 'Crear Lista';
            saveBtn.onclick = async () => {
                await saveWatchlist(document.getElementById('watchlistName').value.trim(), selectedAssetsList);
            };
        }
        
        // Reload watchlists
        await loadCustomWatchlists();
        
        alert(`Lista "${newName}" actualizada exitosamente`);
    } catch (error) {
        console.error('Error updating watchlist:', error);
        // Silently handle errors - the update might have partially succeeded
        // Only show error if it's a critical failure
        if (error.message && !error.message.includes('500')) {
            console.warn('Non-critical error during watchlist update:', error);
        }
        // Reload watchlists anyway to show current state
        await loadCustomWatchlists();
    }
}

async function loadCustomWatchlists() {
    try {
        const token = getAuthToken();
        if (!token) {
            console.log('No token available, skipping watchlists load');
            return; // Don't load watchlists if not authenticated
        }

        console.log('Loading watchlists with token...');
        const response = await fetch(`${API_BASE_URL}/watchlists`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            if (response.status === 401) {
                console.log('Unauthorized, skipping watchlists load');
                return; // Not authenticated, skip loading watchlists
            }
            const errorText = await response.text();
            console.error('Error loading watchlists:', response.status, errorText);
            throw new Error('Error al cargar listas');
        }

        const watchlists = await response.json();
        console.log('Watchlists loaded:', watchlists);
        
        if (!Array.isArray(watchlists) || watchlists.length === 0) {
            console.log('No watchlists found');
            return;
        }
        
        const tabsContainer = document.getElementById('tabsContainer');
        if (!tabsContainer) {
            console.error('Tabs container not found');
            return;
        }

        // Remove existing custom watchlist tabs (keep default ones)
        const defaultTabs = ['tracking', 'portfolio', 'crypto', 'argentina'];
        const existingTabs = Array.from(tabsContainer.querySelectorAll('.tab-button'));
        existingTabs.forEach(tab => {
            const tabName = tab.getAttribute('data-tab');
            if (!defaultTabs.includes(tabName)) {
                tab.remove();
            }
        });

        // Remove existing custom watchlist tab contents (but keep default tabs)
        const existingContents = document.querySelectorAll('.tab-content');
        existingContents.forEach(content => {
            const category = content.getAttribute('data-category');
            if (category && !defaultTabs.includes(category)) {
                content.remove();
            }
        });

        // Add tabs and content for each watchlist
        // watchlists is now an array from Supabase
        watchlists.forEach(watchlist => {
            const watchlistName = watchlist.name;
            const watchlistId = watchlist.id;
            const watchlistAssets = watchlist.watchlist_assets || [];
            
            // Add tab button
            const tabButton = document.createElement('button');
            tabButton.className = 'tab-button';
            tabButton.setAttribute('data-tab', watchlistName);
            tabButton.textContent = watchlistName;
            tabsContainer.appendChild(tabButton);

            // Add tab content
            const tabContent = document.createElement('div');
            tabContent.className = 'tab-content hidden';
            tabContent.id = `${watchlistName}-tab`;
            tabContent.setAttribute('data-category', watchlistName);
            tabContent.setAttribute('data-watchlist-id', watchlistId);

                            tabContent.innerHTML = `
                <div class="flex justify-between items-center mb-6">
                    <h2 class="text-2xl font-bold text-gray-900 dark:text-white">${watchlistName}</h2>
                    <div class="flex items-center gap-2">
                        <button class="edit-watchlist-btn flex items-center justify-center w-10 h-10 rounded-lg bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-blue-50 dark:hover:bg-blue-900/20 hover:text-blue-600 dark:hover:text-blue-400 hover:border-blue-300 dark:hover:border-blue-600 transition-all shadow-sm hover:shadow-md" data-watchlist-id="${watchlistId}" data-watchlist-name="${watchlistName}" title="Editar lista">
                            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" fill="currentColor"/>
                            </svg>
                        </button>
                        <button class="flex items-center justify-center w-10 h-10 rounded-lg bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-green-50 dark:hover:bg-gray-700 hover:text-green-600 dark:hover:text-green-400 hover:border-green-300 dark:hover:border-green-600 transition-all shadow-sm hover:shadow-md" data-config="${watchlistName}" title="Configurar vista">
                            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg" class="hover:rotate-90 transition-transform duration-300">
                                <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z" fill="currentColor"/>
                            </svg>
                        </button>
                        <button class="delete-watchlist-btn flex items-center justify-center w-10 h-10 rounded-lg bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-red-50 dark:hover:bg-red-900/20 hover:text-red-600 dark:hover:text-red-400 hover:border-red-300 dark:hover:border-red-600 transition-all shadow-sm hover:shadow-md" data-watchlist-id="${watchlistId}" data-watchlist-name="${watchlistName}" title="Eliminar lista">
                            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M6 6L14 14M6 14L14 6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                            </svg>
                        </button>
                    </div>
                </div>
                <div class="flex flex-col items-center justify-center py-16 bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700" id="${watchlistName}-loading">
                    <div class="w-12 h-12 border-4 border-gray-200 dark:border-gray-700 border-t-green-500 rounded-full animate-spin"></div>
                    <p class="mt-4 text-gray-600 dark:text-gray-400">Cargando datos...</p>
                </div>
                <div class="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 overflow-hidden" id="${watchlistName}-table" style="display: none;">
                    <div class="overflow-x-auto">
                        <table class="w-full">
                            <thead class="bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-700 dark:to-gray-800">
                                <tr>
                                    <th class="px-4 py-3 text-left text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider cursor-pointer hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors sortable" data-sort="name">Activo <span class="sort-icon"></span></th>
                                    <th class="px-4 py-3 text-left text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider cursor-pointer hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors sortable" data-sort="price">Precio <span class="sort-icon"></span></th>
                                    <th class="px-4 py-3 text-left text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider cursor-pointer hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors sortable" data-sort="daily_change_percent">Var. Diaria <span class="sort-icon"></span></th>
                                    <th class="px-4 py-3 text-left text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider cursor-pointer hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors sortable" data-sort="dividend_yield">Dividendos <span class="sort-icon"></span></th>
                                    <th class="px-4 py-3 text-left text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider cursor-pointer hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors sortable" data-sort="sma_50">SMA 50 <span class="sort-icon"></span></th>
                                    <th class="px-4 py-3 text-left text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider cursor-pointer hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors sortable" data-sort="sma_200">SMA 200 <span class="sort-icon"></span></th>
                                    <th class="px-4 py-3 text-left text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider cursor-pointer hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors sortable" data-sort="pe">P/E <span class="sort-icon"></span></th>
                                    <th class="px-4 py-3 text-left text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider cursor-pointer hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors sortable" data-sort="revenue">Revenue <span class="sort-icon"></span></th>
                                    <th class="px-4 py-3 text-left text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider cursor-pointer hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors sortable" data-sort="revenue_growth">Rev. Growth <span class="sort-icon"></span></th>
                                    <th class="px-4 py-3 text-left text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider cursor-pointer hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors sortable" data-sort="profit_margin">Profit Margin <span class="sort-icon"></span></th>
                                    <th class="px-4 py-3 text-left text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider cursor-pointer hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors sortable" data-sort="roe">ROE <span class="sort-icon"></span></th>
                                    <th class="px-4 py-3 text-left text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider cursor-pointer hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors sortable" data-sort="debt_to_equity">Debt/Equity <span class="sort-icon"></span></th>
                                    <th class="px-4 py-3 text-left text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider cursor-pointer hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors sortable" data-sort="price_to_book">P/B <span class="sort-icon"></span></th>
                                    <th class="px-4 py-3 text-left text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider cursor-pointer hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors sortable" data-sort="beta">Beta <span class="sort-icon"></span></th>
                                    <th class="px-4 py-3 text-left text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider cursor-pointer hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors sortable" data-sort="volume">Volumen <span class="sort-icon"></span></th>
                                    <th class="px-4 py-3 text-left text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider cursor-pointer hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors sortable" data-sort="rsi">RSI <span class="sort-icon"></span></th>
                                    <th class="px-4 py-3 text-left text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider cursor-pointer hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors sortable" data-sort="diff">Diferencia vs. Máx <span class="sort-icon"></span></th>
                                </tr>
                            </thead>
                            <tbody id="${watchlistName}-tbody" class="divide-y divide-gray-200 dark:divide-gray-700"></tbody>
                        </table>
                    </div>
                </div>
                <!-- Analysis Charts for ${watchlistName} -->
                <div id="${watchlistName}-charts-container" class="mt-8"></div>
            `;

            // Insert tab content in the main container (same level as other tabs)
            const mainContainer = document.querySelector('main > div.max-w-7xl');
            if (mainContainer) {
                mainContainer.appendChild(tabContent);
            } else {
                // Fallback: find the container that holds other tab contents
                const firstTab = document.getElementById('tracking-tab');
                if (firstTab && firstTab.parentElement) {
                    firstTab.parentElement.appendChild(tabContent);
                }
            }

            // Add click handler for the new tab
            tabButton.addEventListener('click', () => {
                const tabName = tabButton.getAttribute('data-tab');

                // Remove active class from all buttons and contents
                document.querySelectorAll('.tab-button').forEach(btn => {
                    btn.classList.remove('bg-gradient-to-b', 'from-green-50', 'dark:from-green-900/20', 'text-green-600', 'dark:text-green-400', 'border-b-2', 'border-green-500', 'dark:border-green-400');
                    btn.classList.add('text-gray-600', 'dark:text-gray-400');
                });
                document.querySelectorAll('.tab-content').forEach(content => {
                    content.classList.add('hidden');
                    content.classList.remove('block');
                });

                // Add active class to clicked button and corresponding content
                tabButton.classList.remove('text-gray-600', 'dark:text-gray-400');
                tabButton.classList.add('bg-gradient-to-b', 'from-green-50', 'dark:from-green-900/20', 'text-green-600', 'dark:text-green-400', 'border-b-2', 'border-green-500', 'dark:border-green-400');
                const tabContentEl = document.getElementById(`${tabName}-tab`);
                tabContentEl.classList.remove('hidden');
                tabContentEl.classList.add('block');

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
            
            // Add edit watchlist button handler
            const editBtn = tabContent.querySelector('.edit-watchlist-btn');
            if (editBtn) {
                editBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    const btn = e.currentTarget;
                    const wlId = btn.getAttribute('data-watchlist-id');
                    const wlName = btn.getAttribute('data-watchlist-name');
                    console.log('Edit button clicked:', wlId, wlName, watchlistAssets);
                    if (wlId && wlName) {
                        openEditWatchlistModal(wlId, wlName, watchlistAssets || []);
                    } else {
                        console.error('Missing watchlist ID or name:', { wlId, wlName });
                    }
                });
            } else {
                console.warn('Edit button not found for watchlist:', watchlistName);
            }
            
            // Add delete watchlist button handler
            const deleteBtn = tabContent.querySelector('.delete-watchlist-btn');
            if (deleteBtn) {
                deleteBtn.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    const btn = e.currentTarget;
                    const wlId = btn.getAttribute('data-watchlist-id');
                    const wlName = btn.getAttribute('data-watchlist-name');
                    console.log('Delete button clicked:', wlId, wlName);
                    if (wlId && wlName) {
                        if (confirm(`¿Estás seguro de que deseas eliminar la lista "${wlName}"?`)) {
                            deleteWatchlist(wlId, wlName);
                        }
                    } else {
                        console.error('Missing watchlist ID or name for delete:', { wlId, wlName });
                    }
                });
            } else {
                console.warn('Delete button not found for watchlist:', watchlistName);
            }
        });

        // Re-initialize tabs to include new ones, but preserve current active tab
        const currentActiveTab = document.querySelector('.tab-button.bg-gradient-to-b');
        const currentActiveTabName = currentActiveTab ? currentActiveTab.getAttribute('data-tab') : 'tracking';

        // Re-initialize tabs
        initializeTabs();

        // Update analysis category selector if it exists
        if (typeof updateCategorySelector === 'function') {
            updateCategorySelector();
        }

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

    // Set first tab (tracking) as active by default
    const firstTab = document.querySelector('.tab-button[data-tab="tracking"]');
    if (firstTab) {
        firstTab.classList.remove('text-gray-600', 'dark:text-gray-400');
        firstTab.classList.add('bg-gradient-to-b', 'from-green-50', 'dark:from-green-900/20', 'text-green-600', 'dark:text-green-400', 'border-b-2', 'border-green-500', 'dark:border-green-400');
    }

    // Hide all tab contents except tracking
    document.querySelectorAll('.tab-content').forEach(content => {
        const tabId = content.id;
        if (tabId === 'tracking-tab') {
            content.classList.remove('hidden');
            content.classList.add('block');
        } else {
            content.classList.add('hidden');
            content.classList.remove('block');
        }
    });

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.getAttribute('data-tab');

            // Remove active class from all buttons and contents
            tabButtons.forEach(btn => {
                btn.classList.remove('bg-gradient-to-b', 'from-green-50', 'dark:from-green-900/20', 'text-green-600', 'dark:text-green-400', 'border-b-2', 'border-green-500', 'dark:border-green-400');
                btn.classList.add('text-gray-600', 'dark:text-gray-400');
            });
            // Hide all tab contents
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.add('hidden');
                content.classList.remove('block');
            });

            // Add active class to clicked button and corresponding content
            button.classList.remove('text-gray-600', 'dark:text-gray-400');
            button.classList.add('bg-gradient-to-b', 'from-green-50', 'dark:from-green-900/20', 'text-green-600', 'dark:text-green-400', 'border-b-2', 'border-green-500', 'dark:border-green-400');
            const tabContent = document.getElementById(`${tabName}-tab`);
            if (tabContent) {
                tabContent.classList.remove('hidden');
                tabContent.classList.add('block');
                // Data should already be loaded from preload
                const category = tabContent.getAttribute('data-category');
                if (category && !currentData[category]) {
                    loadAssets(category, false);
                }
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
        if (loadingEl) loadingEl.style.display = 'flex';
        if (tableEl) tableEl.style.display = 'none';
    }

    try {
        let endpoint;
        let headers = {};
        
        if (isCustomWatchlist) {
            // For custom watchlists, get watchlist ID and fetch assets data
            const token = getAuthToken();
            if (!token) {
                throw new Error('Authentication required');
            }
            headers['Authorization'] = `Bearer ${token}`;
            
            // Find watchlist by name
            const watchlistTab = document.querySelector(`[data-category="${category}"]`);
            const watchlistId = watchlistTab ? watchlistTab.getAttribute('data-watchlist-id') : null;
            
            if (!watchlistId) {
                throw new Error('Watchlist ID not found');
            }
            
            endpoint = `${API_BASE_URL}/watchlists/${watchlistId}/assets-data`;
        } else {
            endpoint = `${API_BASE_URL}/${category}-assets`;
        }

        const response = await fetch(endpoint, { headers });

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

    // Apply table configuration if available
    if (typeof getTableConfig === 'function' && typeof applyTableConfiguration === 'function') {
        const config = getTableConfig(category);
        applyTableConfiguration(category, config);
    }

    // Show table, hide loading
    if (loadingEl) {
        loadingEl.style.display = 'none';
    }
    if (tableEl) {
        tableEl.style.display = 'block';
    }

    // Render analysis charts below the table
    const renderCharts = () => {
        if (typeof window.renderAnalysisCharts === 'function') {
            console.log(`Rendering charts for ${category} with ${data.length} assets`);
            window.renderAnalysisCharts(category, data);
        } else {
            // Retry if function not available yet
            console.warn(`renderAnalysisCharts not available for ${category}, retrying...`);
            setTimeout(renderCharts, 200);
        }
    };
    setTimeout(renderCharts, 100);
}

// Create table row from asset data
function createTableRow(asset, isCrypto = false) {
    const row = document.createElement('tr');
    row.className = 'hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors';
    row.setAttribute('data-name', asset.name);
    row.setAttribute('data-price', asset.price || 0);
    row.setAttribute('data-daily_change_percent', asset.daily_change_percent || 0);
    row.setAttribute('data-daily_change', asset.daily_change || 0);
    row.setAttribute('data-dividend_yield', asset.dividend_yield || 0);
    row.setAttribute('data-sma_50', asset.sma_50 || 0);
    row.setAttribute('data-sma_200', asset.sma_200 || 0);
    row.setAttribute('data-pe', asset.pe_ratio || 0);
    row.setAttribute('data-revenue', asset.revenue || 0);
    row.setAttribute('data-revenue_growth', asset.revenue_growth || 0);
    row.setAttribute('data-profit_margin', asset.profit_margin || 0);
    row.setAttribute('data-roe', asset.return_on_equity || 0);
    row.setAttribute('data-debt_to_equity', asset.debt_to_equity || 0);
    row.setAttribute('data-price_to_book', asset.price_to_book || 0);
    row.setAttribute('data-beta', asset.beta || 0);
    row.setAttribute('data-volume', asset.volume || 0);
    row.setAttribute('data-rsi', asset.rsi || 0);
    row.setAttribute('data-diff', asset.diff_from_max || 0);
    row.setAttribute('data-market_cap', asset.market_cap || 0);
    row.setAttribute('data-max', asset.all_time_high || 0);

    // Helper function to create a cell
    const createCell = (value, formatter = null, colorClass = null, columnKey = null) => {
        const cell = document.createElement('td');
        cell.className = 'px-4 py-3 text-sm text-gray-600 dark:text-gray-400';
        if (colorClass) cell.className += ' ' + colorClass;
        if (columnKey) cell.setAttribute('data-column', columnKey);

        if (value === null || value === undefined) {
            cell.textContent = 'N/A';
        } else if (formatter) {
            cell.textContent = formatter(value);
        } else {
            cell.textContent = value;
        }
        return cell;
    };

    // Asset name with logo
    const nameCell = document.createElement('td');
    nameCell.className = 'px-4 py-3 font-semibold text-gray-900 dark:text-white';
    nameCell.setAttribute('data-column', 'name');

    const nameContainer = document.createElement('div');
    nameContainer.className = 'flex items-center gap-3';

    // Add logo
    const logoImg = document.createElement('img');
    logoImg.alt = asset.name;
    logoImg.className = 'w-8 h-8 rounded-full object-cover flex-shrink-0';

    // Determine logo source based on asset type
    if (asset.logo_url) {
        // Use provided logo URL if available
        logoImg.src = asset.logo_url;
    } else if (isCrypto) {
        // For crypto, use CoinCap API
        const cryptoSymbol = (asset.ticker || asset.symbol || '').replace('-USD', '').toLowerCase();
        logoImg.src = `https://assets.coincap.io/assets/icons/${cryptoSymbol}@2x.png`;
    } else {
        // For stocks, use Clearbit Logo API
        const ticker = (asset.ticker || asset.symbol || '').toLowerCase();
        // Map common tickers to their domains
        const domainMap = {
            'amzn': 'amazon.com',
            'aapl': 'apple.com',
            'googl': 'google.com',
            'goog': 'google.com',
            'msft': 'microsoft.com',
            'meta': 'meta.com',
            'tsla': 'tesla.com',
            'nvda': 'nvidia.com',
            'nflx': 'netflix.com',
            'adbe': 'adobe.com',
            'crm': 'salesforce.com',
            'orcl': 'oracle.com',
            'intc': 'intel.com',
            'amd': 'amd.com',
            'qcom': 'qualcomm.com',
            'pypl': 'paypal.com',
            'v': 'visa.com',
            'ma': 'mastercard.com',
            'ko': 'coca-cola.com',
            'pep': 'pepsico.com',
            'wmt': 'walmart.com',
            'dis': 'disney.com',
            'nke': 'nike.com',
            'mcd': 'mcdonalds.com',
            'sbux': 'starbucks.com',
            'ba': 'boeing.com',
            'ibm': 'ibm.com',
            'csco': 'cisco.com'
        };

        const domain = domainMap[ticker] || `${ticker}.com`;
        logoImg.src = `https://logo.clearbit.com/${domain}`;
    }

    // Improved logo fallback system
    logoImg.onerror = function () {
        // Try alternative logo sources
        const ticker = (asset.ticker || asset.symbol || '').toUpperCase();
        
        // Try Yahoo Finance logo API
        if (!isCrypto) {
            this.src = `https://logo.clearbit.com/${ticker.toLowerCase()}.com`;
            this.onerror = function() {
                // Try finnhub logo
                this.src = `https://finnhub.io/api/logo?symbol=${ticker}`;
                this.onerror = function() {
                    // Try another fallback - use first letter as placeholder
                    this.style.display = 'none';
                    // Create a placeholder div with initial
                    const placeholder = document.createElement('div');
                    placeholder.className = 'w-8 h-8 rounded-full flex items-center justify-center text-white font-bold text-sm flex-shrink-0';
                    placeholder.style.backgroundColor = '#6B7280';
                    placeholder.textContent = ticker.charAt(0);
                    if (nameContainer.firstChild === logoImg) {
                        nameContainer.replaceChild(placeholder, logoImg);
                    }
                };
            };
        } else {
            // For crypto, try alternative sources
            const cryptoSymbol = ticker.replace('-USD', '').toLowerCase();
            this.src = `https://cryptoicons.org/api/icon/${cryptoSymbol}/200`;
            this.onerror = function() {
                this.style.display = 'none';
                const placeholder = document.createElement('div');
                placeholder.className = 'w-8 h-8 rounded-full flex items-center justify-center text-white font-bold text-sm flex-shrink-0';
                placeholder.style.backgroundColor = '#6B7280';
                placeholder.textContent = cryptoSymbol.charAt(0).toUpperCase();
                if (nameContainer.firstChild === logoImg) {
                    nameContainer.replaceChild(placeholder, logoImg);
                }
            };
        }
    };

    nameContainer.appendChild(logoImg);

    const nameText = document.createElement('span');
    nameText.textContent = asset.name;
    nameContainer.appendChild(nameText);

    nameCell.appendChild(nameContainer);
    row.appendChild(nameCell);

    // Current price
    row.appendChild(createCell(asset.price, formatCurrency, 'font-semibold text-gray-700 dark:text-gray-300', 'price'));

    if (isCrypto) {
        // Crypto columns: Market Cap, Volume, Max, Diff, Daily Change %
        row.appendChild(createCell(asset.market_cap, formatLargeNumber, null, 'market_cap'));
        row.appendChild(createCell(asset.volume, formatNumber, null, 'volume'));
        row.appendChild(createCell(asset.all_time_high, formatCurrency, null, 'max'));

        // Difference from max for crypto
        const diffCellCrypto = document.createElement('td');
        diffCellCrypto.className = 'px-4 py-3 font-semibold';
        diffCellCrypto.setAttribute('data-column', 'diff');
        if (asset.diff_from_max >= -0.001) {
            diffCellCrypto.className += ' text-green-500 dark:text-green-400';
            diffCellCrypto.innerHTML = '✅ En Máx';
        } else {
            diffCellCrypto.className += ' text-red-500 dark:text-red-400';
            diffCellCrypto.innerHTML = `📉 ${formatPercentage(asset.diff_from_max)}`;
        }
        row.appendChild(diffCellCrypto);

        // Daily variation % for crypto
        const dailyChangeCellCrypto = document.createElement('td');
        dailyChangeCellCrypto.className = 'px-4 py-3 text-sm font-semibold';
        dailyChangeCellCrypto.setAttribute('data-column', 'daily_change_percent');
        if (asset.daily_change_percent !== null && asset.daily_change_percent !== undefined) {
            const dailyChange = asset.daily_change_percent;
            if (dailyChange >= 0) {
                dailyChangeCellCrypto.className += ' text-green-600 dark:text-green-400';
                dailyChangeCellCrypto.innerHTML = `▲ ${(dailyChange * 100).toFixed(2)}%`;
            } else {
                dailyChangeCellCrypto.className += ' text-red-600 dark:text-red-400';
                dailyChangeCellCrypto.innerHTML = `▼ ${(Math.abs(dailyChange) * 100).toFixed(2)}%`;
            }
        } else {
            dailyChangeCellCrypto.className += ' text-gray-400';
            dailyChangeCellCrypto.textContent = 'N/A';
        }
        row.appendChild(dailyChangeCellCrypto);
    } else {
        // Stock columns: P/E, Revenue, Revenue Growth, Profit Margin, ROE, Debt/Equity, P/B, Beta, Volume, RSI, Diff
        row.appendChild(createCell(asset.pe_ratio, (v) => v.toFixed(2), null, 'pe'));
        row.appendChild(createCell(asset.revenue, formatLargeNumber, null, 'revenue'));

        // Revenue Growth with color coding
        const revGrowthCell = createCell(asset.revenue_growth, (v) => (v * 100).toFixed(2) + '%', null, 'revenue_growth');
        if (asset.revenue_growth !== null && asset.revenue_growth > 0) {
            revGrowthCell.className += ' text-green-500 dark:text-green-400';
        } else if (asset.revenue_growth !== null && asset.revenue_growth < 0) {
            revGrowthCell.className += ' text-red-500 dark:text-red-400';
        }
        row.appendChild(revGrowthCell);

        // Profit Margin
        const profitMarginCell = createCell(asset.profit_margin, (v) => (v * 100).toFixed(2) + '%', null, 'profit_margin');
        if (asset.profit_margin !== null && asset.profit_margin > 0.1) {
            profitMarginCell.className += ' text-green-500 dark:text-green-400';
        } else if (asset.profit_margin !== null && asset.profit_margin < 0) {
            profitMarginCell.className += ' text-red-500 dark:text-red-400';
        }
        row.appendChild(profitMarginCell);

        // ROE with color coding
        const roeCell = createCell(asset.return_on_equity, (v) => (v * 100).toFixed(2) + '%', null, 'roe');
        if (asset.return_on_equity !== null && asset.return_on_equity > 0.15) {
            roeCell.className += ' text-green-500 dark:text-green-400';
        } else if (asset.return_on_equity !== null && asset.return_on_equity < 0) {
            roeCell.className += ' text-red-500 dark:text-red-400';
        }
        row.appendChild(roeCell);

        // Debt/Equity
        row.appendChild(createCell(asset.debt_to_equity, (v) => v.toFixed(2), null, 'debt_to_equity'));

        // P/B
        row.appendChild(createCell(asset.price_to_book, (v) => v.toFixed(2), null, 'price_to_book'));

        // Beta
        const betaCell = createCell(asset.beta, (v) => v.toFixed(2), null, 'beta');
        if (asset.beta !== null) {
            if (asset.beta > 1.5) {
                betaCell.className += ' text-red-500 dark:text-red-400';
            } else if (asset.beta < 0.8) {
                betaCell.className += ' text-green-500 dark:text-green-400';
            }
        }
        row.appendChild(betaCell);

        // Volume
        row.appendChild(createCell(asset.volume, formatNumber, null, 'volume'));

        // RSI with color coding
        const rsiCell = createCell(asset.rsi, (v) => v.toFixed(2), null, 'rsi');
        if (asset.rsi !== null) {
            if (asset.rsi > 70) {
                rsiCell.className += ' text-red-500 dark:text-red-400';
            } else if (asset.rsi < 30) {
                rsiCell.className += ' text-green-500 dark:text-green-400';
            }
        }
        row.appendChild(rsiCell);

        // Difference from max
        const diffCell = document.createElement('td');
        diffCell.className = 'px-4 py-3 font-semibold';
        diffCell.setAttribute('data-column', 'diff');
        if (asset.diff_from_max >= -0.001) {
            diffCell.className += ' text-green-500 dark:text-green-400';
            diffCell.innerHTML = '✅ En Máx';
        } else {
            diffCell.className += ' text-red-500 dark:text-red-400';
            diffCell.innerHTML = `📉 ${formatPercentage(asset.diff_from_max)}`;
        }
        row.appendChild(diffCell);

        // Daily variation % (percentage)
        const dailyChangePercentCell = document.createElement('td');
        dailyChangePercentCell.className = 'px-4 py-3 text-sm font-semibold';
        dailyChangePercentCell.setAttribute('data-column', 'daily_change_percent');
        if (asset.daily_change_percent !== null && asset.daily_change_percent !== undefined) {
            const dailyChangePercent = asset.daily_change_percent;
            if (dailyChangePercent >= 0) {
                dailyChangePercentCell.className += ' text-green-600 dark:text-green-400';
                dailyChangePercentCell.innerHTML = `▲ ${(dailyChangePercent * 100).toFixed(2)}%`;
            } else {
                dailyChangePercentCell.className += ' text-red-600 dark:text-red-400';
                dailyChangePercentCell.innerHTML = `▼ ${(Math.abs(dailyChangePercent) * 100).toFixed(2)}%`;
            }
        } else {
            dailyChangePercentCell.className += ' text-gray-400';
            dailyChangePercentCell.textContent = 'N/A';
        }
        row.appendChild(dailyChangePercentCell);

        // Daily variation $ (absolute value)
        const dailyChangeAbsCell = document.createElement('td');
        dailyChangeAbsCell.className = 'px-4 py-3 text-sm font-semibold';
        dailyChangeAbsCell.setAttribute('data-column', 'daily_change');
        if (asset.daily_change !== null && asset.daily_change !== undefined) {
            const dailyChangeAbs = asset.daily_change;
            if (dailyChangeAbs >= 0) {
                dailyChangeAbsCell.className += ' text-green-600 dark:text-green-400';
                dailyChangeAbsCell.innerHTML = `▲ $${dailyChangeAbs.toFixed(2)}`;
            } else {
                dailyChangeAbsCell.className += ' text-red-600 dark:text-red-400';
                dailyChangeAbsCell.innerHTML = `▼ $${Math.abs(dailyChangeAbs).toFixed(2)}`;
            }
        } else {
            dailyChangeAbsCell.className += ' text-gray-400';
            dailyChangeAbsCell.textContent = 'N/A';
        }
        row.appendChild(dailyChangeAbsCell);

        // Dividendos (Dividend Yield)
        const dividendCell = document.createElement('td');
        dividendCell.className = 'px-4 py-3 text-sm';
        dividendCell.setAttribute('data-column', 'dividend_yield');
        if (asset.dividend_yield !== null && asset.dividend_yield !== undefined && asset.dividend_yield > 0) {
            dividendCell.className += ' text-gray-700 dark:text-gray-300 font-medium';
            dividendCell.textContent = `${(asset.dividend_yield * 100).toFixed(2)}%`;
        } else {
            dividendCell.className += ' text-gray-400';
            dividendCell.textContent = '-';
        }
        row.appendChild(dividendCell);

        // SMA 50
        row.appendChild(createCell(asset.sma_50, (v) => v ? `$${v.toFixed(2)}` : 'N/A', null, 'sma_50'));

        // SMA 200
        row.appendChild(createCell(asset.sma_200, (v) => v ? `$${v.toFixed(2)}` : 'N/A', null, 'sma_200'));
    }

    return row;
}

// Helper function to format large numbers (billions, millions)
function formatLargeNumber(num) {
    if (num >= 1e12) {
        return `$${(num / 1e12).toFixed(2)}T`;
    } else if (num >= 1e9) {
        return `$${(num / 1e9).toFixed(2)}B`;
    } else if (num >= 1e6) {
        return `$${(num / 1e6).toFixed(2)}M`;
    } else if (num >= 1e3) {
        return `$${(num / 1e3).toFixed(2)}K`;
    }
    return `$${num.toFixed(2)}`;
}

// Helper function to format numbers (for volume)
function formatNumber(num) {
    if (num >= 1e9) {
        return (num / 1e9).toFixed(2) + 'B';
    } else if (num >= 1e6) {
        return (num / 1e6).toFixed(2) + 'M';
    } else if (num >= 1e3) {
        return (num / 1e3).toFixed(2) + 'K';
    }
    return num.toFixed(0);
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
