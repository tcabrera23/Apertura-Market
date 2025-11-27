// News Page JavaScript

const API_BASE_URL = 'http://localhost:8080/api';

document.addEventListener('DOMContentLoaded', () => {
    loadNews();
});

async function loadNews() {
    const loadingEl = document.getElementById('newsLoading');
    const gridEl = document.getElementById('newsGrid');

    loadingEl.style.display = 'flex';
    gridEl.style.display = 'none';

    try {
        const response = await fetch(`${API_BASE_URL}/news`);

        if (!response.ok) {
            throw new Error('Error al cargar noticias');
        }

        const news = await response.json();

        gridEl.innerHTML = '';

        news.forEach(item => {
            const card = createNewsCard(item);
            gridEl.appendChild(card);
        });

        loadingEl.style.display = 'none';
        gridEl.style.display = 'grid';

    } catch (error) {
        console.error('Error loading news:', error);
        loadingEl.innerHTML = `
            <p style="color: #dc3545;">❌ Error al cargar las noticias. Por favor, verifica que el servidor esté ejecutándose.</p>
        `;
    }
}

function createNewsCard(item) {
    const card = document.createElement('div');
    card.className = 'news-card';

    const publishedDate = item.published ? new Date(item.published).toLocaleDateString('es-ES', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    }) : 'Fecha no disponible';

    card.innerHTML = `
        <div class="news-card-content">
            <h3 class="news-title">
                <a href="${item.link}" target="_blank" rel="noopener noreferrer">${item.title}</a>
            </h3>
            <p class="news-summary">${item.summary}</p>
            <div class="news-meta">
                <span class="news-date">
                    📅 ${publishedDate}
                </span>
                <a href="${item.link}" target="_blank" rel="noopener noreferrer" class="news-link">
                    Leer más →
                </a>
            </div>
        </div>
    `;

    return card;
}
