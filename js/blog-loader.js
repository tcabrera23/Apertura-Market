// Blog Posts Loader
// Carga dinámicamente los posts desde posts.json y los muestra en blog.html

const BLOG_POSTS_URL = 'blog/posts.json';

let allPosts = {
    guias: [],
    releases: [],
    noticias: []
};

// Load blog posts from JSON
async function loadBlogPosts() {
    try {
        const response = await fetch(BLOG_POSTS_URL);
        if (!response.ok) {
            throw new Error('Error al cargar posts');
        }
        allPosts = await response.json();
        return allPosts;
    } catch (error) {
        console.error('Error loading blog posts:', error);
        return null;
    }
}

// Render posts in carousel
function renderPostsInCarousel(category, posts) {
    const track = document.querySelector(`.carousel-track-${category}`);
    if (!track) return;

    // Clear existing cards (except template)
    const existingCards = track.querySelectorAll('.carousel-card');
    existingCards.forEach(card => {
        if (!card.hasAttribute('data-template')) {
            card.remove();
        }
    });

    // Create cards for each post
    posts.forEach(post => {
        const card = createPostCard(post, category);
        track.appendChild(card);
    });

    // Reinitialize carousel after adding new cards
    if (typeof initCarousel === 'function') {
        setTimeout(() => {
            initCarousel(category);
        }, 100);
    }
}

// Create post card element
function createPostCard(post, category) {
    const card = document.createElement('div');
    card.className = 'carousel-card flex-shrink-0 w-full md:w-[calc(50%-12px)] lg:w-[calc(33.333%-16px)]';

    // Determine badge color based on category
    let badgeClass = 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400';
    let badgeText = post.category || 'Artículo';
    
    if (category === 'releases') {
        if (post.category === 'Release') {
            badgeClass = 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400';
        } else if (post.category === 'Novedad') {
            badgeClass = 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400';
        } else if (post.category === 'Mejora') {
            badgeClass = 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400';
        } else if (post.category === 'Próximamente') {
            badgeClass = 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400';
        }
    } else if (category === 'news') {
        if (post.category === 'Video') {
            badgeClass = 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400';
        } else if (post.category === 'Artículo') {
            badgeClass = 'bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-400';
        } else if (post.category === 'Noticia') {
            badgeClass = 'bg-teal-100 dark:bg-teal-900/30 text-teal-700 dark:text-teal-400';
        }
    }

    // Build file path
    const filePath = `blog/${post.file}`;
    
    // Check if it's a video (external link)
    const linkHref = post.video_url || filePath;
    const linkTarget = post.video_url ? '_blank' : '_self';
    const linkRel = post.video_url ? 'noopener noreferrer' : '';

    card.innerHTML = `
        <div class="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 overflow-hidden hover:shadow-xl transition-shadow h-full">
            <div class="h-48 bg-cover bg-center" style="background-image: url('${post.image_url}');">
                <div class="h-full w-full bg-gradient-to-t from-black/60 to-transparent"></div>
            </div>
            <div class="p-6">
                <div class="flex items-center gap-2 mb-2">
                    <span class="px-3 py-1 ${badgeClass} text-xs font-semibold rounded-full">${badgeText}</span>
                    ${post.version ? `<span class="text-xs text-gray-500 dark:text-gray-400">${post.version}</span>` : ''}
                </div>
                <h3 class="text-xl font-bold text-gray-900 dark:text-white mb-2">
                    ${post.title}
                </h3>
                <p class="text-gray-600 dark:text-gray-300 mb-4">
                    ${post.description}
                </p>
                <a href="${linkHref}" ${linkTarget ? `target="${linkTarget}"` : ''} ${linkRel ? `rel="${linkRel}"` : ''} class="text-green-600 dark:text-green-400 font-semibold hover:underline">
                    ${post.video_url ? 'Ver video →' : 'Leer más →'}
                </a>
            </div>
        </div>
    `;

    return card;
}

// Initialize blog loader
async function initBlogLoader() {
    const posts = await loadBlogPosts();
    if (!posts) {
        console.warn('No se pudieron cargar los posts, usando contenido estático');
        return;
    }

    // Render each category
    if (posts.guias && posts.guias.length > 0) {
        renderPostsInCarousel('guides', posts.guias);
    }
    
    if (posts.releases && posts.releases.length > 0) {
        renderPostsInCarousel('releases', posts.releases);
    }
    
    if (posts.noticias && posts.noticias.length > 0) {
        renderPostsInCarousel('news', posts.noticias);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Wait a bit for blog-carousel.js to initialize first
    setTimeout(() => {
        initBlogLoader();
    }, 200);
});

