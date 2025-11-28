// BullAnalytics - Analysis Charts JavaScript

const API_BASE_URL = 'http://localhost:8080/api';

let treemapChart = null;
let barChart = null;
let lineChart = null;
let currentCategory = 'tracking';
let currentData = [];

// Initialize analysis tab
document.addEventListener('DOMContentLoaded', () => {
    const analisisTab = document.getElementById('analisis-tab');
    if (!analisisTab) return;

    // Category selector
    const categorySelect = document.getElementById('analisisCategory');
    if (categorySelect) {
        categorySelect.addEventListener('change', async (e) => {
            currentCategory = e.target.value;
            await loadAnalysisData();
        });
    }

    // Treemap metric buttons
    document.querySelectorAll('.treemap-metric').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.treemap-metric').forEach(b => {
                b.classList.remove('bg-gradient-to-r', 'from-green-500', 'to-green-600', 'text-white');
                b.classList.add('bg-white', 'dark:bg-gray-700', 'border', 'border-gray-300', 'dark:border-gray-600', 'text-gray-700', 'dark:text-gray-300');
            });
            btn.classList.remove('bg-white', 'dark:bg-gray-700', 'border', 'border-gray-300', 'dark:border-gray-600', 'text-gray-700', 'dark:text-gray-300');
            btn.classList.add('bg-gradient-to-r', 'from-green-500', 'to-green-600', 'text-white');
            updateTreemapChart(btn.getAttribute('data-metric'));
        });
    });

    // Bar chart metric buttons
    document.querySelectorAll('.bar-metric').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.bar-metric').forEach(b => {
                b.classList.remove('bg-gradient-to-r', 'from-green-500', 'to-green-600', 'text-white');
                b.classList.add('bg-white', 'dark:bg-gray-700', 'border', 'border-gray-300', 'dark:border-gray-600', 'text-gray-700', 'dark:text-gray-300');
            });
            btn.classList.remove('bg-white', 'dark:bg-gray-700', 'border', 'border-gray-300', 'dark:border-gray-600', 'text-gray-700', 'dark:text-gray-300');
            btn.classList.add('bg-gradient-to-r', 'from-green-500', 'to-green-600', 'text-white');
            updateBarChart(btn.getAttribute('data-metric'));
        });
    });

    // Line chart period buttons
    document.querySelectorAll('.line-period').forEach(btn => {
        btn.addEventListener('click', async () => {
            document.querySelectorAll('.line-period').forEach(b => {
                b.classList.remove('bg-gradient-to-r', 'from-green-500', 'to-green-600', 'text-white');
                b.classList.add('bg-white', 'dark:bg-gray-700', 'border', 'border-gray-300', 'dark:border-gray-600', 'text-gray-700', 'dark:text-gray-300');
            });
            btn.classList.remove('bg-white', 'dark:bg-gray-700', 'border', 'border-gray-300', 'dark:border-gray-600', 'text-gray-700', 'dark:text-gray-300');
            btn.classList.add('bg-gradient-to-r', 'from-green-500', 'to-green-600', 'text-white');
            const period = btn.getAttribute('data-period');
            const assetSelect = document.getElementById('lineChartAsset');
            if (assetSelect && assetSelect.value) {
                await loadLineChart(assetSelect.value, period);
            }
        });
    });

    // Line chart asset selector
    const assetSelect = document.getElementById('lineChartAsset');
    if (assetSelect) {
        assetSelect.addEventListener('change', async (e) => {
            const ticker = e.target.value;
            const activePeriod = document.querySelector('.line-period.bg-gradient-to-r')?.getAttribute('data-period') || '1y';
            if (ticker) {
                await loadLineChart(ticker, activePeriod);
            }
        });
    }

    // Load data when analysis tab is clicked
    const analisisTabButton = document.querySelector('[data-tab="analisis"]');
    if (analisisTabButton) {
        analisisTabButton.addEventListener('click', async () => {
            await updateCategorySelector();
            await loadAnalysisData();
        });
    }
});

