// Table Configuration Management

const API_BASE_URL = 'http://localhost:8080/api';

// Column definitions for different table types
const COLUMN_DEFINITIONS = {
    tracking: [
        { key: 'name', label: 'Activo' },
        { key: 'price', label: 'Precio' },
        { key: 'pe', label: 'P/E' },
        { key: 'revenue', label: 'Revenue' },
        { key: 'revenue_growth', label: 'Rev. Growth' },
        { key: 'profit_margin', label: 'Profit Margin' },
        { key: 'roe', label: 'ROE' },
        { key: 'debt_to_equity', label: 'Debt/Equity' },
        { key: 'price_to_book', label: 'P/B' },
        { key: 'beta', label: 'Beta' },
        { key: 'volume', label: 'Volumen' },
        { key: 'rsi', label: 'RSI' },
        { key: 'diff', label: 'Diferencia vs. Máx' }
    ],
    portfolio: [
        { key: 'name', label: 'Activo' },
        { key: 'price', label: 'Precio' },
        { key: 'pe', label: 'P/E' },
        { key: 'revenue', label: 'Revenue' },
        { key: 'revenue_growth', label: 'Rev. Growth' },
        { key: 'profit_margin', label: 'Profit Margin' },
        { key: 'roe', label: 'ROE' },
        { key: 'debt_to_equity', label: 'Debt/Equity' },
        { key: 'price_to_book', label: 'P/B' },
        { key: 'beta', label: 'Beta' },
        { key: 'volume', label: 'Volumen' },
        { key: 'rsi', label: 'RSI' },
        { key: 'diff', label: 'Diferencia vs. Máx' }
    ],
    argentina: [
        { key: 'name', label: 'Activo' },
        { key: 'price', label: 'Precio' },
        { key: 'pe', label: 'P/E' },
        { key: 'revenue', label: 'Revenue' },
        { key: 'revenue_growth', label: 'Rev. Growth' },
        { key: 'profit_margin', label: 'Profit Margin' },
        { key: 'roe', label: 'ROE' },
        { key: 'debt_to_equity', label: 'Debt/Equity' },
        { key: 'price_to_book', label: 'P/B' },
        { key: 'beta', label: 'Beta' },
        { key: 'volume', label: 'Volumen' },
        { key: 'rsi', label: 'RSI' },
        { key: 'diff', label: 'Diferencia vs. Máx' }
    ],
    crypto: [
        { key: 'name', label: 'Activo' },
        { key: 'price', label: 'Precio' },
        { key: 'market_cap', label: 'Market Cap' },
        { key: 'volume', label: 'Volumen' },
        { key: 'max', label: 'Máximo Histórico' },
        { key: 'diff', label: 'Diferencia vs. Máx' }
    ]
};

let currentConfigCategory = null;
let tableConfigs = {};

// Load saved configurations from localStorage
function loadTableConfigs() {
    const saved = localStorage.getItem('tableConfigs');
    if (saved) {
        try {
            tableConfigs = JSON.parse(saved);
        } catch (e) {
            console.error('Error loading table configs:', e);
            tableConfigs = {};
        }
    }
}

// Save configurations to localStorage
function saveTableConfigs() {
    localStorage.setItem('tableConfigs', JSON.stringify(tableConfigs));
}

// Get configuration for a category
function getTableConfig(category) {
    if (!tableConfigs[category]) {
        const columns = COLUMN_DEFINITIONS[category] || COLUMN_DEFINITIONS.tracking;
        tableConfigs[category] = {
            visibleColumns: columns.map(c => c.key),
            defaultSort: { column: 'name', order: 'asc' },
            filters: []
        };
    }
    return tableConfigs[category];
}

// Initialize configuration modal
document.addEventListener('DOMContentLoaded', () => {
    loadTableConfigs();

    // Open config modal
    document.querySelectorAll('[data-config]').forEach(btn => {
        btn.addEventListener('click', () => {
            const category = btn.getAttribute('data-config');
            openConfigModal(category);
        });
    });

    // Close config modal
    const closeBtn = document.getElementById('closeConfigModal');
    if (closeBtn) {
        closeBtn.addEventListener('click', closeConfigModal);
    }

    // Apply configuration
    const applyBtn = document.getElementById('applyConfigBtn');
    if (applyBtn) {
        applyBtn.addEventListener('click', applyConfiguration);
    }

    // Reset configuration
    const resetBtn = document.getElementById('resetConfigBtn');
    if (resetBtn) {
        resetBtn.addEventListener('click', resetConfiguration);
    }

    // Add filter on Enter key
    const filterValue = document.getElementById('filterValue');
    if (filterValue) {
        filterValue.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                addFilter();
            }
        });
    }

    // Re-initialize config buttons for dynamically created watchlists
    const observer = new MutationObserver(() => {
        document.querySelectorAll('[data-config]').forEach(btn => {
            if (!btn.hasAttribute('data-config-listener')) {
                btn.setAttribute('data-config-listener', 'true');
                btn.addEventListener('click', () => {
                    const category = btn.getAttribute('data-config');
                    openConfigModal(category);
                });
            }
        });
    });
    observer.observe(document.body, { childList: true, subtree: true });
});

