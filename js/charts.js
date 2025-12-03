// BullAnalytics - Charts using TradingView Lightweight Charts
// Comparative analysis charts for each tab

// Chart instances storage
const chartInstances = {};

// Available metrics for different chart types
const METRICS = {
    numeric: [
        { key: 'pe_ratio', label: 'P/E Ratio', format: (v) => v?.toFixed(2) || 'N/A' },
        { key: 'revenue', label: 'Revenue', format: (v) => formatLargeNumber(v) },
        { key: 'revenue_growth', label: 'Revenue Growth', format: (v) => v ? (v * 100).toFixed(2) + '%' : 'N/A' },
        { key: 'profit_margin', label: 'Profit Margin', format: (v) => v ? (v * 100).toFixed(2) + '%' : 'N/A' },
        { key: 'return_on_equity', label: 'ROE', format: (v) => v ? (v * 100).toFixed(2) + '%' : 'N/A' },
        { key: 'debt_to_equity', label: 'Debt/Equity', format: (v) => v?.toFixed(2) || 'N/A' },
        { key: 'price_to_book', label: 'P/B', format: (v) => v?.toFixed(2) || 'N/A' },
        { key: 'beta', label: 'Beta', format: (v) => v?.toFixed(2) || 'N/A' },
        { key: 'volume', label: 'Volume', format: (v) => formatNumber(v) },
        { key: 'rsi', label: 'RSI', format: (v) => v?.toFixed(2) || 'N/A' },
        { key: 'price', label: 'Price', format: (v) => formatCurrency(v) },
        { key: 'market_cap', label: 'Market Cap', format: (v) => formatLargeNumber(v) },
        { key: 'diff_from_max', label: 'Diff vs Max', format: (v) => v ? (v * 100).toFixed(2) + '%' : 'N/A' }
    ]
};

// Helper functions
function formatLargeNumber(num) {
    if (!num) return 'N/A';
    if (num >= 1e12) return `$${(num / 1e12).toFixed(2)}T`;
    if (num >= 1e9) return `$${(num / 1e9).toFixed(2)}B`;
    if (num >= 1e6) return `$${(num / 1e6).toFixed(2)}M`;
    if (num >= 1e3) return `$${(num / 1e3).toFixed(2)}K`;
    return `$${num.toFixed(2)}`;
}

function formatNumber(num) {
    if (!num) return 'N/A';
    if (num >= 1e9) return (num / 1e9).toFixed(2) + 'B';
    if (num >= 1e6) return (num / 1e6).toFixed(2) + 'M';
    if (num >= 1e3) return (num / 1e3).toFixed(2) + 'K';
    return num.toFixed(0);
}

function formatCurrency(value) {
    if (!value) return 'N/A';
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(value);
}

// Get available metrics for a category
function getAvailableMetrics(category, data) {
    if (!data || data.length === 0) return [];
    
    const isCrypto = category === 'crypto';
    const availableMetrics = [];
    
    METRICS.numeric.forEach(metric => {
        // Skip metrics not available for crypto
        if (isCrypto && ['pe_ratio', 'revenue', 'revenue_growth', 'profit_margin', 'return_on_equity', 'debt_to_equity', 'price_to_book'].includes(metric.key)) {
            return;
        }
        
        // Check if at least one asset has this metric
        const hasData = data.some(asset => {
            const value = asset[metric.key];
            return value !== null && value !== undefined && !isNaN(value);
        });
        
        if (hasData) {
            availableMetrics.push(metric);
        }
    });
    
    return availableMetrics;
}

// Calculate average for a metric
function calculateAverage(data, metricKey) {
    const values = data
        .map(asset => asset[metricKey])
        .filter(v => v !== null && v !== undefined && !isNaN(v));
    
    if (values.length === 0) return null;
    return values.reduce((sum, v) => sum + v, 0) / values.length;
}

