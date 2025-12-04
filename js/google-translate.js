// Google Translate Integration
// Auto-translate content on page load

(function() {
    'use strict';
    
    // Initialize Google Translate
    function initGoogleTranslate() {
        // Check if Google Translate is already loaded
        if (window.google && window.google.translate) {
            return;
        }
        
        // Add Google Translate script
        const script = document.createElement('script');
        script.type = 'text/javascript';
        script.src = 'https://translate.google.com/translate_a/element.js?cb=googleTranslateElementInit';
        script.async = true;
        document.head.appendChild(script);
        
        // Initialize translate element
        window.googleTranslateElementInit = function() {
            if (window.google && window.google.translate) {
                new google.translate.TranslateElement({
                    pageLanguage: 'en',
                    includedLanguages: 'es,en',
                    layout: google.translate.TranslateElement.InlineLayout.SIMPLE,
                    autoDisplay: false
                }, 'google_translate_element');
            }
        };
    }
    
    // Auto-translate function for specific elements
    function autoTranslateElements() {
        // Only translate if page language is English or if explicitly requested
        const pageLang = document.documentElement.lang || 'es';
        
        // For news.html, translate news titles and descriptions
        if (window.location.pathname.includes('news.html') || document.querySelector('.news-item')) {
            translateNewsContent();
        }
    }
    
    // Translate news content using Google Translate API (free tier)
    async function translateNewsContent() {
        const newsItems = document.querySelectorAll('.news-item, .news-title, [data-translate]');
        
        if (newsItems.length === 0) return;
        
        // Use Google Translate API (requires API key) or use the free widget
        // For now, we'll use a simpler approach with the translate widget
        
        // Add translate button to news page
        if (!document.getElementById('translate-news-btn')) {
            const translateBtn = document.createElement('button');
            translateBtn.id = 'translate-news-btn';
            translateBtn.className = 'fixed bottom-4 right-4 bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg shadow-lg z-50 flex items-center gap-2 transition-colors';
            translateBtn.innerHTML = `
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
                </svg>
                <span>Traducir Noticias</span>
            `;
            translateBtn.onclick = () => {
                // Show Google Translate widget
                const widget = document.getElementById('google_translate_element');
                if (widget) {
                    widget.style.display = widget.style.display === 'none' ? 'block' : 'none';
                } else {
                    // Create widget if it doesn't exist
                    const div = document.createElement('div');
                    div.id = 'google_translate_element';
                    div.style.position = 'fixed';
                    div.style.top = '20px';
                    div.style.right = '20px';
                    div.style.zIndex = '9999';
                    div.style.backgroundColor = 'white';
                    div.style.padding = '10px';
                    div.style.borderRadius = '8px';
                    div.style.boxShadow = '0 4px 6px rgba(0,0,0,0.1)';
                    document.body.appendChild(div);
                    initGoogleTranslate();
                }
            };
            document.body.appendChild(translateBtn);
        }
    }
    
    // Simple translation function using fetch (requires CORS proxy or backend)
    async function translateText(text, targetLang = 'es') {
        try {
            // Use a free translation service or backend endpoint
            // For now, we'll use a simple approach
            const API_BASE_URL = window.API_BASE_URL || 'http://localhost:8080';
            const response = await fetch(`${API_BASE_URL}/api/translate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    text: text,
                    target_lang: targetLang
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                return data.translated_text || text;
            }
        } catch (error) {
            console.warn('Translation API not available, using Google Translate widget');
        }
        
        return text;
    }
    
    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            initGoogleTranslate();
            autoTranslateElements();
        });
    } else {
        initGoogleTranslate();
        autoTranslateElements();
    }
    
    // Export functions for manual use
    window.translateText = translateText;
    window.autoTranslateElements = autoTranslateElements;
})();

