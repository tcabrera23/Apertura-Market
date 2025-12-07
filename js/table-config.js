// Table Configuration Management

// Use window.API_BASE_URL if available, otherwise use default
// Don't declare const to avoid conflicts
// const getApiBaseUrl = () => window.API_BASE_URL || 'http://localhost:8080/api'; // Development
const getApiBaseUrl = () => window.API_BASE_URL || 'https://api.bullanalytics.io/api'; // Production

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
        { key: 'diff', label: 'Diferencia vs. Máx' },
        { key: 'daily_change_percent', label: 'Var. Diaria %' },
        { key: 'daily_change', label: 'Var. Diaria $' },
        { key: 'dividend_yield', label: 'Dividendos' },
        { key: 'sma_50', label: 'SMA 50' },
        { key: 'sma_200', label: 'SMA 200' }
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
        { key: 'diff', label: 'Diferencia vs. Máx' },
        { key: 'daily_change_percent', label: 'Var. Diaria %' },
        { key: 'daily_change', label: 'Var. Diaria $' },
        { key: 'dividend_yield', label: 'Dividendos' },
        { key: 'sma_50', label: 'SMA 50' },
        { key: 'sma_200', label: 'SMA 200' }
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
        { key: 'diff', label: 'Diferencia vs. Máx' },
        { key: 'daily_change_percent', label: 'Var. Diaria %' },
        { key: 'daily_change', label: 'Var. Diaria $' },
        { key: 'dividend_yield', label: 'Dividendos' },
        { key: 'sma_50', label: 'SMA 50' },
        { key: 'sma_200', label: 'SMA 200' }
    ],
    crypto: [
        { key: 'name', label: 'Activo' },
        { key: 'price', label: 'Precio' },
        { key: 'market_cap', label: 'Market Cap' },
        { key: 'volume', label: 'Volumen' },
        { key: 'max', label: 'Máximo Histórico' },
        { key: 'diff', label: 'Diferencia vs. Máx' },
        { key: 'daily_change_percent', label: 'Var. Diaria %' }
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
            columnOrder: columns.map(c => c.key), // Store column order
            visibleColumns: columns.map(c => c.key),
            defaultSort: { column: 'name', order: 'asc' },
            filters: []
        };
    }
    return tableConfigs[category];
}

// Initialize configuration modal
console.log('table-config.js loaded');

// Wait for DOM to be ready
function initTableConfig() {
    console.log('Initializing table config...');
    loadTableConfigs();

    // Open config modal - use event delegation for better reliability
    // This works even if buttons are added dynamically
    document.addEventListener('click', (e) => {
        // Check if click is on button or any child element (like SVG)
        const configBtn = e.target.closest('[data-config]');
        if (configBtn) {
            console.log('Config button clicked!', configBtn);
            e.preventDefault();
            e.stopPropagation();
            const category = configBtn.getAttribute('data-config');
            console.log('Category from button:', category);
            if (category) {
                console.log('Opening config modal for category:', category);
                openConfigModal(category);
            } else {
                console.error('Button has data-config attribute but no value');
            }
        }
    });
    console.log('Event listener registered for config buttons');

    // Close config modal
    const closeBtn = document.getElementById('closeConfigModal');
    if (closeBtn) {
        closeBtn.addEventListener('click', closeConfigModal);
    } else {
        console.warn('Close config modal button not found');
    }

    // Apply configuration
    const applyBtn = document.getElementById('applyConfigBtn');
    if (applyBtn) {
        applyBtn.addEventListener('click', applyConfiguration);
    } else {
        console.warn('Apply config button not found');
    }

    // Reset configuration
    const resetBtn = document.getElementById('resetConfigBtn');
    if (resetBtn) {
        resetBtn.addEventListener('click', resetConfiguration);
    } else {
        console.warn('Reset config button not found');
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
    
    // Test: Log all buttons with data-config attribute
    const allConfigButtons = document.querySelectorAll('[data-config]');
    console.log('Found', allConfigButtons.length, 'config buttons:', Array.from(allConfigButtons).map(btn => ({
        category: btn.getAttribute('data-config'),
        element: btn
    })));
}

// Try multiple ways to ensure it runs
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTableConfig);
} else {
    // DOM is already loaded
    initTableConfig();
}

    // Event delegation is already handled above, so we don't need the MutationObserver for this

