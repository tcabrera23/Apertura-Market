// Calendar Page JavaScript

// const API_BASE_URL = 'http://localhost:8080/api'; // Development
const API_BASE_URL = 'https://api.bullanalytics.io/api'; // Production

// Cache System for Calendar
const CACHE_DURATION = 120000; // 2 minutes
const CACHE_KEY = 'bullanalytics_calendar_cache';
let calendarCache = { data: {}, timestamp: 0, year: null, month: null, insights: {} };

// Chart instances
let epsChart = null;
let revChart = null;

// Current Tab
let currentTab = 'all'; // all, good, neutral, bad

// Load cache
try {
    const saved = localStorage.getItem(CACHE_KEY);
    if (saved) {
        const parsed = JSON.parse(saved);
        if (!parsed.insights) parsed.insights = {};
        calendarCache = parsed;
    }
} catch (e) { console.error('Error loading calendar cache:', e); }

function persistCache() {
    try {
        localStorage.setItem(CACHE_KEY, JSON.stringify(calendarCache));
    } catch (e) { console.warn('Error saving calendar cache:', e); }
}

function saveCache(data, year, month) {
    if (calendarCache.year !== year || calendarCache.month !== month) {
        calendarCache.insights = {};
    }
    calendarCache.data = data;
    calendarCache.timestamp = Date.now();
    calendarCache.year = year;
    calendarCache.month = month;
    persistCache();
}

function isCacheValid(year, month) {
    if (calendarCache.year !== year || calendarCache.month !== month) return false;
    if (!calendarCache.data) return false;
    return (Date.now() - calendarCache.timestamp) < CACHE_DURATION;
}

console.log('calendar.js loaded');

// Current date tracking
let currentDate = new Date();
let currentYear = currentDate.getFullYear();
let currentMonth = currentDate.getMonth() + 1; // 1-12

// Current tab for analyst insights
let currentTab = 'all';

// Month names in Spanish
const monthNames = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
];

const dayNames = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];

// Check if mobile device
function isMobile() {
    return window.innerWidth < 768; // md breakpoint in Tailwind
}

// Load calendar data
async function loadCalendar() {
    try {
        // Check cache first
        if (isCacheValid(currentYear, currentMonth)) {
            console.log('Using cached calendar data');
            const data = calendarCache.data;
            renderCalendar(data);
            renderEventsList(data);
            // We also need to handle analyst insights caching if needed, 
            // but for now let's just re-fetch insights or cache them inside the main object if possible.
            // The original code calls loadAnalystInsights(data).
            // Let's call it here too.
            loadAnalystInsights(data); 
            return;
        }

        const response = await fetch(`${API_BASE_URL}/earnings-calendar?year=${currentYear}&month=${currentMonth}`);
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            const errorMessage = errorData.detail || 'Error al cargar el calendario';
            throw new Error(errorMessage);
        }
        
        const data = await response.json();
        console.log('Calendar data loaded:', data);
        
        // Save to cache
        saveCache(data, currentYear, currentMonth);

        renderCalendar(data);
        renderEventsList(data);
        
        // Load analyst insights immediately
        console.log('About to call loadAnalystInsights');
        try {
            await loadAnalystInsights(data);
        } catch (error) {
            console.error('Error in loadAnalystInsights call:', error);
        }
    } catch (error) {
        console.error('Error loading calendar:', error);
        
        // If fetch fails but we have some cache (even if expired or different month? no, only if same month), use it
        if (calendarCache.year === currentYear && calendarCache.month === currentMonth && calendarCache.data) {
             console.log('Using expired/cached calendar data due to error');
             const data = calendarCache.data;
             renderCalendar(data);
             renderEventsList(data);
             loadAnalystInsights(data);
             return;
        }

        document.getElementById('calendarContainer').innerHTML = `
            <div class="col-span-7 text-center py-8 text-red-500">
                <p>Error al cargar el calendario. Por favor, intenta de nuevo.</p>
            </div>
        `;
    }
}

