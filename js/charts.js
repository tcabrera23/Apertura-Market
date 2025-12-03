// BullAnalytics - Charts using TradingView Lightweight Charts
// Comparative analysis charts with TradingView styling

// Chart instances storage
const chartInstances = {};

// TradingView color schemes
const TRADINGVIEW_THEMES = {
    dark: {
        background: '#131722',
        text: '#D1D4DC',
        grid: '#2B2B43',
        border: '#363A45',
        upColor: '#26A69A',
        downColor: '#EF5350',
        lineColor: '#2962FF',
        areaTopColor: 'rgba(41, 98, 255, 0.28)',
        areaBottomColor: 'rgba(41, 98, 255, 0.05)',
        crosshair: '#758696',
        panel: '#1E222D'
    },
    light: {
        background: '#FFFFFF',
        text: '#191919',
        grid: '#E0E3EB',
        border: '#D1D4DC',
        upColor: '#26A69A',
        downColor: '#EF5350',
        lineColor: '#2962FF',
        areaTopColor: 'rgba(41, 98, 255, 0.28)',
        areaBottomColor: 'rgba(41, 98, 255, 0.05)',
        crosshair: '#758696',
        panel: '#F8F9FA'
    }
};

// Get current theme
function getTheme() {
    return document.documentElement.classList.contains('dark') ? TRADINGVIEW_THEMES.dark : TRADINGVIEW_THEMES.light;
}

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

// Create Treemap Chart with TradingView styling
function createTreemapChart(container, data, metric, category) {
    container.innerHTML = '';
    
    const theme = getTheme();
    const wrapper = document.createElement('div');
    wrapper.className = 'relative w-full overflow-hidden';
    wrapper.style.height = '450px';
    wrapper.style.backgroundColor = theme.panel;
    wrapper.style.borderRadius = '8px';
    wrapper.style.border = `1px solid ${theme.border}`;
    container.appendChild(wrapper);
    
    const canvas = document.createElement('canvas');
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    wrapper.appendChild(canvas);
    
    const ctx = canvas.getContext('2d');
    const rect = wrapper.getBoundingClientRect();
    const width = rect.width || container.clientWidth || 800;
    const height = 450;
    
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
        ctx.fillStyle = theme.text;
        ctx.font = '14px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('No hay datos disponibles', width / 2, height / 2);
        return;
    }
    
    const avg = calculateAverage(data, metric.key);
    const maxValue = Math.max(...validData.map(d => Math.abs(d.value)));
    const minValue = Math.min(...validData.map(d => Math.abs(d.value)));
    const range = maxValue - minValue || 1;
    
    const padding = 16;
    const headerHeight = 60;
    const availableWidth = width - padding * 2;
    const availableHeight = height - padding * 2 - headerHeight;
    
    // Draw header with TradingView style
    ctx.fillStyle = theme.background;
    ctx.fillRect(0, 0, width, headerHeight);
    
    // Title
    ctx.fillStyle = theme.text;
    ctx.font = 'bold 16px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText(`Treemap - ${metric.label}`, padding, 28);
    
    // Average line and text
    ctx.strokeStyle = theme.grid;
    ctx.lineWidth = 1;
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(padding, 42);
    ctx.lineTo(width - padding, 42);
    ctx.stroke();
    ctx.setLineDash([]);
    
    ctx.fillStyle = theme.text;
    ctx.font = '12px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
    ctx.fillText(`Promedio: ${metric.format(avg)}`, padding, 56);
    
    // Squarified treemap layout
    const cols = Math.ceil(Math.sqrt(validData.length));
    const rows = Math.ceil(validData.length / cols);
    const cellWidth = availableWidth / cols;
    const cellHeight = availableHeight / rows;
    
    let index = 0;
    for (let row = 0; row < rows && index < validData.length; row++) {
        for (let col = 0; col < cols && index < validData.length; col++) {
            const item = validData[index];
            const x = padding + col * cellWidth;
            const y = headerHeight + padding + row * cellHeight;
            
            // Color based on metric type (red for P/E, gradient for others)
            let color;
            if (metric.key === 'pe_ratio') {
                const intensity = Math.min((item.value - minValue) / range * 200, 200);
                color = `rgb(${Math.floor(100 + intensity)}, ${Math.floor(50)}, ${Math.floor(50)})`;
            } else {
                const intensity = Math.min((item.value - minValue) / range * 150, 150);
                color = `rgb(${Math.floor(50)}, ${Math.floor(100 + intensity)}, ${Math.floor(50)})`;
            }
            
            // Draw rectangle
            ctx.fillStyle = color;
            ctx.fillRect(x + 3, y + 3, cellWidth - 6, cellHeight - 6);
            
            // Draw border
            ctx.strokeStyle = theme.border;
            ctx.lineWidth = 1;
            ctx.strokeRect(x + 3, y + 3, cellWidth - 6, cellHeight - 6);
            
            // Draw text
            ctx.fillStyle = '#FFFFFF';
            ctx.font = 'bold 11px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
            ctx.textAlign = 'center';
            const ticker = item.ticker.length > 10 ? item.ticker.substring(0, 10) + '...' : item.ticker;
            ctx.fillText(ticker, x + cellWidth / 2, y + cellHeight / 2 - 6);
            
            ctx.font = '10px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
            ctx.fillText(metric.format(item.value), x + cellWidth / 2, y + cellHeight / 2 + 8);
            
            index++;
        }
    }
}