// Update category selector with custom watchlists
async function updateCategorySelector() {
    const categorySelect = document.getElementById('analisisCategory');
    if (!categorySelect) return;

    try {
        const response = await fetch(`${API_BASE_URL}/watchlists`);
        if (!response.ok) return;

        const watchlists = await response.json();
        const watchlistNames = Object.keys(watchlists);

        // Remove existing custom watchlist options (keep default ones)
        const defaultOptions = ['tracking', 'portfolio', 'crypto', 'argentina'];
        Array.from(categorySelect.options).forEach(option => {
            if (!defaultOptions.includes(option.value)) {
                option.remove();
            }
        });

        // Add custom watchlist options
        watchlistNames.forEach(name => {
            const option = document.createElement('option');
            option.value = name;
            option.textContent = name;
            categorySelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error updating category selector:', error);
    }
}

async function loadAnalysisData() {
    try {
        let endpoint = '';
        switch (currentCategory) {
            case 'tracking':
                endpoint = '/tracking-assets';
                break;
            case 'portfolio':
                endpoint = '/portfolio-assets';
                break;
            case 'crypto':
                endpoint = '/crypto-assets';
                break;
            case 'argentina':
                endpoint = '/argentina-assets';
                break;
            default:
                // Try custom watchlist
                endpoint = `/watchlist/${currentCategory}`;
        }

        const response = await fetch(`${API_BASE_URL}${endpoint}`);
        if (!response.ok) {
            throw new Error('Error loading data');
        }

        currentData = await response.json();
        
        // Filter out crypto if needed (for non-crypto categories)
        const isCryptoCategory = currentCategory === 'crypto';
        const filteredData = isCryptoCategory ? currentData : currentData.filter(asset => {
            // Check if it's a crypto ticker
            return !asset.ticker.includes('-USD');
        });

        // Update charts
        updateTreemapChart('market_cap');
        updateBarChart('revenue_growth');
        
        // Update line chart asset selector
        updateLineChartSelector(filteredData);

    } catch (error) {
        console.error('Error loading analysis data:', error);
    }
}

function updateTreemapChart(metric) {
    const ctx = document.getElementById('treemapChart');
    if (!ctx) return;

    // Update title
    const titleEl = document.getElementById('treemapTitle');
    if (titleEl) {
        if (metric === 'market_cap') {
            titleEl.textContent = 'Treemap - Capitalización Bursátil';
        } else if (metric === 'cash_flow') {
            const isCrypto = currentCategory === 'crypto';
            titleEl.textContent = isCrypto ? 'Treemap - Volumen' : 'Treemap - Cash Flow';
        }
    }
    
    // Load chart image from backend
    const img = document.createElement('img');
    img.src = `${API_BASE_URL}/chart/treemap?category=${currentCategory}&metric=${metric}`;
    img.className = 'w-full h-full object-contain';
    img.alt = 'Treemap Chart';
    img.onerror = () => {
        ctx.innerHTML = '<div class="flex items-center justify-center h-full text-gray-500 dark:text-gray-400">Error al cargar el gráfico</div>';
    };
    
    ctx.innerHTML = '';
    ctx.appendChild(img);

    // Destroy existing chart
    if (treemapChart) {
        treemapChart.destroy();
    }

    // Prepare data
    const chartData = data.map(asset => {
        let value = 0;
        if (metric === 'market_cap') {
            value = asset.market_cap || 0;
        } else if (metric === 'cash_flow') {
            // For crypto, cash flow is not available, use volume as alternative
            if (isCrypto) {
                value = asset.volume || 0;
            } else {
                value = Math.abs(asset.cash_flow || 0);
            }
        }

        return {
            x: asset.ticker,
            y: value,
            v: value
        };
    }).filter(item => item.y > 0);

    if (chartData.length === 0) {
        ctx.innerHTML = '<div class="flex items-center justify-center h-full text-gray-500 dark:text-gray-400">No hay datos disponibles para esta métrica</div>';
        return;
    }

    // Create canvas if needed
    if (!ctx.querySelector('canvas')) {
        ctx.innerHTML = '<canvas></canvas>';
    }

    const isDark = document.documentElement.classList.contains('dark');
    const textColor = isDark ? '#e5e7eb' : '#374151';
    const bgColor = isDark ? '#1f2937' : '#ffffff';

    // Sort data by value (descending)
    chartData.sort((a, b) => b.v - a.v);

    const labels = chartData.map(d => d.x);
    const values = chartData.map(d => d.v);
    const maxValue = Math.max(...values);

    treemapChart = new Chart(ctx.querySelector('canvas'), {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: (metric === 'market_cap' ? 'Capitalización Bursátil' : 
                       (isCrypto && metric === 'cash_flow' ? 'Volumen' : 'Cash Flow')),
                data: values,
                backgroundColor: (ctx) => {
                    const value = ctx.parsed.y;
                    const ratio = value / maxValue;
                    // Gradient from light green to dark green
                    const r = Math.floor(40 + (ratio * 215));
                    const g = Math.floor(167 + (ratio * 88));
                    const b = Math.floor(69 + (ratio * 186));
                    return `rgba(${r}, ${g}, ${b}, 0.7)`;
                },
                borderColor: (ctx) => {
                    const value = ctx.parsed.y;
                    const ratio = value / maxValue;
                    const r = Math.floor(40 + (ratio * 215));
                    const g = Math.floor(167 + (ratio * 88));
                    const b = Math.floor(69 + (ratio * 186));
                    return `rgba(${r}, ${g}, ${b}, 1)`;
                },
                borderWidth: 2
            }]
        },
        options: {
            indexAxis: 'y',
            maintainAspectRatio: false,
            responsive: true,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: (context) => {
                            const asset = data.find(a => a.ticker === context.label);
                            const formatted = formatLargeNumber(context.parsed.y);
                            const metricLabel = (metric === 'cash_flow' && isCrypto) ? 'Volumen' : 
                                               (metric === 'market_cap' ? 'Capitalización' : 'Cash Flow');
                            return `${asset?.name || context.label}: ${formatted} (${metricLabel})`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: {
                        color: textColor,
                        callback: (value) => formatLargeNumber(value)
                    },
                    grid: {
                        color: bgColor === '#ffffff' ? '#e5e7eb' : '#374151'
                    }
                },
                y: {
                    ticks: {
                        color: textColor
                    },
                    grid: {
                        color: bgColor === '#ffffff' ? '#e5e7eb' : '#374151'
                    }
                }
            }
        }
    });
}

