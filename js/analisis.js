// BullAnalytics - Analysis Charts with React and Plotly

const API_BASE_URL = 'http://localhost:8080/api';

let currentCategory = 'tracking';
let currentData = [];

// React Components for Charts
const { useState, useEffect, useRef } = React;

// Treemap Chart Component
function TreemapChart({ data, metric, category }) {
    const chartRef = useRef(null);

    useEffect(() => {
        if (!data || data.length === 0 || !chartRef.current) return;

        const isCrypto = category === 'crypto';
        let chartData = data;

        // Filter out crypto for non-crypto categories
        if (!isCrypto) {
            chartData = data.filter(asset => !asset.ticker?.includes('-USD'));
        }

        // Fetch chart data from backend
        fetch(`${API_BASE_URL}/chart/treemap?category=${category}&metric=${metric}`)
            .then(res => res.json())
            .then(chartData => {
                if (!chartData.labels || chartData.labels.length === 0) {
                    chartRef.current.innerHTML = '<div class="flex items-center justify-center h-full text-gray-500 dark:text-gray-400">No hay datos disponibles</div>';
                    return;
                }

                const plotData = [{
                    type: 'treemap',
                    labels: chartData.labels,
                    parents: chartData.labels.map(() => ''),
                    values: chartData.values,
                    textinfo: 'label+value',
                    texttemplate: '<b>%{label}</b><br>%{value:,.0f}',
                    hovertemplate: '<b>%{label}</b><br>%{value:,.0f}<extra></extra>',
                    marker: {
                        colors: chartData.values,
                        colorscale: 'Greens',
                        showscale: true,
                        colorbar: {
                            title: metric === 'market_cap' ? 'Capitalización' : (chartData.is_crypto ? 'Volumen' : 'Cash Flow')
                        }
                    }
                }];

                const layout = {
                    title: {
                        text: metric === 'market_cap' 
                            ? 'Capitalización Bursátil' 
                            : (chartData.is_crypto ? 'Volumen' : 'Cash Flow'),
                        font: { size: 16 }
                    },
                    paper_bgcolor: 'rgba(0,0,0,0)',
                    plot_bgcolor: 'rgba(0,0,0,0)',
                    font: {
                        color: document.documentElement.classList.contains('dark') ? '#e5e7eb' : '#374151'
                    }
                };

                const config = {
                    responsive: true,
                    displayModeBar: true,
                    modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d'],
                    displaylogo: false
                };

                Plotly.newPlot(chartRef.current, plotData, layout, config);
            })
            .catch(error => {
                console.error('Error loading treemap chart:', error);
                chartRef.current.innerHTML = '<div class="flex items-center justify-center h-full text-red-500 dark:text-red-400">Error al cargar el gráfico</div>';
            });
    }, [data, metric, category]);

    return <div ref={chartRef} style={{ width: '100%', height: '100%' }} />;
}

