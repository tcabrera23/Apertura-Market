// News Page JavaScript

const API_BASE_URL = 'http://localhost:8080/api';
let currentNews = [];

document.addEventListener('DOMContentLoaded', () => {
    // Load initial news
    loadNews('general');

    // Category pills
    const pills = document.querySelectorAll('.category-pill');
    pills.forEach(pill => {
        pill.addEventListener('click', () => {
        // Update active state
        pills.forEach(p => {
            p.classList.remove('bg-gradient-to-r', 'from-green-500', 'to-green-600', 'text-white', 'shadow-lg');
            p.classList.add('bg-white', 'dark:bg-gray-800', 'border', 'border-gray-300', 'dark:border-gray-600', 'text-gray-700', 'dark:text-gray-300');
        });
        pill.classList.remove('bg-white', 'dark:bg-gray-800', 'border', 'border-gray-300', 'dark:border-gray-600', 'text-gray-700', 'dark:text-gray-300');
        pill.classList.add('bg-gradient-to-r', 'from-green-500', 'to-green-600', 'text-white', 'shadow-lg');

            // Load news for category
            const category = pill.getAttribute('data-category');
            loadNews(category);
        });
    });

    // Date filter
    const dateInput = document.getElementById('dateFilter');
    dateInput.addEventListener('change', () => {
        filterNewsByDate(dateInput.value);
    });
});

async function loadNews(category) {
    const loadingEl = document.getElementById('newsLoading');
    const gridEl = document.getElementById('newsGrid');

    loadingEl.classList.remove('hidden');
    loadingEl.classList.add('flex');
    gridEl.classList.add('hidden');
    gridEl.classList.remove('grid');

    try {
        const response = await fetch(`${API_BASE_URL}/news?category=${category}`);

        if (!response.ok) {
            throw new Error('Error al cargar noticias');
        }

        currentNews = await response.json();

        // Apply date filter if exists
        const dateInput = document.getElementById('dateFilter');
        if (dateInput.value) {
            filterNewsByDate(dateInput.value);
        } else {
            renderNews(currentNews);
        }

    } catch (error) {
        console.error('Error loading news:', error);
        loadingEl.innerHTML = `
            <p class="text-red-500">❌ Error al cargar las noticias. Por favor, verifica que el servidor esté ejecutándose.</p>
        `;
    }
}

function filterNewsByDate(dateStr) {
    if (!dateStr) {
        renderNews(currentNews);
        return;
    }

    const selectedDate = new Date(dateStr);
    const filtered = currentNews.filter(item => {
        if (!item.published) return false;
        const itemDate = new Date(item.published);
        return itemDate.toDateString() === selectedDate.toDateString();
    });

    renderNews(filtered);
}

function renderNews(newsItems) {
    const loadingEl = document.getElementById('newsLoading');
    const gridEl = document.getElementById('newsGrid');

    gridEl.innerHTML = '';

    if (newsItems.length === 0) {
        gridEl.innerHTML = '<p class="text-center py-16 text-gray-500 dark:text-gray-400 col-span-full">No se encontraron noticias para esta selección.</p>';
        gridEl.classList.remove('hidden');
        gridEl.classList.add('grid');
        loadingEl.classList.add('hidden');
        loadingEl.classList.remove('flex');
        return;
    }

    newsItems.forEach(item => {
        const card = createNewsCard(item);
        gridEl.appendChild(card);
    });

    loadingEl.classList.add('hidden');
    loadingEl.classList.remove('flex');
    gridEl.classList.remove('hidden');
    gridEl.classList.add('grid');
}

function createNewsCard(item) {
    const card = document.createElement('div');
    card.className = 'bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 overflow-hidden hover:shadow-2xl hover:scale-[1.02] transition-all';

    const publishedDate = item.published ? new Date(item.published).toLocaleDateString('es-ES', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    }) : 'Fecha no disponible';

    // Image HTML
    let imageHtml = '';
    if (item.image) {
        imageHtml = `<div class="w-full h-48 bg-cover bg-center" style="background-image: url('${item.image}')"></div>`;
    } else {
        imageHtml = `<div class="w-full h-48 bg-gradient-to-br from-green-400 to-green-600"></div>`;
    }

    card.innerHTML = `
        ${imageHtml}
        <div class="p-6">
            <div class="text-xs font-semibold text-green-600 dark:text-green-400 mb-2">${item.source || 'Yahoo Finance'}</div>
            <h3 class="text-lg font-bold text-gray-900 dark:text-white mb-3 line-clamp-2">
                <a href="${item.link}" target="_blank" rel="noopener noreferrer" class="hover:text-green-500 dark:hover:text-green-400 transition-colors">${item.title}</a>
            </h3>
            <p class="text-gray-600 dark:text-gray-400 text-sm mb-4 line-clamp-3">${item.summary}</p>
            <div class="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-500">
                <span>📅 ${publishedDate}</span>
            </div>
        </div>
    `;

    return card;
}