// Create Treemap Chart using canvas
function createTreemapChart(container, data, metric, category) {
    // Clear container
    container.innerHTML = '';
    
    // Create wrapper for responsive canvas
    const wrapper = document.createElement('div');
    wrapper.className = 'relative w-full';
    wrapper.style.height = '400px';
    container.appendChild(wrapper);
    
    const canvas = document.createElement('canvas');
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    wrapper.appendChild(canvas);
    
    const ctx = canvas.getContext('2d');
    const rect = wrapper.getBoundingClientRect();
    const width = rect.width || container.clientWidth || 800;
    const height = 400;
    
    // Set actual canvas size (for high DPI displays)
    const dpr = window.devicePixelRatio || 1;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.scale(dpr, dpr);
    
    // Filter and prepare data
    const validData = data
        .map(asset => ({
            name: asset.name || asset.ticker,
            ticker: asset.ticker,
            value: asset[metric.key]
        }))
        .filter(item => item.value !== null && item.value !== undefined && !isNaN(item.value))
        .sort((a, b) => b.value - a.value);
    
    if (validData.length === 0) {
        ctx.fillStyle = document.documentElement.classList.contains('dark') ? '#9CA3AF' : '#6B7280';
        ctx.font = '16px Inter';
        ctx.textAlign = 'center';
        ctx.fillText('No hay datos disponibles', width / 2, height / 2);
        return;
    }
    
    // Calculate average
    const avg = calculateAverage(data, metric.key);
    
    // Normalize values for sizing
    const maxValue = Math.max(...validData.map(d => Math.abs(d.value)));
    const minValue = Math.min(...validData.map(d => Math.abs(d.value)));
    const range = maxValue - minValue || 1;
    
    // Simple treemap layout (squarified algorithm simplified)
    const padding = 10;
    const availableWidth = width - padding * 2;
    const availableHeight = height - padding * 2 - 60; // Space for title
    
    // Draw title
    ctx.fillStyle = document.documentElement.classList.contains('dark') ? '#E5E7EB' : '#111827';
    ctx.font = 'bold 18px Inter';
    ctx.textAlign = 'center';
    ctx.fillText(`Treemap - ${metric.label}`, width / 2, 30);
    
    // Draw average line
    ctx.strokeStyle = document.documentElement.classList.contains('dark') ? '#6B7280' : '#9CA3AF';
    ctx.lineWidth = 2;
    ctx.setLineDash([5, 5]);
    ctx.beginPath();
    ctx.moveTo(padding, 50);
    ctx.lineTo(width - padding, 50);
    ctx.stroke();
    ctx.setLineDash([]);
    
    // Draw average text
    ctx.fillStyle = document.documentElement.classList.contains('dark') ? '#9CA3AF' : '#6B7280';
    ctx.font = '12px Inter';
    ctx.textAlign = 'left';
    ctx.fillText(`Promedio: ${metric.format(avg)}`, padding, 45);
    
    // Simple grid layout
    const cols = Math.ceil(Math.sqrt(validData.length));
    const rows = Math.ceil(validData.length / cols);
    const cellWidth = availableWidth / cols;
    const cellHeight = availableHeight / rows;
    
    let index = 0;
    for (let row = 0; row < rows && index < validData.length; row++) {
        for (let col = 0; col < cols && index < validData.length; col++) {
            const item = validData[index];
            const x = padding + col * cellWidth;
            const y = 60 + row * cellHeight;
            
            // Calculate color intensity based on value (red scale for P/E, green for others)
            const normalizedValue = (item.value - minValue) / range;
            let color;
            if (metric.key === 'pe_ratio') {
                // Red scale for P/E
                const intensity = Math.min(normalizedValue * 255, 255);
                color = `rgb(${Math.floor(intensity)}, 50, 50)`;
            } else {
                // Green scale for positive metrics
                const intensity = Math.min(normalizedValue * 200, 200);
                color = `rgb(50, ${Math.floor(50 + intensity)}, 50)`;
            }
            
            // Draw rectangle
            ctx.fillStyle = color;
            ctx.fillRect(x + 2, y + 2, cellWidth - 4, cellHeight - 4);
            
            // Draw border
            ctx.strokeStyle = document.documentElement.classList.contains('dark') ? '#374151' : '#E5E7EB';
            ctx.lineWidth = 1;
            ctx.strokeRect(x + 2, y + 2, cellWidth - 4, cellHeight - 4);
            
            // Draw text
            ctx.fillStyle = '#FFFFFF';
            ctx.font = 'bold 10px Inter';
            ctx.textAlign = 'center';
            const ticker = item.ticker.length > 8 ? item.ticker.substring(0, 8) : item.ticker;
            ctx.fillText(ticker, x + cellWidth / 2, y + cellHeight / 2 - 8);
            
            ctx.font = '9px Inter';
            ctx.fillText(metric.format(item.value), x + cellWidth / 2, y + cellHeight / 2 + 8);
            
            index++;
        }
    }
}