function openConfigModal(category) {
    if (!category) {
        console.error('No category provided to openConfigModal');
        return;
    }
    
    currentConfigCategory = category;
    const modal = document.getElementById('configModal');
    
    if (!modal) {
        console.error('Config modal not found in DOM. Make sure the modal exists in dashboard.html');
        alert('Error: Modal de configuración no encontrado. Por favor, recarga la página.');
        return;
    }
    
    const config = getTableConfig(category);
    const allColumns = COLUMN_DEFINITIONS[category] || COLUMN_DEFINITIONS.tracking;
    
    // Get column order from config or use default
    const columnOrder = config.columnOrder || allColumns.map(c => c.key);
    
    // Create ordered columns list based on saved order
    const orderedColumns = columnOrder.map(key => 
        allColumns.find(col => col.key === key)
    ).filter(Boolean);
    
    // Add any missing columns at the end
    allColumns.forEach(col => {
        if (!orderedColumns.find(c => c.key === col.key)) {
            orderedColumns.push(col);
        }
    });

    // Populate column visibility with drag & drop
    const columnVisibility = document.getElementById('columnVisibility');
    columnVisibility.innerHTML = '';
    
    orderedColumns.forEach((col, index) => {
        const isVisible = config.visibleColumns.includes(col.key);
        const item = document.createElement('div');
        item.className = 'flex items-center gap-3 p-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg cursor-move hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors draggable-item';
        item.setAttribute('data-column', col.key);
        item.setAttribute('draggable', 'true');
        item.innerHTML = `
            <div class="flex items-center gap-2 flex-shrink-0 text-gray-400 dark:text-gray-500 cursor-grab active:cursor-grabbing">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8h16M4 16h16"></path>
                </svg>
            </div>
            <input type="checkbox" class="w-4 h-4 text-green-600 border-gray-300 rounded focus:ring-green-500 flex-shrink-0" 
                   data-column="${col.key}" ${isVisible ? 'checked' : ''}>
            <span class="flex-1 text-gray-700 dark:text-gray-300 font-medium">${col.label}</span>
            <div class="flex items-center gap-1 flex-shrink-0">
                <button type="button" class="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors move-up" data-index="${index}" ${index === 0 ? 'disabled' : ''} title="Mover arriba">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7"></path>
                    </svg>
                </button>
                <button type="button" class="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors move-down" data-index="${index}" ${index === orderedColumns.length - 1 ? 'disabled' : ''} title="Mover abajo">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
                    </svg>
                </button>
            </div>
        `;
        columnVisibility.appendChild(item);
        
        // Add drag event listeners
        item.addEventListener('dragstart', handleDragStart);
        item.addEventListener('dragover', handleDragOver);
        item.addEventListener('drop', handleDrop);
        item.addEventListener('dragend', handleDragEnd);
        
        // Add move up/down button listeners
        const moveUpBtn = item.querySelector('.move-up');
        const moveDownBtn = item.querySelector('.move-down');
        if (moveUpBtn) {
            moveUpBtn.addEventListener('click', () => moveColumn(index, 'up'));
        }
        if (moveDownBtn) {
            moveDownBtn.addEventListener('click', () => moveColumn(index, 'down'));
        }
    });

    // Populate sort selectors
    const sortColumn = document.getElementById('defaultSortColumn');
    const sortOrder = document.getElementById('defaultSortOrder');
    sortColumn.innerHTML = '';
    orderedColumns.forEach(col => {
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
    orderedColumns.forEach(col => {
        const option = document.createElement('option');
        option.value = col.key;
        option.textContent = col.label;
        filterColumn.appendChild(option);
    });

    // Show active filters
    updateActiveFilters();

    // Show modal
    modal.classList.remove('hidden');
    modal.classList.add('flex');
    document.body.style.overflow = 'hidden';
    
    console.log('Modal opened successfully for category:', category);
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

    // Get column order from DOM
    const columnItems = Array.from(document.querySelectorAll('#columnVisibility .draggable-item'));
    config.columnOrder = columnItems.map(item => item.getAttribute('data-column'));

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
        columnOrder: columns.map(c => c.key),
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

    const thead = table.querySelector('thead');
    const tbody = table.querySelector('tbody');
    if (!thead || !tbody) return;

    // Get all headers and their current order
    const headers = Array.from(thead.querySelectorAll('th'));
    const headerMap = new Map();
    headers.forEach((header, index) => {
        const sortKey = header.getAttribute('data-sort');
        if (sortKey) {
            headerMap.set(sortKey, { element: header, originalIndex: index });
        }
    });

    // Reorder headers based on config.columnOrder
    if (config.columnOrder && config.columnOrder.length > 0) {
        const orderedHeaders = [];
        const remainingHeaders = [];
        
        // First, add headers in the configured order
        config.columnOrder.forEach(key => {
            const headerData = headerMap.get(key);
            if (headerData) {
                orderedHeaders.push(headerData);
            }
        });
        
        // Then add any remaining headers (in case new columns were added)
        headers.forEach((header, index) => {
            const sortKey = header.getAttribute('data-sort');
            if (sortKey && !config.columnOrder.includes(sortKey)) {
                remainingHeaders.push({ element: header, originalIndex: index });
            }
        });
        
        // Reorder header row
        const headerRow = thead.querySelector('tr');
        if (headerRow) {
            // Clear and rebuild header row
            headerRow.innerHTML = '';
            [...orderedHeaders, ...remainingHeaders].forEach(({ element }) => {
                headerRow.appendChild(element);
            });
        }
        
        // Reorder cells in all body rows using data-column attribute
        const rows = Array.from(tbody.querySelectorAll('tr'));
        rows.forEach(row => {
            const cells = Array.from(row.querySelectorAll('td'));
            const cellMap = new Map();
            cells.forEach((cell) => {
                const columnKey = cell.getAttribute('data-column');
                if (columnKey) {
                    cellMap.set(columnKey, cell);
                }
            });
            
            // Clear and rebuild row with new order
            row.innerHTML = '';
            [...orderedHeaders, ...remainingHeaders].forEach(({ element }) => {
                const sortKey = element.getAttribute('data-sort');
                const cell = cellMap.get(sortKey);
                if (cell) {
                    row.appendChild(cell);
                }
            });
        });
    }

    // Apply column visibility
    const finalHeaders = Array.from(thead.querySelectorAll('th'));
    finalHeaders.forEach((header) => {
        const sortKey = header.getAttribute('data-sort');
        if (sortKey) {
            const isVisible = config.visibleColumns.includes(sortKey);
            header.style.display = isVisible ? '' : 'none';
            
            // Hide/show corresponding cells in all rows
            const rows = tbody.querySelectorAll('tr');
            rows.forEach(row => {
                const cells = Array.from(row.querySelectorAll('td'));
                const headerIndex = finalHeaders.indexOf(header);
                if (cells[headerIndex]) {
                    cells[headerIndex].style.display = isVisible ? '' : 'none';
                }
            });
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

// Drag & Drop handlers
let draggedElement = null;

function handleDragStart(e) {
    draggedElement = this;
    this.style.opacity = '0.5';
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/html', this.innerHTML);
}

function handleDragOver(e) {
    if (e.preventDefault) {
        e.preventDefault();
    }
    e.dataTransfer.dropEffect = 'move';
    this.classList.add('border-green-500', 'border-2');
    return false;
}

function handleDragEnd(e) {
    this.style.opacity = '1';
    const items = document.querySelectorAll('#columnVisibility .draggable-item');
    items.forEach(item => {
        item.classList.remove('border-green-500', 'border-2');
    });
}

function handleDrop(e) {
    if (e.stopPropagation) {
        e.stopPropagation();
    }
    
    if (draggedElement !== this) {
        const container = this.parentElement;
        const items = Array.from(container.querySelectorAll('.draggable-item'));
        const draggedIndex = items.indexOf(draggedElement);
        const targetIndex = items.indexOf(this);
        
        if (draggedIndex < targetIndex) {
            container.insertBefore(draggedElement, this.nextSibling);
        } else {
            container.insertBefore(draggedElement, this);
        }
        
        // Update button indices
        updateMoveButtonIndices();
    }
    
    this.classList.remove('border-green-500', 'border-2');
    return false;
}

function moveColumn(index, direction) {
    const container = document.getElementById('columnVisibility');
    const items = Array.from(container.querySelectorAll('.draggable-item'));
    
    if (direction === 'up' && index > 0) {
        container.insertBefore(items[index], items[index - 1]);
        updateMoveButtonIndices();
    } else if (direction === 'down' && index < items.length - 1) {
        container.insertBefore(items[index + 1], items[index]);
        updateMoveButtonIndices();
    }
}

function updateMoveButtonIndices() {
    const items = Array.from(document.querySelectorAll('#columnVisibility .draggable-item'));
    items.forEach((item, index) => {
        const moveUpBtn = item.querySelector('.move-up');
        const moveDownBtn = item.querySelector('.move-down');
        if (moveUpBtn) {
            moveUpBtn.setAttribute('data-index', index);
            moveUpBtn.disabled = index === 0;
            moveUpBtn.classList.toggle('opacity-50', index === 0);
            moveUpBtn.classList.toggle('cursor-not-allowed', index === 0);
        }
        if (moveDownBtn) {
            moveDownBtn.setAttribute('data-index', index);
            moveDownBtn.disabled = index === items.length - 1;
            moveDownBtn.classList.toggle('opacity-50', index === items.length - 1);
            moveDownBtn.classList.toggle('cursor-not-allowed', index === items.length - 1);
        }
    });
}

// Make functions available globally
window.removeFilter = removeFilter;
window.addFilter = addFilter;
window.getTableConfig = getTableConfig;
window.applyTableConfiguration = applyTableConfiguration;