// Create Scatter Chart with TradingView styling
function createScatterChart(container, data, xMetric, yMetric, category) {
    container.innerHTML = '';
    
    const theme = getTheme();
    const wrapper = document.createElement('div');
    wrapper.className = 'relative w-full';
    wrapper.style.height = '500px';
    wrapper.style.backgroundColor = theme.background;
    wrapper.style.borderRadius = '8px';
    wrapper.style.border = `1px solid ${theme.border}`;
    wrapper.style.position = 'relative';
    container.appendChild(wrapper);
    
    const canvas = document.createElement('canvas');
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    canvas.style.display = 'block';
    wrapper.appendChild(canvas);
    
    const ctx = canvas.getContext('2d');
    const rect = wrapper.getBoundingClientRect();
    const width = rect.width || container.clientWidth || 800;
    const height = 500;
    
    const dpr = window.devicePixelRatio || 1;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.scale(dpr, dpr);
    
    // Prepare data
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
        );
    
    if (validData.length === 0) {
        ctx.fillStyle = theme.text;
        ctx.font = '14px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('No hay datos disponibles', width / 2, height / 2);
        return;
    }
    
    // Calculate averages
    const avgX = calculateAverage(data, xMetric.key);
    const avgY = calculateAverage(data, yMetric.key);
    
    // Setup chart area
    const padding = { top: 50, right: 20, bottom: 50, left: 70 };
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;
    
    // Find ranges
    const xValues = validData.map(d => d.x);
    const yValues = validData.map(d => d.y);
    const xMin = Math.min(...xValues);
    const xMax = Math.max(...xValues);
    const yMin = Math.min(...yValues);
    const yMax = Math.max(...yValues);
    const xRange = xMax - xMin || 1;
    const yRange = yMax - yMin || 1;
    
    // Draw background
    ctx.fillStyle = theme.background;
    ctx.fillRect(0, 0, width, height);
    
    // Draw grid (TradingView style)
    ctx.strokeStyle = theme.grid;
    ctx.lineWidth = 1;
    
    // Vertical grid lines
    for (let i = 0; i <= 5; i++) {
        const x = padding.left + (i / 5) * chartWidth;
        ctx.beginPath();
        ctx.moveTo(x, padding.top);
        ctx.lineTo(x, height - padding.bottom);
        ctx.stroke();
    }
    
    // Horizontal grid lines
    for (let i = 0; i <= 5; i++) {
        const y = height - padding.bottom - (i / 5) * chartHeight;
        ctx.beginPath();
        ctx.moveTo(padding.left, y);
        ctx.lineTo(width - padding.right, y);
        ctx.stroke();
    }
    
    // Draw axes
    ctx.strokeStyle = theme.border;
    ctx.lineWidth = 1.5;
    
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
    
    // Draw axis labels and ticks
    ctx.fillStyle = theme.text;
    ctx.font = '11px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
    ctx.textAlign = 'center';
    
    // X axis ticks
    for (let i = 0; i <= 5; i++) {
        const x = padding.left + (i / 5) * chartWidth;
        const value = xMin + (i / 5) * xRange;
        
        // Tick mark
        ctx.strokeStyle = theme.border;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(x, height - padding.bottom);
        ctx.lineTo(x, height - padding.bottom + 5);
        ctx.stroke();
        
        // Label
        ctx.fillStyle = theme.text;
        ctx.fillText(xMetric.format(value), x, height - padding.bottom + 20);
    }
    
    // Y axis ticks
    ctx.textAlign = 'right';
    for (let i = 0; i <= 5; i++) {
        const y = height - padding.bottom - (i / 5) * chartHeight;
        const value = yMin + (i / 5) * yRange;
        
        // Tick mark
        ctx.strokeStyle = theme.border;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(padding.left, y);
        ctx.lineTo(padding.left - 5, y);
        ctx.stroke();
        
        // Label
        ctx.fillStyle = theme.text;
        ctx.fillText(yMetric.format(value), padding.left - 10, y + 4);
    }
    
    // Draw average lines
    if (avgX !== null) {
        const avgXPos = padding.left + ((avgX - xMin) / xRange) * chartWidth;
        ctx.strokeStyle = theme.downColor;
        ctx.lineWidth = 1.5;
        ctx.setLineDash([4, 4]);
        ctx.beginPath();
        ctx.moveTo(avgXPos, padding.top);
        ctx.lineTo(avgXPos, height - padding.bottom);
        ctx.stroke();
        ctx.setLineDash([]);
    }
    
    if (avgY !== null) {
        const avgYPos = height - padding.bottom - ((avgY - yMin) / yRange) * chartHeight;
        ctx.strokeStyle = theme.upColor;
        ctx.lineWidth = 1.5;
        ctx.setLineDash([4, 4]);
        ctx.beginPath();
        ctx.moveTo(padding.left, avgYPos);
        ctx.lineTo(width - padding.right, avgYPos);
        ctx.stroke();
        ctx.setLineDash([]);
    }
    
    // Draw scatter points
    let hoveredIndex = null;
    validData.forEach((item, index) => {
        const x = padding.left + ((item.x - xMin) / xRange) * chartWidth;
        const y = height - padding.bottom - ((item.y - yMin) / yRange) * chartHeight;
        
        // Draw point with TradingView style
        ctx.fillStyle = theme.lineColor;
        ctx.beginPath();
        ctx.arc(x, y, 6, 0, Math.PI * 2);
        ctx.fill();
        
        // Draw border
        ctx.strokeStyle = theme.background;
        ctx.lineWidth = 2;
        ctx.stroke();
        
        // Store position for hover
        item._x = x;
        item._y = y;
    });
    
    // Draw axis titles
    ctx.fillStyle = theme.text;
    ctx.font = '13px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(xMetric.label, width / 2, height - 10);
    
    ctx.save();
    ctx.translate(15, height / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.fillText(yMetric.label, 0, 0);
    ctx.restore();
    
    // Add hover tooltip
    canvas.addEventListener('mousemove', (e) => {
        const rect = canvas.getBoundingClientRect();
        const mouseX = (e.clientX - rect.left) * (canvas.width / rect.width) / dpr;
        const mouseY = (e.clientY - rect.top) * (canvas.height / rect.height) / dpr;
        
        let minDist = Infinity;
        let closestIndex = null;
        
        validData.forEach((item, index) => {
            const dist = Math.sqrt(Math.pow(mouseX - item._x, 2) + Math.pow(mouseY - item._y, 2));
            if (dist < minDist && dist < 15) {
                minDist = dist;
                closestIndex = index;
            }
        });
        
        if (closestIndex !== hoveredIndex) {
            hoveredIndex = closestIndex;
            // Redraw to show tooltip
            createScatterChart(container, data, xMetric, yMetric, category);
            
            if (hoveredIndex !== null) {
                const item = validData[hoveredIndex];
                const x = item._x;
                const y = item._y;
                
                // Draw tooltip
                const tooltipWidth = 180;
                const tooltipHeight = 80;
                const tooltipX = Math.min(x + 15, width - tooltipWidth - 10);
                const tooltipY = Math.max(y - tooltipHeight / 2, 10);
                
                // Background
                ctx.fillStyle = 'rgba(0, 0, 0, 0.85)';
                ctx.fillRect(tooltipX, tooltipY, tooltipWidth, tooltipHeight);
                
                // Border
                ctx.strokeStyle = theme.border;
                ctx.lineWidth = 1;
                ctx.strokeRect(tooltipX, tooltipY, tooltipWidth, tooltipHeight);
                
                // Text
                ctx.fillStyle = '#FFFFFF';
                ctx.font = 'bold 12px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
                ctx.textAlign = 'left';
                ctx.fillText(item.name, tooltipX + 10, tooltipY + 20);
                
                ctx.font = '11px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
                ctx.fillText(`${xMetric.label}: ${xMetric.format(item.x)}`, tooltipX + 10, tooltipY + 40);
                ctx.fillText(`${yMetric.label}: ${yMetric.format(item.y)}`, tooltipX + 10, tooltipY + 60);
            }
        }
    });
    
    // Handle resize
    const resizeObserver = new ResizeObserver(() => {
        const newRect = wrapper.getBoundingClientRect();
        const newWidth = newRect.width || container.clientWidth || 800;
        if (Math.abs(newWidth - width) > 10) {
            createScatterChart(container, data, xMetric, yMetric, category);
        }
    });
    resizeObserver.observe(wrapper);
}