// Render calendar grid
function renderCalendar(data) {
    const container = document.getElementById('calendarContainer');
    const events = data.events || {};
    
    // Update month/year display
    document.getElementById('currentMonth').textContent = monthNames[currentMonth - 1];
    document.getElementById('currentYear').textContent = currentYear;
    
    // Get first day of month and number of days
    const firstDay = new Date(currentYear, currentMonth - 1, 1).getDay();
    const daysInMonth = new Date(currentYear, currentMonth, 0).getDate();
    
    // Clear container
    container.innerHTML = '';
    
    // Add day headers
    dayNames.forEach(day => {
        const header = document.createElement('div');
        header.className = 'text-center font-semibold text-gray-700 dark:text-gray-300 py-2';
        header.textContent = day;
        container.appendChild(header);
    });
    
    // Add empty cells for days before month starts
    for (let i = 0; i < firstDay; i++) {
        const emptyCell = document.createElement('div');
        emptyCell.className = 'aspect-square';
        container.appendChild(emptyCell);
    }
    
    // Add day cells - reduced height by 30% (from ~80px to ~56px)
    for (let day = 1; day <= daysInMonth; day++) {
        const dayCell = document.createElement('div');
        dayCell.className = 'min-h-[56px] border border-gray-200 dark:border-gray-700 rounded-lg p-2 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors cursor-pointer';
        
        const dateKey = `${currentYear}-${String(currentMonth).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        const dayEvents = events[dateKey] || [];
        
        // Day number
        const dayNumber = document.createElement('div');
        dayNumber.className = 'text-sm font-semibold text-gray-900 dark:text-white mb-1';
        dayNumber.textContent = day;
        dayCell.appendChild(dayNumber);
        
        // Events indicators
        if (dayEvents.length > 0) {
            const eventsIndicator = document.createElement('div');
            eventsIndicator.className = 'flex flex-wrap gap-1 mt-1';
            
            if (isMobile()) {
                // Mobile: only show count
                const countBadge = document.createElement('span');
                countBadge.className = 'px-2 py-0.5 text-xs font-semibold bg-green-500 text-white rounded-full';
                countBadge.textContent = dayEvents.length.toString();
                countBadge.title = `${dayEvents.length} ${dayEvents.length === 1 ? 'evento' : 'eventos'}: ${dayEvents.map(e => e.ticker).join(', ')}`;
                eventsIndicator.appendChild(countBadge);
            } else {
                // Desktop: show tickers (up to 3) + count if more
                dayEvents.slice(0, 3).forEach(event => {
                    const badge = document.createElement('span');
                    badge.className = 'px-2 py-0.5 text-xs font-semibold bg-green-500 text-white rounded-full';
                    badge.textContent = event.ticker;
                    badge.title = `${event.name} - ${event.ticker}`;
                    eventsIndicator.appendChild(badge);
                });
                
                if (dayEvents.length > 3) {
                    const moreBadge = document.createElement('span');
                    moreBadge.className = 'px-2 py-0.5 text-xs font-semibold bg-green-600 text-white rounded-full';
                    moreBadge.textContent = `+${dayEvents.length - 3}`;
                    eventsIndicator.appendChild(moreBadge);
                }
            }
            
            dayCell.appendChild(eventsIndicator);
            dayCell.classList.add('bg-green-50');
            dayCell.classList.add('dark:bg-green-900/20');
        }
        
        // Click handler to show events
        dayCell.addEventListener('click', () => {
            if (dayEvents.length > 0) {
                showDayEvents(dateKey, dayEvents);
            }
        });
        
        container.appendChild(dayCell);
    }
}

// Render events list
function renderEventsList(data) {
    const container = document.getElementById('eventsContainer');
    const events = data.events || {};
    
    if (Object.keys(events).length === 0) {
        container.innerHTML = `
            <div class="text-center py-8 text-gray-500 dark:text-gray-400">
                <p>No hay eventos de resultados programados para este mes.</p>
            </div>
        `;
        return;
    }
    
    // Sort dates
    const sortedDates = Object.keys(events).sort();
    
    container.innerHTML = sortedDates.map(dateKey => {
        const dayEvents = events[dateKey];
        const date = new Date(dateKey);
        const dayName = dayNames[date.getDay()];
        const day = date.getDate();
        
        return `
            <div class="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                <div class="flex items-center justify-between mb-3">
                    <h4 class="font-bold text-gray-900 dark:text-white">
                        ${dayName}, ${day} de ${monthNames[currentMonth - 1]}
                    </h4>
                    <span class="px-3 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded-full text-xs font-semibold">
                        ${dayEvents.length} ${dayEvents.length === 1 ? 'evento' : 'eventos'}
                    </span>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    ${dayEvents.map(event => `
                        <div class="flex items-center justify-between gap-3 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">
                            <div class="flex-1">
                                <p class="font-semibold text-gray-900 dark:text-white">${event.name}</p>
                                <p class="text-sm text-gray-600 dark:text-gray-400">${event.ticker}</p>
                            </div>
                            ${event.is_past && event.earnings_link ? `
                                <a href="${event.earnings_link}" target="_blank" 
                                   class="px-3 py-1 bg-green-500 hover:bg-green-600 text-white rounded-lg text-xs font-semibold transition-colors"
                                   title="Ver balance">
                                    Ver Balance
                                </a>
                            ` : ''}
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }).join('');
}

// Show day events modal
function showDayEvents(dateKey, events) {
    const date = new Date(dateKey);
    const dayName = dayNames[date.getDay()];
    const day = date.getDate();
    
    // Create modal
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm';
    modal.innerHTML = `
        <div class="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
            <div class="flex justify-between items-center p-6 border-b border-gray-200 dark:border-gray-700">
                <h3 class="text-2xl font-bold text-gray-900 dark:text-white">
                    ${dayName}, ${day} de ${monthNames[currentMonth - 1]} de ${currentYear}
                </h3>
                <button class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500 dark:text-gray-400" onclick="this.closest('.fixed').remove()">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                </button>
            </div>
            <div class="p-6">
                <div class="space-y-3">
                    ${events.map(event => `
                        <div class="p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                            <div class="flex items-center justify-between">
                                <div class="flex-1">
                                    <p class="font-bold text-lg text-gray-900 dark:text-white">${event.name}</p>
                                    <p class="text-sm text-gray-600 dark:text-gray-400">${event.ticker}</p>
                                </div>
                                <div class="flex items-center gap-2">
                                    ${event.is_past && event.earnings_link ? `
                                        <a href="${event.earnings_link}" target="_blank" 
                                           class="px-3 py-1 bg-green-500 hover:bg-green-600 text-white rounded-lg text-xs font-semibold transition-colors whitespace-nowrap"
                                           title="Ver balance">
                                            Ver Balance
                                        </a>
                                    ` : ''}
                                    <span class="px-3 py-1 bg-green-500 text-white rounded-full text-xs font-semibold">
                                        Resultados
                                    </span>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Close on backdrop click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.remove();
        }
    });
}

// Navigation handlers
document.getElementById('prevMonth').addEventListener('click', () => {
    currentMonth--;
    if (currentMonth < 1) {
        currentMonth = 12;
        currentYear--;
    }
    loadCalendar();
});

document.getElementById('nextMonth').addEventListener('click', () => {
    currentMonth++;
    if (currentMonth > 12) {
        currentMonth = 1;
        currentYear++;
    }
    loadCalendar();
});

// Handle window resize to re-render calendar on mobile/desktop switch
let resizeTimeout;
window.addEventListener('resize', () => {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(() => {
        // Re-render calendar if switching between mobile/desktop
        loadCalendar();
    }, 250);
});

// Load analyst insights for events in the current month
async function loadAnalystInsights(calendarData) {
    console.log('=== loadAnalystInsights START ===');
    console.log('loadAnalystInsights called with data:', calendarData);
    try {
        const tbody = document.getElementById('analystInsightsBody');
        if (!tbody) {
            console.error('analystInsightsBody element not found');
            return;
        }
        
        const events = calendarData.events || {};
        const allTickers = new Set();
        
        // Collect all unique tickers from events
        Object.values(events).forEach(dayEvents => {
            dayEvents.forEach(event => {
                allTickers.add(event.ticker);
            });
        });
        
        console.log('Found tickers:', Array.from(allTickers));
        
        if (allTickers.size === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="text-center py-8 text-gray-500 dark:text-gray-400">
                        No hay eventos este mes
                    </td>
                </tr>
            `;
            return;
        }

        // Filter tickers that need fetching (not in cache)
        const tickersToFetch = Array.from(allTickers).filter(ticker => !calendarCache.insights[ticker]);
        console.log(`Tickers to fetch: ${tickersToFetch.length} (Cached: ${allTickers.size - tickersToFetch.length})`);

        if (tickersToFetch.length > 0) {
            console.log('Fetching insights for', tickersToFetch.length, 'tickers');
            
            // Fetch analyst insights for missing tickers
            const insightsPromises = tickersToFetch.map(async (ticker) => {
                try {
                    const url = `${API_BASE_URL}/asset/${ticker}/analyst-insights`;
                    console.log(`Fetching insights for ${ticker} from ${url}`);
                    const response = await fetch(url);
                    if (response.ok) {
                        const data = await response.json();
                        return { ticker, data };
                    } else {
                        return { ticker, data: null };
                    }
                } catch (error) {
                    console.error(`Error fetching insights for ${ticker}:`, error);
                    return { ticker, data: null };
                }
            });
            
            const insightsResults = await Promise.all(insightsPromises);
            
            // Update cache with new results
            insightsResults.forEach(({ ticker, data }) => {
                if (data) {
                    calendarCache.insights[ticker] = data;
                }
            });
            
            // Persist updated cache
            persistCache();
        }
        
        // Build insights map from cache for rendering
        const insightsMap = new Map();
        Array.from(allTickers).forEach(ticker => {
            if (calendarCache.insights[ticker]) {
                insightsMap.set(ticker, calendarCache.insights[ticker]);
            }
        });
        
        renderAnalystInsights(insightsMap, events);
    } catch (error) {
        console.error('Error loading analyst insights:', error);
        // ... (error handling remains same)
        const tbody = document.getElementById('analystInsightsBody');
        if (tbody) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="text-center py-8 text-red-500">
                        Error al cargar análisis de analistas: ${error.message}
                    </td>
                </tr>
            `;
        }
    }
}

// Render analyst insights table
function renderAnalystInsights(insightsMap, events) {
    console.log('renderAnalystInsights called', insightsMap.size, 'insights');
    const tbody = document.getElementById('analystInsightsBody');
    
    if (!tbody) {
        console.error('analystInsightsBody element not found in renderAnalystInsights');
        return;
    }
    
    if (insightsMap.size === 0) {
        console.log('No insights data, showing empty message');
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center py-8 text-gray-500 dark:text-gray-400">
                    No hay datos de analistas disponibles
                </td>
            </tr>
        `;
        return;
    }
    
    // Get all events and group by ticker
    const tickerEvents = new Map();
    Object.values(events).forEach(dayEvents => {
        dayEvents.forEach(event => {
            if (!tickerEvents.has(event.ticker)) {
                tickerEvents.set(event.ticker, event);
            }
        });
    });
    
    // Filter based on tab
    let filteredTickers = Array.from(tickerEvents.keys());
    
    if (currentTab !== 'all') {
        filteredTickers = filteredTickers.filter(ticker => {
            const insight = insightsMap.get(ticker);
            if (!insight) return false;
            
            const sentiment = insight.sentiment?.value || '';
            const score = insight.sentiment?.score || 3;
            
            if (currentTab === 'good') {
                return sentiment === 'Strong Buy' || sentiment === 'Buy' || score <= 2.5;
            } else if (currentTab === 'neutral') {
                return sentiment === 'Hold' || sentiment === 'Neutral' || (score > 2.5 && score <= 3.5);
            } else if (currentTab === 'bad') {
                return sentiment === 'Sell' || sentiment === 'Strong Sell' || score > 3.5;
            }
            return true;
        });
    }
    
    if (filteredTickers.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center py-8 text-gray-500 dark:text-gray-400">
                    No hay activos en esta categoría
                </td>
            </tr>
        `;
        return;
    }
    
    const rows = filteredTickers.map(ticker => {
        const event = tickerEvents.get(ticker);
        const insight = insightsMap.get(ticker);
        
        if (!insight) {
            return `
                <tr class="border-b border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50">
                    <td class="py-4 px-4">
                        <div class="font-semibold text-gray-900 dark:text-white">${event.name}</div>
                        <div class="text-sm text-gray-600 dark:text-gray-400">${ticker}</div>
                    </td>
                    <td colspan="7" class="py-4 px-4 text-gray-500 dark:text-gray-400 text-sm">
                        Datos no disponibles
                    </td>
                </tr>
            `;
        }
        
        // Format recommendations
        const recs = insight.recommendations;
        const totalRecs = insight.total_recommendations || 0;
        const recommendationsText = totalRecs > 0 
            ? `${recs.strongBuy || 0} Strong Buy, ${recs.buy || 0} Buy, ${recs.hold || 0} Hold`
            : 'Sin datos';
        
        // Format sentiment with color
        const sentiment = insight.sentiment || { value: 'Sin datos', color: 'gray' };
        const sentimentColors = {
            'green': 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400',
            'lightgreen': 'bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-300',
            'yellow': 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400',
            'orange': 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400',
            'red': 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400',
            'gray': 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
        };
        const sentimentClass = sentimentColors[sentiment.color] || sentimentColors.gray;
        
        // Format earnings
        const formatEarnings = (value) => {
            if (value === null || value === undefined) return 'N/A';
            if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
            if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
            if (value >= 1e3) return `$${(value / 1e3).toFixed(2)}K`;
            return `$${value.toFixed(2)}`;
        };
        
        const lastQExpected = insight.earnings?.last_quarter?.expected;
        const lastQActual = insight.earnings?.last_quarter?.actual;
        const lastAnnualExpected = insight.earnings?.last_annual?.expected;
        const lastAnnualActual = insight.earnings?.last_annual?.actual;
        
        return `
            <tr class="border-b border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50">
                <td class="py-4 px-4">
                    <div class="font-semibold text-gray-900 dark:text-white">${insight.name || event.name}</div>
                    <div class="text-sm text-gray-600 dark:text-gray-400">${ticker}</div>
                    <button onclick='openAnalysisModal("${ticker}", ${JSON.stringify(insight).replace(/'/g, "\\'")})' class="mt-2 px-3 py-1 bg-green-500 hover:bg-green-600 text-white text-xs rounded-lg transition-colors">
                        Ver Análisis
                    </button>
                </td>
                <td class="py-4 px-4 text-sm text-gray-700 dark:text-gray-300 max-w-xs truncate">
                    ${insight.market_expectation || 'Sin datos disponibles'}
                </td>
                <td class="py-4 px-4 text-sm text-gray-700 dark:text-gray-300">
                    ${recommendationsText}
                </td>
                <td class="py-4 px-4">
                    <span class="px-3 py-1 rounded-full text-xs font-semibold ${sentimentClass}">
                        ${sentiment.value}
                    </span>
                </td>
                <td class="py-4 px-4 text-sm text-gray-700 dark:text-gray-300">
                    ${lastQExpected ? formatEarnings(lastQExpected) : 'N/A'}
                </td>
                <td class="py-4 px-4 text-sm text-gray-700 dark:text-gray-300">
                    ${lastQActual ? formatEarnings(lastQActual) : 'N/A'}
                </td>
                <td class="py-4 px-4 text-sm text-gray-700 dark:text-gray-300">
                    ${lastAnnualExpected ? formatEarnings(lastAnnualExpected) : 'N/A'}
                </td>
                <td class="py-4 px-4 text-sm text-gray-700 dark:text-gray-300">
                    ${lastAnnualActual ? formatEarnings(lastAnnualActual) : 'N/A'}
                </td>
            </tr>
        `;
    }).join('');
    
    tbody.innerHTML = rows;
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadCalendar();
    setupTabs();
});

function setupTabs() {
    const tabs = document.querySelectorAll('.insight-tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Update UI
            tabs.forEach(t => {
                t.classList.remove('text-green-600', 'border-b-2', 'border-green-500');
                t.classList.add('text-gray-500', 'hover:text-gray-700', 'dark:text-gray-400', 'dark:hover:text-gray-300');
            });
            tab.classList.add('text-green-600', 'border-b-2', 'border-green-500');
            tab.classList.remove('text-gray-500', 'hover:text-gray-700', 'dark:text-gray-400', 'dark:hover:text-gray-300');
            
            // Update Filter
            currentTab = tab.getAttribute('data-tab');
            
            // Re-render
            const events = calendarCache.data.events || {};
            const insightsMap = new Map();
            Object.keys(calendarCache.insights).forEach(ticker => {
                insightsMap.set(ticker, calendarCache.insights[ticker]);
            });
            
            renderAnalystInsights(insightsMap, events);
        });
    });
}

// Open analysis modal with charts
function openAnalysisModal(ticker, insight) {
    const modal = document.getElementById('analysisModal');
    const modalTitle = document.getElementById('modalTitle');
    
    modalTitle.textContent = `Análisis: ${insight.name || ticker}`;
    modal.classList.remove('hidden');
    modal.classList.add('flex');
    document.body.style.overflow = 'hidden';
    
    // Render charts
    renderEPSTrendChart(insight.earnings?.trend || []);
    renderRevenueEarningsChart(insight.earnings?.financials_chart || []);
    renderRecommendationsBar(insight.recommendations || {});
}

// Close analysis modal
function closeAnalysisModal() {
    const modal = document.getElementById('analysisModal');
    modal.classList.add('hidden');
    modal.classList.remove('flex');
    document.body.style.overflow = '';
    
    // Destroy charts to prevent memory leaks
    if (window.epsTrendChart) {
        window.epsTrendChart.destroy();
        window.epsTrendChart = null;
    }
    if (window.revenueEarningsChart) {
        window.revenueEarningsChart.destroy();
        window.revenueEarningsChart = null;
    }
}

// Make functions global
window.openAnalysisModal = openAnalysisModal;
window.closeAnalysisModal = closeAnalysisModal;

// Render EPS Trend Chart
function renderEPSTrendChart(trendData) {
    const ctx = document.getElementById('epsTrendChart');
    if (!ctx) return;
    
    // Destroy existing chart
    if (window.epsTrendChart) {
        window.epsTrendChart.destroy();
    }
    
    const isDark = document.documentElement.classList.contains('dark');
    const textColor = isDark ? '#D1D4DC' : '#191919';
    const gridColor = isDark ? '#2B2B43' : '#E0E3EB';
    
    window.epsTrendChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: trendData.map(d => d.period),
            datasets: [
                {
                    label: 'Estimate',
                    data: trendData.map(d => d.estimate),
                    backgroundColor: 'rgba(41, 98, 255, 0.6)',
                    borderColor: 'rgba(41, 98, 255, 1)',
                    borderWidth: 1
                },
                {
                    label: 'Actual',
                    data: trendData.map(d => d.actual),
                    backgroundColor: 'rgba(38, 166, 154, 0.6)',
                    borderColor: 'rgba(38, 166, 154, 1)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: textColor }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': $' + context.parsed.y.toFixed(2);
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { color: textColor },
                    grid: { color: gridColor }
                },
                x: {
                    ticks: { color: textColor },
                    grid: { color: gridColor }
                }
            }
        }
    });
}

// Render Revenue vs Earnings Chart
function renderRevenueEarningsChart(financialsData) {
    const ctx = document.getElementById('revenueEarningsChart');
    if (!ctx) return;
    
    // Destroy existing chart
    if (window.revenueEarningsChart) {
        window.revenueEarningsChart.destroy();
    }
    
    const isDark = document.documentElement.classList.contains('dark');
    const textColor = isDark ? '#D1D4DC' : '#191919';
    const gridColor = isDark ? '#2B2B43' : '#E0E3EB';
    
    window.revenueEarningsChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: financialsData.map(d => d.period),
            datasets: [
                {
                    label: 'Revenue',
                    data: financialsData.map(d => d.revenue / 1e9), // Convert to billions
                    backgroundColor: 'rgba(66, 165, 245, 0.6)',
                    borderColor: 'rgba(66, 165, 245, 1)',
                    borderWidth: 1
                },
                {
                    label: 'Earnings',
                    data: financialsData.map(d => d.earnings / 1e9), // Convert to billions
                    backgroundColor: 'rgba(255, 167, 38, 0.6)',
                    borderColor: 'rgba(255, 167, 38, 1)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: textColor }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': $' + context.parsed.y.toFixed(2) + 'B';
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { 
                        color: textColor,
                        callback: function(value) {
                            return '$' + value.toFixed(1) + 'B';
                        }
                    },
                    grid: { color: gridColor }
                },
                x: {
                    ticks: { color: textColor },
                    grid: { color: gridColor }
                }
            }
        }
    });
}

// Render Recommendations Bar
function renderRecommendationsBar(recommendations) {
    const container = document.getElementById('recommendationsBarContainer');
    const legend = document.getElementById('recommendationsLegend');
    if (!container || !legend) return;
    
    const total = recommendations.strongBuy + recommendations.buy + recommendations.hold + 
                  recommendations.underperform + recommendations.sell;
    
    if (total === 0) {
        container.innerHTML = '<p class="text-gray-500 dark:text-gray-400 text-sm">No hay recomendaciones disponibles</p>';
        legend.innerHTML = '';
        return;
    }
    
    const strongBuyPct = (recommendations.strongBuy / total) * 100;
    const buyPct = (recommendations.buy / total) * 100;
    const holdPct = (recommendations.hold / total) * 100;
    const underperformPct = (recommendations.underperform / total) * 100;
    const sellPct = (recommendations.sell / total) * 100;
    
    container.innerHTML = `
        <div class="w-full h-8 flex rounded-lg overflow-hidden border border-gray-300 dark:border-gray-600">
            ${strongBuyPct > 0 ? `<div class="bg-green-600" style="width: ${strongBuyPct}%" title="Strong Buy: ${recommendations.strongBuy}"></div>` : ''}
            ${buyPct > 0 ? `<div class="bg-green-400" style="width: ${buyPct}%" title="Buy: ${recommendations.buy}"></div>` : ''}
            ${holdPct > 0 ? `<div class="bg-yellow-400" style="width: ${holdPct}%" title="Hold: ${recommendations.hold}"></div>` : ''}
            ${underperformPct > 0 ? `<div class="bg-orange-400" style="width: ${underperformPct}%" title="Underperform: ${recommendations.underperform}"></div>` : ''}
            ${sellPct > 0 ? `<div class="bg-red-500" style="width: ${sellPct}%" title="Sell: ${recommendations.sell}"></div>` : ''}
        </div>
    `;
    
    legend.innerHTML = `
        <span><span class="inline-block w-3 h-3 bg-green-600 rounded mr-1"></span>Strong Buy: ${recommendations.strongBuy}</span>
        <span><span class="inline-block w-3 h-3 bg-green-400 rounded mr-1"></span>Buy: ${recommendations.buy}</span>
        <span><span class="inline-block w-3 h-3 bg-yellow-400 rounded mr-1"></span>Hold: ${recommendations.hold}</span>
        <span><span class="inline-block w-3 h-3 bg-orange-400 rounded mr-1"></span>Underperform: ${recommendations.underperform}</span>
        <span><span class="inline-block w-3 h-3 bg-red-500 rounded mr-1"></span>Sell: ${recommendations.sell}</span>
    `;
}