function openConfigModal(category) {
    currentConfigCategory = category;
    const modal = document.getElementById('configModal');
    const config = getTableConfig(category);
    const columns = COLUMN_DEFINITIONS[category] || COLUMN_DEFINITIONS.tracking;

    // Populate column visibility checkboxes
    const columnVisibility = document.getElementById('columnVisibility');
    columnVisibility.innerHTML = '';
    columns.forEach(col => {
        const isVisible = config.visibleColumns.includes(col.key);
        const checkbox = document.createElement('label');
        checkbox.className = 'flex items-center gap-3 p-2 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg cursor-pointer';
        checkbox.innerHTML = `
            <input type="checkbox" class="w-4 h-4 text-green-600 border-gray-300 rounded focus:ring-green-500" 
                   data-column="${col.key}" ${isVisible ? 'checked' : ''}>
            <span class="text-gray-700 dark:text-gray-300">${col.label}</span>
        `;
        columnVisibility.appendChild(checkbox);
    });

    // Populate sort selectors
    const sortColumn = document.getElementById('defaultSortColumn');
    const sortOrder = document.getElementById('defaultSortOrder');
    sortColumn.innerHTML = '';
    columns.forEach(col => {
        const option = document.createElement('option');
        option.value = col.key;
        option.textContent = col.label;
        if (config.defaultSort.column === col.key) {
            option.selected = true;
        }
        sortColumn.appendChild(option);
    });
    sortOrder.value = config.defaultSort.order;

    // Populate filter column selector
    const filterColumn = document.getElementById('filterColumn');
    filterColumn.innerHTML = '<option value="">Seleccionar columna</option>';
    columns.forEach(col => {
        const option = document.createElement('option');
        option.value = col.key;
        option.textContent = col.label;
        filterColumn.appendChild(option);
    });

    // Show active filters
    updateActiveFilters();

    modal.classList.remove('hidden');
    modal.classList.add('flex');
    document.body.style.overflow = 'hidden';
}

function closeConfigModal() {
    const modal = document.getElementById('configModal');
    modal.classList.add('hidden');
    modal.classList.remove('flex');
    document.body.style.overflow = '';
    currentConfigCategory = null;
}

function applyConfiguration() {
    if (!currentConfigCategory) return;

    const config = getTableConfig(currentConfigCategory);
    const columns = COLUMN_DEFINITIONS[currentConfigCategory] || COLUMN_DEFINITIONS.tracking;

    // Get visible columns
    const checkboxes = document.querySelectorAll('#columnVisibility input[type="checkbox"]');
    config.visibleColumns = Array.from(checkboxes)
        .filter(cb => cb.checked)
        .map(cb => cb.getAttribute('data-column'));

    // Get default sort
    const sortColumn = document.getElementById('defaultSortColumn').value;
    const sortOrder = document.getElementById('defaultSortOrder').value;
    config.defaultSort = { column: sortColumn, order: sortOrder };

    // Save configuration
    tableConfigs[currentConfigCategory] = config;
    saveTableConfigs();

    // Apply to table
    applyTableConfiguration(currentConfigCategory, config);

    closeConfigModal();
}

function resetConfiguration() {
    if (!currentConfigCategory) return;

    const columns = COLUMN_DEFINITIONS[currentConfigCategory] || COLUMN_DEFINITIONS.tracking;
    tableConfigs[currentConfigCategory] = {
        visibleColumns: columns.map(c => c.key),
        defaultSort: { column: 'name', order: 'asc' },
        filters: []
    };
    saveTableConfigs();

    // Reload modal
    openConfigModal(currentConfigCategory);
}