// Create Price History Chart with TradingView Lightweight Charts
function createPriceHistoryChart(container, ticker, assetData, period = '1y') {
    // Clean up existing chart
    const chartKey = `${ticker}-price-history`;
    if (chartInstances[chartKey]) {
        try {
            chartInstances[chartKey].remove();
        } catch (e) {
            console.warn('Error removing chart:', e);
        }
        delete chartInstances[chartKey];
    }
    
    container.innerHTML = '';
    
    const theme = getTheme();
    const API_BASE_URL = window.API_BASE_URL || 'http://localhost:8080/api';
    
    // Create wrapper
    const wrapper = document.createElement('div');
    wrapper.className = 'relative w-full';
    wrapper.style.height = '500px';
    wrapper.style.backgroundColor = theme.background;
    wrapper.style.borderRadius = '8px';
    wrapper.style.border = `1px solid ${theme.border}`;
    container.appendChild(wrapper);
    
    // Loading state
    wrapper.innerHTML = `<div style="display: flex; align-items: center; justify-content: center; height: 100%; color: ${theme.text}; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">Cargando datos históricos...</div>`;
    
    // Check if LightweightCharts is available with retry mechanism
    const checkLibrary = (retries = 5) => {
        if (typeof LightweightCharts === 'undefined') {
            if (retries > 0) {
                setTimeout(() => checkLibrary(retries - 1), 500);
            } else {
                wrapper.innerHTML = `<div style="display: flex; align-items: center; justify-content: center; height: 100%; color: ${theme.text};">Error: La biblioteca de gráficos no está disponible. Por favor recarga la página.</div>`;
            }
            return;
        }
        
        // Library is available, proceed with fetch
        loadChartData();
    };
    
    const loadChartData = () => {
        // Fetch historical data
        fetch(`${API_BASE_URL}/asset/${ticker}/history?period=${period}&interval=1d`)
        .then(res => {
            if (!res.ok) {
                throw new Error(`HTTP error! status: ${res.status}`);
            }
            return res.json();
        })
        .then(historyData => {
            console.log('History data received:', historyData);
            
            if (!historyData || historyData.length === 0) {
                wrapper.innerHTML = `<div style="display: flex; align-items: center; justify-content: center; height: 100%; color: ${theme.text};">No hay datos históricos disponibles</div>`;
                return;
            }
            
            wrapper.innerHTML = '';
            
            // Create chart
            const chart = LightweightCharts.createChart(wrapper, {
                width: wrapper.clientWidth,
                height: 500,
                layout: {
                    background: { color: theme.background },
                    textColor: theme.text,
                    fontSize: 12,
                    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
                },
                grid: {
                    vertLines: { color: theme.grid, style: 1 },
                    horzLines: { color: theme.grid, style: 1 }
                },
                crosshair: {
                    mode: LightweightCharts.CrosshairMode.Normal,
                    vertLine: { color: theme.crosshair, width: 1 },
                    horzLine: { color: theme.crosshair, width: 1 }
                },
                rightPriceScale: {
                    borderColor: theme.border,
                    scaleMargins: { top: 0.1, bottom: 0.1 }
                },
                timeScale: {
                    borderColor: theme.border,
                    timeVisible: true,
                    secondsVisible: false
                }
            });
            
            // Add area series - check for different API versions
            let areaSeries;
            try {
                // Try addSeries with AreaSeries (v5+ API)
                if (typeof LightweightCharts.AreaSeries !== 'undefined' && typeof chart.addSeries === 'function') {
                    areaSeries = chart.addSeries(LightweightCharts.AreaSeries, {
                        lineColor: theme.upColor,
                        topColor: theme.areaTopColor,
                        bottomColor: theme.areaBottomColor,
                        lineWidth: 2
                    });
                }
                // Try addAreaSeries (older API)
                else if (typeof chart.addAreaSeries === 'function') {
                    areaSeries = chart.addAreaSeries({
                        lineColor: theme.upColor,
                        topColor: theme.areaTopColor,
                        bottomColor: theme.areaBottomColor,
                        lineWidth: 2
                    });
                }
                // Fallback to addLineSeries with area fill
                else {
                    areaSeries = chart.addLineSeries({
                        color: theme.upColor,
                        lineWidth: 2,
                        priceLineVisible: false,
                        lastValueVisible: true
                    });
                    // Note: LineSeries doesn't support area fill in all versions
                    // We'll use a line chart as fallback
                }
            } catch (e) {
                console.error('Error creating area series:', e);
                // Final fallback to basic line series
                areaSeries = chart.addLineSeries({
                    color: theme.upColor,
                    lineWidth: 2
                });
            }
            
            // Convert data to TradingView format
            // TradingView expects dates in YYYY-MM-DD format as strings
            const chartData = historyData
                .map(item => {
                    // Ensure date is in correct format
                    let dateStr = item.date;
                    if (dateStr && dateStr.length === 10) {
                        // Already in YYYY-MM-DD format
                        return {
                            time: dateStr,
                            value: parseFloat(item.close) || 0
                        };
                    }
                    return null;
                })
                .filter(item => item !== null && item.value > 0)
                .sort((a, b) => a.time.localeCompare(b.time)); // Sort by date
            
            console.log('Chart data prepared:', chartData.slice(0, 5), '...', chartData.slice(-5));
            
            if (chartData.length === 0) {
                wrapper.innerHTML = `<div style="display: flex; align-items: center; justify-content: center; height: 100%; color: ${theme.text};">No se pudieron procesar los datos históricos</div>`;
                return;
            }
            
            try {
                areaSeries.setData(chartData);
                
                // Add previous close line (if available)
                if (assetData && historyData.length > 1) {
                    // Use first data point as previous close reference
                    const previousClose = parseFloat(historyData[0].close);
                    if (previousClose && !isNaN(previousClose)) {
                        areaSeries.createPriceLine({
                            price: previousClose,
                            color: theme.downColor,
                            lineWidth: 1,
                            lineStyle: LightweightCharts.LineStyle.Dashed,
                            axisLabelVisible: true,
                            title: `Cierre: ${formatCurrency(previousClose)}`
                        });
                    }
                }
                
                // Fit content and handle resize
                chart.timeScale().fitContent();
                
                // Store chart instance
                chartInstances[chartKey] = chart;
                
                // Handle resize
                const resizeObserver = new ResizeObserver(() => {
                    chart.applyOptions({ width: wrapper.clientWidth });
                });
                resizeObserver.observe(wrapper);
            } catch (chartError) {
                console.error('Error creating chart:', chartError);
                wrapper.innerHTML = `<div style="display: flex; align-items: center; justify-content: center; height: 100%; color: ${theme.text};">Error al crear el gráfico: ${chartError.message}</div>`;
            }
        })
        .catch(error => {
            console.error('Error loading price history:', error);
            wrapper.innerHTML = `<div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: ${theme.text}; gap: 8px;">
                <div style="font-weight: 600;">Error al cargar datos históricos</div>
                <div style="font-size: 12px; opacity: 0.7;">${error.message || 'Error desconocido'}</div>
            </div>`;
        });
    };
    
    // Start checking for library
    checkLibrary();
}

