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
            pills.forEach(p => p.classList.remove('active'));
            pill.classList.add('active');

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

    loadingEl.style.display = 'flex';
    gridEl.style.display = 'none';

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
            <p style="color: #dc3545;">❌ Error al cargar las noticias. Por favor, verifica que el servidor esté ejecutándose.</p>
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
        gridEl.innerHTML = '<p class="no-news">No se encontraron noticias para esta selección.</p>';
        gridEl.style.display = 'block'; // Show message
        loadingEl.style.display = 'none';
        return;
    }

    newsItems.forEach(item => {
        const card = createNewsCard(item);
        gridEl.appendChild(card);
    });

    loadingEl.style.display = 'none';
    gridEl.style.display = 'grid';
}

function createNewsCard(item) {
    const card = document.createElement('div');
    card.className = 'news-card';

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
        imageHtml = `<div class="news-image" style="background-image: url('${item.image}')"></div>`;
    } else {
        // Fallback gradient or placeholder
        imageHtml = `<div class="news-image placeholder"></div>`;
    }

    card.innerHTML = `
        ${imageHtml}
        <div class="news-card-content">
            <div class="news-source">${item.source || 'Yahoo Finance'}</div>
            <h3 class="news-title">
                <a href="${item.link}" target="_blank" rel="noopener noreferrer">${item.title}</a>
            </h3>
            <p class="news-summary">${item.summary}</p>
            <div class="news-meta">
                <span class="news-date">
                    📅 ${publishedDate}
                </span>
            </div>
        </div>
    `;

    return card;
}