// Bar Chart Component
function BarChart({ data, metric, category }) {
    const chartRef = useRef(null);

    useEffect(() => {
        if (!data || data.length === 0 || !chartRef.current) return;

        const isCrypto = category === 'crypto';

        // Check if metric is available for crypto
        if ((metric === 'pe' || metric === 'revenue_growth' || metric === 'profit_margin' || metric === 'roe') && isCrypto) {
            chartRef.current.innerHTML = '<div class="flex items-center justify-center h-full text-gray-500 dark:text-gray-400">Esta métrica no está disponible para criptomonedas</div>';
            return;
        }

        // Fetch chart data from backend
        fetch(`${API_BASE_URL}/chart/bar?category=${category}&metric=${metric}`)
            .then(res => res.json())
            .then(chartData => {
                if (!chartData.labels || chartData.labels.length === 0) {
                    chartRef.current.innerHTML = '<div class="flex items-center justify-center h-full text-gray-500 dark:text-gray-400">No hay datos disponibles</div>';
                    return;
                }

                const plotData = [{
                    type: 'bar',
                    x: chartData.values,
                    y: chartData.labels,
                    orientation: 'h',
                    marker: {
                        color: chartData.colors,
                        line: {
                            color: chartData.colors.map(c => c.replace('0.7', '1')),
                            width: 1
                        }
                    },
                    text: chartData.values.map(val => val.toFixed(2)),
                    textposition: 'auto',
                    hovertemplate: '<b>%{y}</b><br>%{x:.2f}<extra></extra>'
                }];

                const layout = {
                    title: {
                        text: chartData.metric_title || metric,
                        font: { size: 16 }
                    },
                    xaxis: {
                        title: chartData.metric_title || metric,
                        showgrid: true,
                        gridcolor: document.documentElement.classList.contains('dark') ? '#374151' : '#e5e7eb'
                    },
                    yaxis: {
                        showgrid: true,
                        gridcolor: document.documentElement.classList.contains('dark') ? '#374151' : '#e5e7eb'
                    },
                    paper_bgcolor: 'rgba(0,0,0,0)',
                    plot_bgcolor: 'rgba(0,0,0,0)',
                    font: {
                        color: document.documentElement.classList.contains('dark') ? '#e5e7eb' : '#374151'
                    },
                    margin: { l: 150, r: 50, t: 50, b: 50 }
                };

                const config = {
                    responsive: true,
                    displayModeBar: true,
                    modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d'],
                    displaylogo: false
                };

                Plotly.newPlot(chartRef.current, plotData, layout, config);
            })
            .catch(error => {
                console.error('Error loading bar chart:', error);
                chartRef.current.innerHTML = '<div class="flex items-center justify-center h-full text-red-500 dark:text-red-400">Error al cargar el gráfico</div>';
            });
    }, [data, metric, category]);

    return <div ref={chartRef} style={{ width: '100%', height: '100%' }} />;
}

// Line Chart Component
function LineChart({ ticker, period }) {
    const chartRef = useRef(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (!ticker || !chartRef.current) return;

        setLoading(true);
        
        // Use the chart endpoint that returns Plotly data
        fetch(`${API_BASE_URL}/chart/line?ticker=${ticker}&period=${period}`)
            .then(res => res.json())
            .then(chartData => {
                if (!chartData.dates || chartData.dates.length === 0) {
                    chartRef.current.innerHTML = '<div class="flex items-center justify-center h-full text-gray-500 dark:text-gray-400">No hay datos disponibles para este período</div>';
                    setLoading(false);
                    return;
                }

                const plotData = [{
                    type: 'scatter',
                    mode: 'lines',
                    x: chartData.dates,
                    y: chartData.prices,
                    line: {
                        color: 'rgba(34, 197, 94, 1)',
                        width: 2
                    },
                    fill: 'tozeroy',
                    fillcolor: 'rgba(34, 197, 94, 0.2)',
                    hovertemplate: '<b>%{x}</b><br>Precio: $%{y:.2f}<extra></extra>'
                }];

                const layout = {
                    title: {
                        text: `Precio Histórico - ${chartData.ticker}`,
                        font: { size: 16 }
                    },
                    xaxis: {
                        title: 'Fecha',
                        showgrid: true,
                        gridcolor: document.documentElement.classList.contains('dark') ? '#374151' : '#e5e7eb'
                    },
                    yaxis: {
                        title: 'Precio (USD)',
                        showgrid: true,
                        gridcolor: document.documentElement.classList.contains('dark') ? '#374151' : '#e5e7eb'
                    },
                    paper_bgcolor: 'rgba(0,0,0,0)',
                    plot_bgcolor: 'rgba(0,0,0,0)',
                    font: {
                        color: document.documentElement.classList.contains('dark') ? '#e5e7eb' : '#374151'
                    }
                };

                const config = {
                    responsive: true,
                    displayModeBar: true,
                    modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d'],
                    displaylogo: false
                };

                Plotly.newPlot(chartRef.current, plotData, layout, config);
                setLoading(false);
            })
            .catch(error => {
                console.error('Error loading line chart:', error);
                chartRef.current.innerHTML = '<div class="flex items-center justify-center h-full text-red-500 dark:text-red-400">Error al cargar el gráfico</div>';
                setLoading(false);
            });
    }, [ticker, period]);

    if (loading) {
        return <div className="flex items-center justify-center h-full text-gray-500 dark:text-gray-400">Cargando...</div>;
    }

    return <div ref={chartRef} style={{ width: '100%', height: '100%' }} />;
}