// Create Asset Info Panel
function createAssetInfoPanel(container, assetData) {
    const theme = getTheme();
    
    const changePercent = assetData.diff_from_max ? (assetData.diff_from_max * 100) : 0;
    const changeColor = changePercent >= 0 ? theme.upColor : theme.downColor;
    const changeSign = changePercent >= 0 ? '+' : '';
    
    container.innerHTML = `
        <div style="background-color: ${theme.panel}; border: 1px solid ${theme.border}; border-radius: 8px; padding: 20px; height: 100%;">
            <div style="margin-bottom: 20px;">
                <h3 style="color: ${theme.text}; font-size: 24px; font-weight: 700; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin-bottom: 8px;">
                    ${assetData.name || assetData.ticker}
                </h3>
                <div style="display: flex; align-items: baseline; gap: 12px; margin-bottom: 12px;">
                    <span style="color: ${theme.text}; font-size: 32px; font-weight: 700; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
                        ${formatCurrency(assetData.price)}
                    </span>
                    <span style="background-color: ${changeColor}20; color: ${changeColor}; padding: 4px 8px; border-radius: 4px; font-size: 14px; font-weight: 600;">
                        ${changeSign}${changePercent.toFixed(2)}%
                    </span>
                </div>
                <div style="color: ${theme.text}80; font-size: 12px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
                    ${assetData.ticker} • ${new Date().toLocaleDateString('es-ES', { day: 'numeric', month: 'short', year: 'numeric' })}
                </div>
            </div>
            
            <div style="border-top: 1px solid ${theme.border}; padding-top: 16px;">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
                    <div>
                        <div style="color: ${theme.text}80; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
                            Máximo Histórico
                        </div>
                        <div style="color: ${theme.text}; font-size: 14px; font-weight: 600; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
                            ${formatCurrency(assetData.all_time_high || 0)}
                        </div>
                    </div>
                    <div>
                        <div style="color: ${theme.text}80; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
                            P/E Ratio
                        </div>
                        <div style="color: ${theme.text}; font-size: 14px; font-weight: 600; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
                            ${assetData.pe_ratio ? assetData.pe_ratio.toFixed(2) : 'N/A'}
                        </div>
                    </div>
                    <div>
                        <div style="color: ${theme.text}80; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
                            Market Cap
                        </div>
                        <div style="color: ${theme.text}; font-size: 14px; font-weight: 600; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
                            ${assetData.market_cap ? formatLargeNumber(assetData.market_cap) : 'N/A'}
                        </div>
                    </div>
                    <div>
                        <div style="color: ${theme.text}80; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
                            Volumen
                        </div>
                        <div style="color: ${theme.text}; font-size: 14px; font-weight: 600; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
                            ${assetData.volume ? formatNumber(assetData.volume) : 'N/A'}
                        </div>
                    </div>
                    ${assetData.revenue ? `
                    <div>
                        <div style="color: ${theme.text}80; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
                            Revenue
                        </div>
                        <div style="color: ${theme.text}; font-size: 14px; font-weight: 600; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
                            ${formatLargeNumber(assetData.revenue)}
                        </div>
                    </div>
                    ` : ''}
                    ${assetData.return_on_equity ? `
                    <div>
                        <div style="color: ${theme.text}80; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
                            ROE
                        </div>
                        <div style="color: ${theme.text}; font-size: 14px; font-weight: 600; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
                            ${(assetData.return_on_equity * 100).toFixed(2)}%
                        </div>
                    </div>
                    ` : ''}
                </div>
            </div>
        </div>
    `;
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
    
    const theme = getTheme();
    const defaultXMetric = availableMetrics.find(m => m.key === 'pe_ratio') || availableMetrics[0];
    const defaultYMetric = availableMetrics.find(m => m.key === 'revenue_growth') || 
                          availableMetrics.find(m => m.key === 'profit_margin') || 
                          availableMetrics[1] || availableMetrics[0];
    
    // Default selected asset for price chart
    const defaultAsset = data[0];
    
    // Create chart container HTML with 2x2 grid layout
    container.innerHTML = `
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- Top Left: Treemap Chart -->
            <div style="background-color: ${theme.panel}; border: 1px solid ${theme.border}; border-radius: 8px; padding: 20px;">
                <div class="flex items-center justify-between mb-4">
                    <h3 style="color: ${theme.text}; font-size: 18px; font-weight: 600; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
                        Treemap - Análisis Comparativo
                    </h3>
                </div>
                <div class="mb-4">
                    <label style="display: block; color: ${theme.text}; font-size: 13px; font-weight: 500; margin-bottom: 8px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
                        Métrica:
                    </label>
                    <select id="${category}-treemap-metric" 
                        style="width: 100%; padding: 10px 14px; border: 1px solid ${theme.border}; border-radius: 6px; background-color: ${theme.background}; color: ${theme.text}; font-size: 13px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; outline: none; transition: all 0.2s;"
                        onmouseover="this.style.borderColor='${theme.lineColor}'"
                        onmouseout="this.style.borderColor='${theme.border}'"
                        onfocus="this.style.borderColor='${theme.lineColor}'; this.style.boxShadow='0 0 0 3px rgba(41, 98, 255, 0.1)'"
                        onblur="this.style.borderColor='${theme.border}'; this.style.boxShadow='none'">
                        ${availableMetrics.map(m => `<option value="${m.key}" ${m.key === defaultXMetric.key ? 'selected' : ''}>${m.label}</option>`).join('')}
                    </select>
                </div>
                <div id="${category}-treemap-container" class="w-full"></div>
            </div>
            
            <!-- Top Right: Price History Chart with Info Panel -->
            <div style="background-color: ${theme.panel}; border: 1px solid ${theme.border}; border-radius: 8px; padding: 20px;">
                <div class="flex items-center justify-between mb-4">
                    <h3 style="color: ${theme.text}; font-size: 18px; font-weight: 600; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
                        Precio Histórico
                    </h3>
                </div>
                <div class="mb-4 flex gap-2">
                    <select id="${category}-asset-select" 
                        style="flex: 1; padding: 10px 14px; border: 1px solid ${theme.border}; border-radius: 6px; background-color: ${theme.background}; color: ${theme.text}; font-size: 13px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; outline: none; transition: all 0.2s;"
                        onmouseover="this.style.borderColor='${theme.lineColor}'"
                        onmouseout="this.style.borderColor='${theme.border}'"
                        onfocus="this.style.borderColor='${theme.lineColor}'; this.style.boxShadow='0 0 0 3px rgba(41, 98, 255, 0.1)'"
                        onblur="this.style.borderColor='${theme.border}'; this.style.boxShadow='none'">
                        ${data.map(asset => `<option value="${asset.ticker}" ${asset.ticker === defaultAsset.ticker ? 'selected' : ''}>${asset.name || asset.ticker}</option>`).join('')}
                    </select>
                    <select id="${category}-period-select" 
                        style="padding: 10px 14px; border: 1px solid ${theme.border}; border-radius: 6px; background-color: ${theme.background}; color: ${theme.text}; font-size: 13px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; outline: none; transition: all 0.2s;"
                        onmouseover="this.style.borderColor='${theme.lineColor}'"
                        onmouseout="this.style.borderColor='${theme.border}'"
                        onfocus="this.style.borderColor='${theme.lineColor}'; this.style.boxShadow='0 0 0 3px rgba(41, 98, 255, 0.1)'"
                        onblur="this.style.borderColor='${theme.border}'; this.style.boxShadow='none'">
                        <option value="5d">5 Días</option>
                        <option value="1mo">1 Mes</option>
                        <option value="3mo">3 Meses</option>
                        <option value="6mo">6 Meses</option>
                        <option value="1y" selected>1 Año</option>
                        <option value="2y">2 Años</option>
                        <option value="5y">5 Años</option>
                        <option value="max">Máximo</option>
                    </select>
                </div>
                <div id="${category}-price-chart-container" class="w-full mb-4"></div>
                <div id="${category}-asset-info-container" class="w-full"></div>
            </div>
            
            <!-- Bottom Left: Scatter Chart with customizable axes -->
            <div style="background-color: ${theme.panel}; border: 1px solid ${theme.border}; border-radius: 8px; padding: 20px;">
                <div class="flex items-center justify-between mb-4">
                    <h3 style="color: ${theme.text}; font-size: 18px; font-weight: 600; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
                        Gráfico Comparativo
                    </h3>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                    <div>
                        <label style="display: block; color: ${theme.text}; font-size: 13px; font-weight: 500; margin-bottom: 8px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
                            Eje X:
                        </label>
                        <select id="${category}-x-metric" 
                            style="width: 100%; padding: 10px 14px; border: 1px solid ${theme.border}; border-radius: 6px; background-color: ${theme.background}; color: ${theme.text}; font-size: 13px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; outline: none; transition: all 0.2s;"
                            onmouseover="this.style.borderColor='${theme.lineColor}'"
                            onmouseout="this.style.borderColor='${theme.border}'"
                            onfocus="this.style.borderColor='${theme.lineColor}'; this.style.boxShadow='0 0 0 3px rgba(41, 98, 255, 0.1)'"
                            onblur="this.style.borderColor='${theme.border}'; this.style.boxShadow='none'">
                            ${availableMetrics.map(m => `<option value="${m.key}" ${m.key === defaultXMetric.key ? 'selected' : ''}>${m.label}</option>`).join('')}
                        </select>
                    </div>
                    <div>
                        <label style="display: block; color: ${theme.text}; font-size: 13px; font-weight: 500; margin-bottom: 8px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
                            Eje Y:
                        </label>
                        <select id="${category}-y-metric" 
                            style="width: 100%; padding: 10px 14px; border: 1px solid ${theme.border}; border-radius: 6px; background-color: ${theme.background}; color: ${theme.text}; font-size: 13px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; outline: none; transition: all 0.2s;"
                            onmouseover="this.style.borderColor='${theme.lineColor}'"
                            onmouseout="this.style.borderColor='${theme.border}'"
                            onfocus="this.style.borderColor='${theme.lineColor}'; this.style.boxShadow='0 0 0 3px rgba(41, 98, 255, 0.1)'"
                            onblur="this.style.borderColor='${theme.border}'; this.style.boxShadow='none'">
                            ${availableMetrics.map(m => `<option value="${m.key}" ${m.key === defaultYMetric.key ? 'selected' : ''}>${m.label}</option>`).join('')}
                        </select>
                    </div>
                </div>
                <div id="${category}-scatter-container" class="w-full"></div>
            </div>
            
            <!-- Bottom Right: Additional chart or metrics summary -->
            <div style="background-color: ${theme.panel}; border: 1px solid ${theme.border}; border-radius: 8px; padding: 20px;">
                <div class="flex items-center justify-between mb-4">
                    <h3 style="color: ${theme.text}; font-size: 18px; font-weight: 600; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
                        Resumen de Métricas
                    </h3>
                </div>
                <div id="${category}-summary-container" class="w-full" style="min-height: 400px;">
                    <!-- Summary will be generated here -->
                </div>
            </div>
        </div>
    `;
    
    // Store data for this category
    if (!window.chartData) window.chartData = {};
    window.chartData[category] = data;
    
    // Render initial charts
    renderTreemap(category, defaultXMetric);
    renderScatterChart(category, defaultXMetric, defaultYMetric);
    renderPriceHistory(category, defaultAsset.ticker, defaultAsset, '1y');
    renderSummary(category);
    
    // Add event listeners
    const treemapSelect = document.getElementById(`${category}-treemap-metric`);
    const xSelect = document.getElementById(`${category}-x-metric`);
    const ySelect = document.getElementById(`${category}-y-metric`);
    const assetSelect = document.getElementById(`${category}-asset-select`);
    const periodSelect = document.getElementById(`${category}-period-select`);
    
    treemapSelect?.addEventListener('change', (e) => {
        const metric = availableMetrics.find(m => m.key === e.target.value);
        if (metric) renderTreemap(category, metric);
    });
    
    xSelect?.addEventListener('change', (e) => {
        const xMetric = availableMetrics.find(m => m.key === e.target.value);
        const yMetric = availableMetrics.find(m => m.key === ySelect.value);
        if (xMetric && yMetric) renderScatterChart(category, xMetric, yMetric);
    });
    
    ySelect?.addEventListener('change', (e) => {
        const xMetric = availableMetrics.find(m => m.key === xSelect.value);
        const yMetric = availableMetrics.find(m => m.key === e.target.value);
        if (xMetric && yMetric) renderScatterChart(category, xMetric, yMetric);
    });
    
    assetSelect?.addEventListener('change', (e) => {
        const ticker = e.target.value;
        const asset = data.find(a => a.ticker === ticker);
        const period = periodSelect?.value || '1y';
        if (asset) {
            renderPriceHistory(category, ticker, asset, period);
        }
    });
    
    periodSelect?.addEventListener('change', (e) => {
        const ticker = assetSelect?.value || defaultAsset.ticker;
        const asset = data.find(a => a.ticker === ticker);
        const period = e.target.value;
        if (asset) {
            renderPriceHistory(category, ticker, asset, period);
        }
    });
};

