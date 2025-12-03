// Blog Carousel Functionality
document.addEventListener('DOMContentLoaded', () => {
    // Initialize all carousels
    initCarousel('guides');
    initCarousel('releases');
    initCarousel('news');
});

function initCarousel(type) {
    const container = document.querySelector(`.carousel-container-${type}`);
    const track = document.querySelector(`.carousel-track-${type}`);
    const prevBtn = document.querySelector(`.carousel-btn-prev-${type}`);
    const nextBtn = document.querySelector(`.carousel-btn-next-${type}`);
    const cards = track.querySelectorAll('.carousel-card');

    if (!container || !track || !prevBtn || !nextBtn || cards.length === 0) {
        return;
    }

    let currentIndex = 0;
    const cardsPerView = getCardsPerView();
    const totalCards = cards.length;
    const maxIndex = Math.max(0, totalCards - cardsPerView);

    // Update carousel position
    function updateCarousel() {
        if (cards.length === 0) return;
        
        const cardWidth = cards[0].offsetWidth;
        const gap = 24; // gap-6 = 1.5rem = 24px
        const translateX = -(currentIndex * (cardWidth + gap));
        track.style.transform = `translateX(${translateX}px)`;

        // Update button states
        prevBtn.disabled = currentIndex === 0;
        nextBtn.disabled = currentIndex >= maxIndex;

        // Update button opacity
        if (prevBtn.disabled) {
            prevBtn.classList.add('opacity-50', 'cursor-not-allowed');
        } else {
            prevBtn.classList.remove('opacity-50', 'cursor-not-allowed');
        }

        if (nextBtn.disabled) {
            nextBtn.classList.add('opacity-50', 'cursor-not-allowed');
        } else {
            nextBtn.classList.remove('opacity-50', 'cursor-not-allowed');
        }
    }

    // Get number of cards per view based on screen size
    function getCardsPerView() {
        const width = window.innerWidth;
        if (width >= 1024) { // lg
            return 3;
        } else if (width >= 768) { // md
            return 2;
        } else {
            return 1;
        }
    }

    // Handle window resize
    let resizeTimeout;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
            const newCardsPerView = getCardsPerView();
            const newMaxIndex = Math.max(0, totalCards - newCardsPerView);
            if (currentIndex > newMaxIndex) {
                currentIndex = newMaxIndex;
            }
            updateCarousel();
        }, 250);
    });

    // Previous button
    prevBtn.addEventListener('click', () => {
        if (currentIndex > 0) {
            currentIndex--;
            updateCarousel();
        }
    });

    // Next button
    nextBtn.addEventListener('click', () => {
        const cardsPerView = getCardsPerView();
        const maxIndex = Math.max(0, totalCards - cardsPerView);
        if (currentIndex < maxIndex) {
            currentIndex++;
            updateCarousel();
        }
    });

    // Initialize after a short delay to ensure cards are rendered
    setTimeout(() => {
        updateCarousel();
    }, 100);
    
    // Also update on first load
    if (document.readyState === 'complete') {
        updateCarousel();
    } else {
        window.addEventListener('load', updateCarousel);
    }

    // Touch/swipe support for mobile
    let touchStartX = 0;
    let touchEndX = 0;

    track.addEventListener('touchstart', (e) => {
        touchStartX = e.changedTouches[0].screenX;
    }, { passive: true });

    track.addEventListener('touchend', (e) => {
        touchEndX = e.changedTouches[0].screenX;
        handleSwipe();
    }, { passive: true });

    function handleSwipe() {
        const swipeThreshold = 50;
        const diff = touchStartX - touchEndX;

        if (Math.abs(diff) > swipeThreshold) {
            if (diff > 0) {
                // Swipe left - next
                const cardsPerView = getCardsPerView();
                const maxIndex = Math.max(0, totalCards - cardsPerView);
                if (currentIndex < maxIndex) {
                    currentIndex++;
                    updateCarousel();
                }
            } else {
                // Swipe right - previous
                if (currentIndex > 0) {
                    currentIndex--;
                    updateCarousel();
                }
            }
        }
    }
}

