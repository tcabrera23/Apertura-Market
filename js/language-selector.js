// Custom Language Selector with Google Translate Integration
// Creates a beautiful dropdown that triggers Google Translate

const LANGUAGES = [
    { code: 'es', name: 'Español', flag: '🇪🇸', googleCode: 'es' },
    { code: 'en', name: 'English', flag: '🇺🇸', googleCode: 'en' },
    { code: 'pt', name: 'Português', flag: '🇧🇷', googleCode: 'pt' }
];

let languageSelectorInitialized = false;

document.addEventListener('DOMContentLoaded', () => {
    initLanguageSelector();
});

function initLanguageSelector() {
    if (languageSelectorInitialized) return;
    languageSelectorInitialized = true;
    
    // Find Google Translate element and hide it
    const googleTranslate = document.getElementById('google_translate_element');
    if (googleTranslate) {
        googleTranslate.style.display = 'none';
    }
    
    // Create and insert language selector
    createLanguageSelector();
    
    // Set initial language from saved preference
    const savedLang = localStorage.getItem('selectedLanguage') || 'es';
    updateSelectedLanguage(savedLang);
}

function createLanguageSelector() {
    // Find where to insert the selector (after dark mode toggle)
    const darkModeToggle = document.getElementById('darkModeToggle');
    if (!darkModeToggle) return;
    
    // Check if selector already exists
    if (document.getElementById('languageSelectorContainer')) return;
    
    const container = document.createElement('div');
    container.id = 'languageSelectorContainer';
    container.className = 'relative';
    container.innerHTML = `
        <button id="languageSelectorBtn" 
            class="flex items-center gap-2 px-3 py-2 rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors font-medium text-sm"
            aria-expanded="false"
            aria-haspopup="true">
            <span id="selectedLangFlag" class="text-base">🇪🇸</span>
            <span id="selectedLangCode" class="uppercase font-semibold">ES</span>
            <svg class="w-4 h-4 transition-transform duration-200" id="langDropdownArrow" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
            </svg>
        </button>
        <div id="languageDropdown" 
            class="hidden absolute right-0 mt-2 w-40 bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 py-1 z-50 overflow-hidden"
            role="menu">
            ${LANGUAGES.map(lang => `
                <button type="button" 
                    class="lang-option w-full flex items-center gap-3 px-4 py-2.5 text-left text-gray-700 dark:text-gray-300 hover:bg-green-50 dark:hover:bg-green-900/20 hover:text-green-600 dark:hover:text-green-400 transition-colors"
                    data-lang="${lang.code}"
                    data-google-code="${lang.googleCode}"
                    role="menuitem">
                    <span class="text-lg">${lang.flag}</span>
                    <span class="font-medium">${lang.name}</span>
                </button>
            `).join('')}
        </div>
    `;
    
    // Insert after dark mode toggle
    darkModeToggle.parentNode.insertBefore(container, darkModeToggle.nextSibling);
    
    // Add event listeners
    const btn = document.getElementById('languageSelectorBtn');
    const dropdown = document.getElementById('languageDropdown');
    const arrow = document.getElementById('langDropdownArrow');
    
    // Toggle dropdown
    btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const isOpen = !dropdown.classList.contains('hidden');
        
        if (isOpen) {
            closeDropdown();
        } else {
            dropdown.classList.remove('hidden');
            arrow.classList.add('rotate-180');
            btn.setAttribute('aria-expanded', 'true');
        }
    });
    
    // Close when clicking outside
    document.addEventListener('click', (e) => {
        if (!container.contains(e.target)) {
            closeDropdown();
        }
    });
    
    // Close on escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeDropdown();
        }
    });
    
    // Handle language selection
    document.querySelectorAll('.lang-option').forEach(option => {
        option.addEventListener('click', () => {
            const langCode = option.dataset.lang;
            const googleCode = option.dataset.googleCode;
            
            selectLanguage(langCode, googleCode);
            closeDropdown();
        });
    });
    
    function closeDropdown() {
        dropdown.classList.add('hidden');
        arrow.classList.remove('rotate-180');
        btn.setAttribute('aria-expanded', 'false');
    }
}

function updateSelectedLanguage(langCode) {
    const lang = LANGUAGES.find(l => l.code === langCode) || LANGUAGES[0];
    
    const flagEl = document.getElementById('selectedLangFlag');
    const codeEl = document.getElementById('selectedLangCode');
    
    if (flagEl) flagEl.textContent = lang.flag;
    if (codeEl) codeEl.textContent = lang.code.toUpperCase();
    
    // Update active state in dropdown
    document.querySelectorAll('.lang-option').forEach(option => {
        if (option.dataset.lang === langCode) {
            option.classList.add('bg-green-50', 'dark:bg-green-900/20', 'text-green-600', 'dark:text-green-400');
        } else {
            option.classList.remove('bg-green-50', 'dark:bg-green-900/20', 'text-green-600', 'dark:text-green-400');
        }
    });
}

function selectLanguage(langCode, googleCode) {
    // Save preference
    localStorage.setItem('selectedLanguage', langCode);
    
    // Update UI
    updateSelectedLanguage(langCode);
    
    // Trigger Google Translate
    triggerGoogleTranslate(googleCode);
}

function triggerGoogleTranslate(langCode) {
    // Method 1: Try using the combo box
    const googleCombo = document.querySelector('.goog-te-combo');
    if (googleCombo) {
        googleCombo.value = langCode;
        googleCombo.dispatchEvent(new Event('change'));
        return;
    }
    
    // Method 2: Set cookie and reload (Google Translate reads this)
    const domain = window.location.hostname;
    
    if (langCode === 'es') {
        // Reset to original language - remove Google Translate
        document.cookie = `googtrans=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=${domain}`;
        document.cookie = `googtrans=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
        document.cookie = `googtrans=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=.${domain}`;
        
        // Also try removing the Google Translate frame effect
        const frame = document.querySelector('.goog-te-banner-frame');
        if (frame) frame.style.display = 'none';
        
        // Reload to reset
        if (document.querySelector('.translated-ltr, .translated-rtl')) {
            window.location.reload();
        }
    } else {
        // Set translation cookie
        const cookieValue = `/es/${langCode}`;
        document.cookie = `googtrans=${cookieValue}; path=/; domain=${domain}`;
        document.cookie = `googtrans=${cookieValue}; path=/;`;
        document.cookie = `googtrans=${cookieValue}; path=/; domain=.${domain}`;
        
        // Reload to apply translation
        window.location.reload();
    }
}

// Check saved language on page load and apply if needed
window.addEventListener('load', () => {
    const savedLang = localStorage.getItem('selectedLanguage');
    if (savedLang && savedLang !== 'es') {
        // Check if page is already translated
        const googleCombo = document.querySelector('.goog-te-combo');
        if (googleCombo && googleCombo.value !== savedLang) {
            // Need to set the translation
            setTimeout(() => {
                googleCombo.value = savedLang;
                googleCombo.dispatchEvent(new Event('change'));
            }, 500);
        }
    }
    
    // Update UI to show current language
    if (savedLang) {
        updateSelectedLanguage(savedLang);
    }
});

// Export for use in other scripts
window.selectLanguage = selectLanguage;
window.updateSelectedLanguage = updateSelectedLanguage;