function renderPriceHistory(category, ticker, assetData, period) {
    const chartContainer = document.getElementById(`${category}-price-chart-container`);
    const infoContainer = document.getElementById(`${category}-asset-info-container`);
    
    if (chartContainer) {
        createPriceHistoryChart(chartContainer, ticker, assetData, period);
    }
    
    if (infoContainer && assetData) {
        createAssetInfoPanel(infoContainer, assetData);
    }
}

function renderSummary(category) {
    const container = document.getElementById(`${category}-summary-container`);
    if (!container || !window.chartData || !window.chartData[category]) return;
    
    const data = window.chartData[category];
    const theme = getTheme();
    
    // Calculate averages and stats
    const metrics = ['pe_ratio', 'revenue_growth', 'profit_margin', 'return_on_equity', 'beta', 'rsi'];
    const stats = {};
    
    metrics.forEach(metric => {
        const values = data
            .map(asset => asset[metric])
            .filter(v => v !== null && v !== undefined && !isNaN(v));
        
        if (values.length > 0) {
            stats[metric] = {
                avg: values.reduce((a, b) => a + b, 0) / values.length,
                min: Math.min(...values),
                max: Math.max(...values),
                count: values.length
            };
        }
    });
    
    const metricLabels = {
        'pe_ratio': 'P/E Ratio',
        'revenue_growth': 'Revenue Growth',
        'profit_margin': 'Profit Margin',
        'return_on_equity': 'ROE',
        'beta': 'Beta',
        'rsi': 'RSI'
    };
    
    container.innerHTML = `
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px;">
            ${Object.keys(stats).map(metric => {
                const stat = stats[metric];
                const label = metricLabels[metric] || metric;
                const format = metric.includes('growth') || metric.includes('margin') || metric.includes('roe') 
                    ? (v) => (v * 100).toFixed(2) + '%'
                    : (v) => v.toFixed(2);
                
                return `
                    <div style="padding: 16px; background-color: ${theme.background}; border: 1px solid ${theme.border}; border-radius: 6px;">
                        <div style="color: ${theme.text}80; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
                            ${label}
                        </div>
                        <div style="color: ${theme.text}; font-size: 20px; font-weight: 700; margin-bottom: 4px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
                            ${format(stat.avg)}
                        </div>
                        <div style="color: ${theme.text}60; font-size: 12px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
                            Min: ${format(stat.min)} • Max: ${format(stat.max)}
                        </div>
                    </div>
                `;
            }).join('')}
        </div>
    `;
}

