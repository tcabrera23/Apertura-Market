// Calendar Page JavaScript

const API_BASE_URL = 'http://localhost:8080/api';

// Current date tracking
let currentDate = new Date();
let currentYear = currentDate.getFullYear();
let currentMonth = currentDate.getMonth() + 1; // 1-12

// Month names in Spanish
const monthNames = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
];

const dayNames = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];

// Load calendar data
async function loadCalendar() {
    try {
        const response = await fetch(`${API_BASE_URL}/earnings-calendar?year=${currentYear}&month=${currentMonth}`);
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            const errorMessage = errorData.detail || 'Error al cargar el calendario';
            throw new Error(errorMessage);
        }
        
        const data = await response.json();
        renderCalendar(data);
        renderEventsList(data);
    } catch (error) {
        console.error('Error loading calendar:', error);
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
    
    // Add day cells
    for (let day = 1; day <= daysInMonth; day++) {
        const dayCell = document.createElement('div');
        dayCell.className = 'aspect-square border border-gray-200 dark:border-gray-700 rounded-lg p-2 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors cursor-pointer';
        
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

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadCalendar();
});