function updateBarChart(metric) {
    const ctx = document.getElementById('barChart');
    if (!ctx || !currentData || currentData.length === 0) return;

    const isCrypto = currentCategory === 'crypto';
    let data = currentData;
    
    // For crypto, show all data. For others, filter out crypto tickers
    if (!isCrypto) {
        data = currentData.filter(a => !a.ticker.includes('-USD'));
    }

    if (data.length === 0) {
        ctx.innerHTML = '<div class="flex items-center justify-center h-full text-gray-500 dark:text-gray-400">No hay datos disponibles</div>';
        return;
    }

    // Destroy existing chart
    if (barChart) {
        barChart.destroy();
    }

    // Update title
    const titleEl = document.getElementById('barChartTitle');
    if (titleEl) {
        const titles = {
            'revenue_growth': 'Revenue Growth (%)',
            'profit_margin': 'Profit Margin (%)',
            'roe': 'Return on Equity (ROE) (%)',
            'pe': 'P/E Ratio',
            'diff_max': 'Diferencia vs Máximo (%)'
        };
        titleEl.textContent = `Gráfico de Barras - ${titles[metric] || metric}`;
    }

    // Prepare data - filter out crypto for fundamental metrics
    let filteredData = data;
    if ((metric === 'pe' || metric === 'revenue_growth' || metric === 'profit_margin' || metric === 'roe') && isCrypto) {
        ctx.innerHTML = '<div class="flex items-center justify-center h-full text-gray-500 dark:text-gray-400">Esta métrica no está disponible para criptomonedas</div>';
        return;
    }

    // Sort by value for better visualization
    filteredData.sort((a, b) => {
        let aVal = 0, bVal = 0;
        if (metric === 'diff_max') {
            aVal = a.diff_from_max || 0;
            bVal = b.diff_from_max || 0;
        } else if (metric === 'pe') {
            aVal = a.pe_ratio || 0;
            bVal = b.pe_ratio || 0;
        } else if (metric === 'revenue_growth') {
            aVal = a.revenue_growth || 0;
            bVal = b.revenue_growth || 0;
        } else if (metric === 'profit_margin') {
            aVal = a.profit_margin || 0;
            bVal = b.profit_margin || 0;
        } else if (metric === 'roe') {
            aVal = a.return_on_equity || 0;
            bVal = b.return_on_equity || 0;
        }
        return bVal - aVal;
    });

    const labels = filteredData.map(asset => asset.ticker);
    const values = filteredData.map(asset => {
        if (metric === 'diff_max') {
            return parseFloat((asset.diff_from_max * 100).toFixed(2));
        } else if (metric === 'pe') {
            return asset.pe_ratio || 0;
        } else if (metric === 'revenue_growth') {
            return asset.revenue_growth ? parseFloat((asset.revenue_growth * 100).toFixed(2)) : 0;
        } else if (metric === 'profit_margin') {
            return asset.profit_margin ? parseFloat((asset.profit_margin * 100).toFixed(2)) : 0;
        } else if (metric === 'roe') {
            return asset.return_on_equity ? parseFloat((asset.return_on_equity * 100).toFixed(2)) : 0;
        }
        return 0;
    });

    // Create canvas if needed
    if (!ctx.querySelector('canvas')) {
        ctx.innerHTML = '<canvas></canvas>';
    }

    const isDark = document.documentElement.classList.contains('dark');
    const textColor = isDark ? '#e5e7eb' : '#374151';
    const gridColor = isDark ? '#374151' : '#e5e7eb';

    barChart = new Chart(ctx.querySelector('canvas'), {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: metric === 'diff_max' ? 'Diferencia vs Máximo (%)' : 'P/E Ratio',
                data: values,
                backgroundColor: (ctx) => {
                    const value = ctx.parsed.y;
                    if (metric === 'diff_max') {
                        return value >= 0 ? 'rgba(34, 197, 94, 0.7)' : 'rgba(239, 68, 68, 0.7)';
                    } else if (metric === 'revenue_growth' || metric === 'profit_margin' || metric === 'roe') {
                        return value >= 0 ? 'rgba(34, 197, 94, 0.7)' : 'rgba(239, 68, 68, 0.7)';
                    }
                    return 'rgba(34, 197, 94, 0.7)';
                },
                borderColor: (ctx) => {
                    const value = ctx.parsed.y;
                    if (metric === 'diff_max') {
                        return value >= 0 ? 'rgba(34, 197, 94, 1)' : 'rgba(239, 68, 68, 1)';
                    } else if (metric === 'revenue_growth' || metric === 'profit_margin' || metric === 'roe') {
                        return value >= 0 ? 'rgba(34, 197, 94, 1)' : 'rgba(239, 68, 68, 1)';
                    }
                    return 'rgba(34, 197, 94, 1)';
                },
                borderWidth: 2
            }]
        },
        options: {
            maintainAspectRatio: false,
            responsive: true,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: (context) => {
                            const asset = filteredData[context.dataIndex];
                            const value = context.parsed.y;
                            if (metric === 'diff_max' || metric === 'revenue_growth' || metric === 'profit_margin' || metric === 'roe') {
                                return `${asset.name}: ${value}%`;
                            }
                            return `${asset.name}: ${value.toFixed(2)}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: textColor
                    },
                    grid: {
                        color: gridColor
                    }
                },
                x: {
                    ticks: {
                        color: textColor
                    },
                    grid: {
                        color: gridColor
                    }
                }
            }
        }
    });
}

async function loadLineChart(ticker, period) {
    const ctx = document.getElementById('lineChart');
    if (!ctx || !ticker) return;

    // Load chart image from backend
    const img = document.createElement('img');
    img.src = `${API_BASE_URL}/chart/line?ticker=${ticker}&period=${period}`;
    img.className = 'w-full h-full object-contain';
    img.alt = 'Line Chart';
    img.onerror = () => {
        ctx.innerHTML = '<div class="flex items-center justify-center h-full text-gray-500 dark:text-gray-400">Error al cargar el gráfico</div>';
    };
    
    ctx.innerHTML = '';
    ctx.appendChild(img);
}

function updateLineChartSelector(data) {
    const select = document.getElementById('lineChartAsset');
    if (!select) return;

    select.innerHTML = '<option value="">Selecciona un activo</option>';
    data.forEach(asset => {
        const option = document.createElement('option');
        option.value = asset.ticker;
        option.textContent = asset.name;
        select.appendChild(option);
    });
}

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