function renderTreemap(category, metric) {
    const container = document.getElementById(`${category}-treemap-container`);
    if (!container || !window.chartData || !window.chartData[category]) return;
    
    const data = window.chartData[category];
    createTreemapChart(container, data, metric, category);
}

function renderScatterChart(category, xMetric, yMetric) {
    const container = document.getElementById(`${category}-scatter-container`);
    if (!container || !window.chartData || !window.chartData[category]) return;
    
    const data = window.chartData[category];
    createScatterChart(container, data, xMetric, yMetric, category);
}

// Handle theme changes
document.addEventListener('DOMContentLoaded', () => {
    const observer = new MutationObserver(() => {
        // Re-render charts when theme changes
        if (window.chartData) {
            Object.keys(window.chartData).forEach(category => {
                const container = document.getElementById(`${category}-charts-container`);
                if (container && container.innerHTML) {
                    // Trigger re-render by finding current selections
                    const treemapSelect = document.getElementById(`${category}-treemap-metric`);
                    const xSelect = document.getElementById(`${category}-x-metric`);
                    const ySelect = document.getElementById(`${category}-y-metric`);
                    
                    if (treemapSelect) {
                        const metric = METRICS.numeric.find(m => m.key === treemapSelect.value);
                        if (metric) renderTreemap(category, metric);
                    }
                    
                    if (xSelect && ySelect) {
                        const xMetric = METRICS.numeric.find(m => m.key === xSelect.value);
                        const yMetric = METRICS.numeric.find(m => m.key === ySelect.value);
                        if (xMetric && yMetric) renderScatterChart(category, xMetric, yMetric);
                    }
                }
            });
        }
    });
    
    observer.observe(document.documentElement, {
        attributes: true,
        attributeFilter: ['class']
    });
});