// Main Analysis Component
function AnalysisCharts() {
    const [category, setCategory] = useState('tracking');
    const [data, setData] = useState([]);
    const [treemapMetric, setTreemapMetric] = useState('market_cap');
    const [barMetric, setBarMetric] = useState('revenue_growth');
    const [lineTicker, setLineTicker] = useState('');
    const [linePeriod, setLinePeriod] = useState('1y');
    const [lineChartAssets, setLineChartAssets] = useState([]);

    // Load data when category changes
    useEffect(() => {
        loadAnalysisData(category);
    }, [category]);

    // Update line chart assets when data changes
    useEffect(() => {
        if (data && data.length > 0) {
            const isCrypto = category === 'crypto';
            const filteredData = isCrypto ? data : data.filter(asset => !asset.ticker?.includes('-USD'));
            setLineChartAssets(filteredData);
            
            // Set first asset as default if none selected
            if (!lineTicker && filteredData.length > 0) {
                setLineTicker(filteredData[0].ticker);
            }
        }
    }, [data, category]);

    async function loadAnalysisData(cat) {
        try {
            let endpoint = '';
            switch (cat) {
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
                    endpoint = `/watchlist/${cat}`;
            }

            const response = await fetch(`${API_BASE_URL}${endpoint}`);
            if (!response.ok) {
                throw new Error('Error loading data');
            }

            const result = await response.json();
            setData(result);
            currentCategory = cat;
            currentData = result;
        } catch (error) {
            console.error('Error loading analysis data:', error);
            setData([]);
        }
    }

    // Update category selector with custom watchlists
    useEffect(() => {
        async function updateCategorySelector() {
            const categorySelect = document.getElementById('analisisCategory');
            if (!categorySelect) return;

            try {
                const response = await fetch(`${API_BASE_URL}/watchlists`);
                if (!response.ok) return;

                const watchlists = await response.json();
                const watchlistNames = Object.keys(watchlists);
                
                // Remove existing custom watchlist options
                const existingOptions = Array.from(categorySelect.querySelectorAll('option'));
                existingOptions.forEach(opt => {
                    if (!['tracking', 'portfolio', 'crypto', 'argentina', 'analisis'].includes(opt.value)) {
                        opt.remove();
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

        updateCategorySelector();
    }, []);

    // Sync category with external selector on mount and when it changes
    useEffect(() => {
        const categorySelect = document.getElementById('analisisCategory');
        if (categorySelect) {
            const selectedCategory = categorySelect.value || 'tracking';
            if (selectedCategory !== category) {
                setCategory(selectedCategory);
            }
            
            // Listen for external changes to the selector
            const handleChange = (e) => {
                if (e.target.value !== category) {
                    setCategory(e.target.value);
                }
            };
            categorySelect.addEventListener('change', handleChange);
            return () => categorySelect.removeEventListener('change', handleChange);
        }
    }, [category]);

    return (
        <div className="space-y-6">
            {/* Treemap Chart */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 p-6">
                <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4">
                    {treemapMetric === 'market_cap' 
                        ? 'Treemap - Capitalización Bursátil' 
                        : (category === 'crypto' ? 'Treemap - Volumen' : 'Treemap - Cash Flow')}
                </h3>
                <div className="flex gap-4 mb-4">
                    <button 
                        className={`px-4 py-2 rounded-lg font-semibold text-sm transition-all ${
                            treemapMetric === 'market_cap'
                                ? 'bg-gradient-to-r from-green-500 to-green-600 text-white'
                                : 'bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600'
                        }`}
                        onClick={() => setTreemapMetric('market_cap')}
                    >
                        Capitalización Bursátil
                    </button>
                    <button 
                        className={`px-4 py-2 rounded-lg font-semibold text-sm transition-all ${
                            treemapMetric === 'cash_flow'
                                ? 'bg-gradient-to-r from-green-500 to-green-600 text-white'
                                : 'bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600'
                        }`}
                        onClick={() => setTreemapMetric('cash_flow')}
                    >
                        {category === 'crypto' ? 'Volumen' : 'Cash Flow'}
                    </button>
                </div>
                <div className="h-96">
                    {data.length > 0 ? (
                        <TreemapChart data={data} metric={treemapMetric} category={category} />
                    ) : (
                        <div className="flex items-center justify-center h-full text-gray-500 dark:text-gray-400">
                            Selecciona una categoría para ver el gráfico
                        </div>
                    )}
                </div>
            </div>

            {/* Bar Chart */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 p-6">
                <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4">Gráfico de Barras</h3>
                <div className="flex flex-wrap gap-2 mb-4">
                    {['revenue_growth', 'profit_margin', 'roe', 'pe', 'diff_max'].map(metric => (
                        <button
                            key={metric}
                            className={`px-4 py-2 rounded-lg font-semibold text-sm transition-all ${
                                barMetric === metric
                                    ? 'bg-gradient-to-r from-green-500 to-green-600 text-white'
                                    : 'bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600'
                            }`}
                            onClick={() => setBarMetric(metric)}
                        >
                            {metric === 'revenue_growth' ? 'Revenue Growth' :
                             metric === 'profit_margin' ? 'Profit Margin' :
                             metric === 'roe' ? 'ROE' :
                             metric === 'pe' ? 'P/E Ratio' :
                             'Diff vs Máx'}
                        </button>
                    ))}
                </div>
                <div className="h-96">
                    {data.length > 0 ? (
                        <BarChart data={data} metric={barMetric} category={category} />
                    ) : (
                        <div className="flex items-center justify-center h-full text-gray-500 dark:text-gray-400">
                            Selecciona una categoría para ver el gráfico
                        </div>
                    )}
                </div>
            </div>

            {/* Line Chart */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 p-6">
                <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4">Gráfico de Líneas - Precio Histórico</h3>
                <div className="flex flex-wrap items-center gap-4 mb-4">
                    <select 
                        value={lineTicker}
                        onChange={(e) => setLineTicker(e.target.value)}
                        className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all"
                    >
                        <option value="">Selecciona un activo</option>
                        {lineChartAssets.map(asset => (
                            <option key={asset.ticker} value={asset.ticker}>
                                {asset.name || asset.ticker}
                            </option>
                        ))}
                    </select>
                    <div className="flex gap-2">
                        {['1d', '5d', '1mo', '6mo', '1y', 'max'].map(period => (
                            <button
                                key={period}
                                className={`px-3 py-2 rounded-lg font-semibold text-sm transition-all ${
                                    linePeriod === period
                                        ? 'bg-gradient-to-r from-green-500 to-green-600 text-white'
                                        : 'bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600'
                                }`}
                                onClick={() => setLinePeriod(period)}
                            >
                                {period === '1d' ? '1 día' :
                                 period === '5d' ? '5 D' :
                                 period === '1mo' ? '1 mes' :
                                 period === '6mo' ? '6 M' :
                                 period === '1y' ? '1 año' :
                                 'MÁX'}
                            </button>
                        ))}
                    </div>
                </div>
                <div className="h-96">
                    {lineTicker ? (
                        <LineChart ticker={lineTicker} period={linePeriod} />
                    ) : (
                        <div className="flex items-center justify-center h-full text-gray-500 dark:text-gray-400">
                            Selecciona un activo para ver el gráfico
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const analisisTab = document.getElementById('analisis-tab');
    if (!analisisTab) return;

    // Find or create root element
    let root = document.getElementById('analysis-charts-root');
    if (!root) {
        root = document.createElement('div');
        root.id = 'analysis-charts-root';
        // Find the container after the category selector
        const categoryContainer = analisisTab.querySelector('.mb-6');
        if (categoryContainer && categoryContainer.nextSibling) {
            categoryContainer.parentNode.insertBefore(root, categoryContainer.nextSibling);
        } else {
            analisisTab.appendChild(root);
        }
    }

    // Category selector handler - sync with React component
    const categorySelect = document.getElementById('analisisCategory');
    if (categorySelect) {
        categorySelect.addEventListener('change', (e) => {
            currentCategory = e.target.value;
            // Re-render React component with new category
            const root = document.getElementById('analysis-charts-root');
            if (root) {
                ReactDOM.render(<AnalysisCharts />, root);
            }
        });
    }

    // Initial render
    ReactDOM.render(<AnalysisCharts />, root);
});

// Export for use in dashboard.js
window.loadAnalysisData = async function(category) {
    currentCategory = category;
    const categorySelect = document.getElementById('analisisCategory');
    if (categorySelect) {
        categorySelect.value = category;
    }
    const root = document.getElementById('analysis-charts-root');
    if (root) {
        ReactDOM.render(<AnalysisCharts />, root);
    }
};