// Create Bar Chart using canvas
function createBarChart(container, data, xMetric, yMetric, category) {
    // Clear container
    container.innerHTML = '';
    
    // Create wrapper for responsive canvas
    const wrapper = document.createElement('div');
    wrapper.className = 'relative w-full';
    wrapper.style.height = '500px';
    container.appendChild(wrapper);
    
    const canvas = document.createElement('canvas');
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    wrapper.appendChild(canvas);
    
    const ctx = canvas.getContext('2d');
    const rect = wrapper.getBoundingClientRect();
    const width = rect.width || container.clientWidth || 800;
    const height = 500;
    
    // Set actual canvas size (for high DPI displays)
    const dpr = window.devicePixelRatio || 1;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.scale(dpr, dpr);
    
    // Filter and prepare data
    const validData = data
        .map(asset => ({
            name: asset.name || asset.ticker,
            ticker: asset.ticker,
            x: asset[xMetric.key],
            y: asset[yMetric.key]
        }))
        .filter(item => 
            item.x !== null && item.x !== undefined && !isNaN(item.x) &&
            item.y !== null && item.y !== undefined && !isNaN(item.y)
        )
        .sort((a, b) => b.y - a.y);
    
    if (validData.length === 0) {
        ctx.fillStyle = document.documentElement.classList.contains('dark') ? '#9CA3AF' : '#6B7280';
        ctx.font = '16px Inter';
        ctx.textAlign = 'center';
        ctx.fillText('No hay datos disponibles', width / 2, height / 2);
        return;
    }
    
    // Calculate averages
    const avgX = calculateAverage(data, xMetric.key);
    const avgY = calculateAverage(data, yMetric.key);
    
    // Setup chart area
    const padding = { top: 60, right: 150, bottom: 60, left: 80 };
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;
    
    // Find ranges
    const xMin = Math.min(...validData.map(d => d.x));
    const xMax = Math.max(...validData.map(d => d.x));
    const yMin = Math.min(...validData.map(d => d.y));
    const yMax = Math.max(...validData.map(d => d.y));
    const xRange = xMax - xMin || 1;
    const yRange = yMax - yMin || 1;
    
    // Draw title
    ctx.fillStyle = document.documentElement.classList.contains('dark') ? '#E5E7EB' : '#111827';
    ctx.font = 'bold 18px Inter';
    ctx.textAlign = 'center';
    ctx.fillText(`${yMetric.label} vs ${xMetric.label}`, width / 2, 30);
    
    // Draw axes
    ctx.strokeStyle = document.documentElement.classList.contains('dark') ? '#6B7280' : '#9CA3AF';
    ctx.lineWidth = 1;
    
    // X axis
    ctx.beginPath();
    ctx.moveTo(padding.left, height - padding.bottom);
    ctx.lineTo(width - padding.right, height - padding.bottom);
    ctx.stroke();
    
    // Y axis
    ctx.beginPath();
    ctx.moveTo(padding.left, padding.top);
    ctx.lineTo(padding.left, height - padding.bottom);
    ctx.stroke();
    
    // Draw axis labels
    ctx.fillStyle = document.documentElement.classList.contains('dark') ? '#9CA3AF' : '#6B7280';
    ctx.font = '12px Inter';
    ctx.textAlign = 'center';
    ctx.fillText(xMetric.label, width / 2, height - 20);
    
    ctx.save();
    ctx.translate(20, height / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.fillText(yMetric.label, 0, 0);
    ctx.restore();
    
    // Draw grid lines
    ctx.strokeStyle = document.documentElement.classList.contains('dark') ? '#374151' : '#E5E7EB';
    ctx.lineWidth = 0.5;
    ctx.setLineDash([2, 2]);
    
    // X grid
    for (let i = 0; i <= 5; i++) {
        const x = padding.left + (i / 5) * chartWidth;
        ctx.beginPath();
        ctx.moveTo(x, padding.top);
        ctx.lineTo(x, height - padding.bottom);
        ctx.stroke();
        
        const value = xMin + (i / 5) * xRange;
        ctx.fillStyle = document.documentElement.classList.contains('dark') ? '#6B7280' : '#9CA3AF';
        ctx.font = '10px Inter';
        ctx.textAlign = 'center';
        ctx.fillText(xMetric.format(value), x, height - padding.bottom + 20);
    }
    
    // Y grid
    for (let i = 0; i <= 5; i++) {
        const y = height - padding.bottom - (i / 5) * chartHeight;
        ctx.beginPath();
        ctx.moveTo(padding.left, y);
        ctx.lineTo(width - padding.right, y);
        ctx.stroke();
        
        const value = yMin + (i / 5) * yRange;
        ctx.fillStyle = document.documentElement.classList.contains('dark') ? '#6B7280' : '#9CA3AF';
        ctx.font = '10px Inter';
        ctx.textAlign = 'right';
        ctx.fillText(yMetric.format(value), padding.left - 10, y + 4);
    }
    
    ctx.setLineDash([]);
    
    // Draw average lines
    if (avgX !== null) {
        const avgXPos = padding.left + ((avgX - xMin) / xRange) * chartWidth;
        ctx.strokeStyle = '#EF4444';
        ctx.lineWidth = 2;
        ctx.setLineDash([5, 5]);
        ctx.beginPath();
        ctx.moveTo(avgXPos, padding.top);
        ctx.lineTo(avgXPos, height - padding.bottom);
        ctx.stroke();
    }
    
    if (avgY !== null) {
        const avgYPos = height - padding.bottom - ((avgY - yMin) / yRange) * chartHeight;
        ctx.strokeStyle = '#10B981';
        ctx.lineWidth = 2;
        ctx.setLineDash([5, 5]);
        ctx.beginPath();
        ctx.moveTo(padding.left, avgYPos);
        ctx.lineTo(width - padding.right, avgYPos);
        ctx.stroke();
    }
    
    ctx.setLineDash([]);
    
    // Draw data points
    validData.forEach((item, index) => {
        const x = padding.left + ((item.x - xMin) / xRange) * chartWidth;
        const y = height - padding.bottom - ((item.y - yMin) / yRange) * chartHeight;
        
        // Draw point
        ctx.fillStyle = '#10B981';
        ctx.beginPath();
        ctx.arc(x, y, 6, 0, Math.PI * 2);
        ctx.fill();
        
        // Draw label on hover area (right side)
        const labelY = padding.top + index * 25;
        if (labelY < height - padding.bottom) {
            ctx.fillStyle = document.documentElement.classList.contains('dark') ? '#E5E7EB' : '#111827';
            ctx.font = '11px Inter';
            ctx.textAlign = 'left';
            const displayName = item.ticker.length > 12 ? item.ticker.substring(0, 12) + '...' : item.ticker;
            ctx.fillText(displayName, width - padding.right + 10, labelY);
            
            // Draw connecting line
            ctx.strokeStyle = document.documentElement.classList.contains('dark') ? '#374151' : '#E5E7EB';
            ctx.lineWidth = 1;
            ctx.setLineDash([2, 2]);
            ctx.beginPath();
            ctx.moveTo(x, y);
            ctx.lineTo(width - padding.right, labelY);
            ctx.stroke();
            ctx.setLineDash([]);
        }
    });
    
    // Add tooltip on hover
    let hoveredIndex = null;
    canvas.addEventListener('mousemove', (e) => {
        const rect = canvas.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;
        const mouseY = e.clientY - rect.top;
        
        // Find closest point
        let minDist = Infinity;
        let closestIndex = null;
        
        validData.forEach((item, index) => {
            const x = padding.left + ((item.x - xMin) / xRange) * chartWidth;
            const y = height - padding.bottom - ((item.y - yMin) / yRange) * chartHeight;
            const dist = Math.sqrt(Math.pow(mouseX - x, 2) + Math.pow(mouseY - y, 2));
            if (dist < minDist && dist < 20) {
                minDist = dist;
                closestIndex = index;
            }
        });
        
        if (closestIndex !== hoveredIndex) {
            hoveredIndex = closestIndex;
            // Redraw chart (simplified - in production, use requestAnimationFrame)
            createBarChart(container, data, xMetric, yMetric, category);
            
            if (hoveredIndex !== null) {
                const item = validData[hoveredIndex];
                const x = padding.left + ((item.x - xMin) / xRange) * chartWidth;
                const y = height - padding.bottom - ((item.y - yMin) / yRange) * chartHeight;
                
                // Draw tooltip
                ctx.fillStyle = 'rgba(0, 0, 0, 0.8)';
                ctx.fillRect(x - 60, y - 60, 120, 50);
                
                ctx.fillStyle = '#FFFFFF';
                ctx.font = '10px Inter';
                ctx.textAlign = 'center';
                ctx.fillText(item.name, x, y - 40);
                ctx.fillText(`${xMetric.label}: ${xMetric.format(item.x)}`, x, y - 25);
                ctx.fillText(`${yMetric.label}: ${yMetric.format(item.y)}`, x, y - 10);
            }
        }
    });
}

// Render charts for a category
window.renderAnalysisCharts = function(category, data) {
    const containerId = `${category}-charts-container`;
    const container = document.getElementById(containerId);
    
    if (!container || !data || data.length === 0) {
        return;
    }
    
    const availableMetrics = getAvailableMetrics(category, data);
    if (availableMetrics.length === 0) {
        container.innerHTML = '<div class="text-center text-gray-500 dark:text-gray-400 py-8">No hay métricas disponibles para visualizar</div>';
        return;
    }
    
    // Default selections
    const defaultXMetric = availableMetrics.find(m => m.key === 'pe_ratio') || availableMetrics[0];
    const defaultYMetric = availableMetrics.find(m => m.key === 'revenue_growth') || 
                          availableMetrics.find(m => m.key === 'profit_margin') || 
                          availableMetrics[1] || availableMetrics[0];
    
    // Create chart container HTML
    container.innerHTML = `
        <div class="space-y-6">
            <!-- Treemap Chart -->
            <div class="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 p-6">
                <h3 class="text-lg font-bold text-gray-900 dark:text-white mb-4">Treemap - Análisis Comparativo</h3>
                <div class="mb-4">
                    <label class="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Métrica:</label>
                    <select id="${category}-treemap-metric" class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500 focus:border-transparent">
                        ${availableMetrics.map(m => `<option value="${m.key}" ${m.key === defaultXMetric.key ? 'selected' : ''}>${m.label}</option>`).join('')}
                    </select>
                </div>
                <div id="${category}-treemap-container" class="w-full"></div>
            </div>
            
            <!-- Bar/Scatter Chart with customizable axes -->
            <div class="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 p-6">
                <h3 class="text-lg font-bold text-gray-900 dark:text-white mb-4">Gráfico Comparativo - Personalizar Ejes</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                    <div>
                        <label class="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Eje X:</label>
                        <select id="${category}-x-metric" class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500 focus:border-transparent">
                            ${availableMetrics.map(m => `<option value="${m.key}" ${m.key === defaultXMetric.key ? 'selected' : ''}>${m.label}</option>`).join('')}
                        </select>
                    </div>
                    <div>
                        <label class="block text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Eje Y:</label>
                        <select id="${category}-y-metric" class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500 focus:border-transparent">
                            ${availableMetrics.map(m => `<option value="${m.key}" ${m.key === defaultYMetric.key ? 'selected' : ''}>${m.label}</option>`).join('')}
                        </select>
                    </div>
                </div>
                <div id="${category}-bar-container" class="w-full"></div>
            </div>
        </div>
    `;
    
    // Store data for this category
    if (!window.chartData) window.chartData = {};
    window.chartData[category] = data;
    
    // Render initial charts
    renderTreemap(category, defaultXMetric);
    renderBarChart(category, defaultXMetric, defaultYMetric);
    
    // Add event listeners
    const treemapSelect = document.getElementById(`${category}-treemap-metric`);
    const xSelect = document.getElementById(`${category}-x-metric`);
    const ySelect = document.getElementById(`${category}-y-metric`);
    
    treemapSelect?.addEventListener('change', (e) => {
        const metric = availableMetrics.find(m => m.key === e.target.value);
        if (metric) renderTreemap(category, metric);
    });
    
    xSelect?.addEventListener('change', (e) => {
        const xMetric = availableMetrics.find(m => m.key === e.target.value);
        const yMetric = availableMetrics.find(m => m.key === ySelect.value);
        if (xMetric && yMetric) renderBarChart(category, xMetric, yMetric);
    });
    
    ySelect?.addEventListener('change', (e) => {
        const xMetric = availableMetrics.find(m => m.key === xSelect.value);
        const yMetric = availableMetrics.find(m => m.key === e.target.value);
        if (xMetric && yMetric) renderBarChart(category, xMetric, yMetric);
    });
};

function renderTreemap(category, metric) {
    const container = document.getElementById(`${category}-treemap-container`);
    if (!container || !window.chartData || !window.chartData[category]) return;
    
    const data = window.chartData[category];
    createTreemapChart(container, data, metric, category);
}

function renderBarChart(category, xMetric, yMetric) {
    const container = document.getElementById(`${category}-bar-container`);
    if (!container || !window.chartData || !window.chartData[category]) return;
    
    const data = window.chartData[category];
    createBarChart(container, data, xMetric, yMetric, category);
}