function addFilter() {
    const filterColumn = document.getElementById('filterColumn').value;
    const filterOperator = document.getElementById('filterOperator').value;
    const filterValue = document.getElementById('filterValue').value;

    if (!filterColumn || !filterValue) {
        alert('Por favor, completa todos los campos del filtro');
        return;
    }

    const config = getTableConfig(currentConfigCategory);
    config.filters.push({
        column: filterColumn,
        operator: filterOperator,
        value: filterValue
    });
    saveTableConfigs();

    // Clear inputs
    document.getElementById('filterValue').value = '';
    updateActiveFilters();
}

function removeFilter(index) {
    const config = getTableConfig(currentConfigCategory);
    config.filters.splice(index, 1);
    saveTableConfigs();
    updateActiveFilters();
}

function updateActiveFilters() {
    const activeFilters = document.getElementById('activeFilters');
    const config = getTableConfig(currentConfigCategory);
    const columns = COLUMN_DEFINITIONS[currentConfigCategory] || COLUMN_DEFINITIONS.tracking;

    activeFilters.innerHTML = '';
    config.filters.forEach((filter, index) => {
        const columnLabel = columns.find(c => c.key === filter.column)?.label || filter.column;
        const operatorLabels = {
            gt: '>',
            lt: '<',
            eq: '=',
            gte: '≥',
            lte: '≤'
        };

        const filterBadge = document.createElement('div');
        filterBadge.className = 'flex items-center justify-between px-4 py-2 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg';
        filterBadge.innerHTML = `
            <span class="text-sm text-gray-700 dark:text-gray-300">
                ${columnLabel} ${operatorLabels[filter.operator]} ${filter.value}
            </span>
            <button class="text-red-500 hover:text-red-700 dark:hover:text-red-400 transition-colors" onclick="removeFilter(${index})">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
            </button>
        `;
        activeFilters.appendChild(filterBadge);
    });
}

function applyTableConfiguration(category, config) {
    const table = document.getElementById(`${category}-table`);
    if (!table) return;

    // Apply column visibility
    const headers = Array.from(table.querySelectorAll('thead th'));
    headers.forEach((header, index) => {
        const sortKey = header.getAttribute('data-sort');
        if (sortKey) {
            if (!config.visibleColumns.includes(sortKey)) {
                header.style.display = 'none';
                // Hide corresponding cells in all rows
                const rows = table.querySelectorAll('tbody tr');
                rows.forEach(row => {
                    const cells = Array.from(row.querySelectorAll('td'));
                    if (cells[index]) {
                        cells[index].style.display = 'none';
                    }
                });
            } else {
                header.style.display = '';
                const rows = table.querySelectorAll('tbody tr');
                rows.forEach(row => {
                    const cells = Array.from(row.querySelectorAll('td'));
                    if (cells[index]) {
                        cells[index].style.display = '';
                    }
                });
            }
        }
    });

    // Apply default sort
    if (config.defaultSort && config.defaultSort.column) {
        const header = table.querySelector(`th[data-sort="${config.defaultSort.column}"]`);
        if (header && typeof sortTable === 'function') {
            sortTable(category, config.defaultSort.column, header);
            // Apply sort order
            if (config.defaultSort.order === 'desc') {
                // Toggle to get descending order
                sortTable(category, config.defaultSort.column, header);
            }
        }
    }

    // Apply filters
    applyFilters(category, config.filters);
}

function applyFilters(category, filters) {
    const tbody = document.getElementById(`${category}-tbody`);
    if (!tbody) return;

    const rows = Array.from(tbody.querySelectorAll('tr'));
    rows.forEach(row => {
        let showRow = true;

        filters.forEach(filter => {
            const value = parseFloat(row.getAttribute(`data-${filter.column}`)) || row.getAttribute(`data-${filter.column}`);
            const filterValue = parseFloat(filter.value) || filter.value;

            let matches = false;
            switch (filter.operator) {
                case 'gt':
                    matches = parseFloat(value) > parseFloat(filterValue);
                    break;
                case 'lt':
                    matches = parseFloat(value) < parseFloat(filterValue);
                    break;
                case 'eq':
                    matches = value == filterValue;
                    break;
                case 'gte':
                    matches = parseFloat(value) >= parseFloat(filterValue);
                    break;
                case 'lte':
                    matches = parseFloat(value) <= parseFloat(filterValue);
                    break;
            }

            if (!matches) {
                showRow = false;
            }
        });

        row.style.display = showRow ? '' : 'none';
    });
}

// Make functions available globally
window.removeFilter = removeFilter;
window.addFilter = addFilter;

