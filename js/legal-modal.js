// Legal Modal - Terms of Service and Privacy Policy
let legalContent = null;
let isFullScreen = false;
let currentSection = 'terms'; // 'terms' or 'privacy'

// Load legal content from markdown file
async function loadLegalContent() {
    if (legalContent) return legalContent;
    
    try {
        const response = await fetch('docs/LEGAL.md');
        if (!response.ok) throw new Error('Failed to load legal content');
        const text = await response.text();
        legalContent = parseMarkdownToHTML(text);
        return legalContent;
    } catch (error) {
        console.error('Error loading legal content:', error);
        return {
            terms: '<p>Error al cargar los términos de servicio. Por favor, contacte al soporte.</p>',
            privacy: '<p>Error al cargar la política de privacidad. Por favor, contacte al soporte.</p>'
        };
    }
}

// Parse markdown to HTML
function parseMarkdownToHTML(markdown) {
    const sections = {
        terms: '',
        privacy: ''
    };
    
    let currentSection = null;
    const lines = markdown.split('\n');
    let inList = false;
    let listItems = [];
    
    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        const trimmedLine = line.trim();
        
        // Detect section headers
        if (trimmedLine.startsWith('## Política de Privacidad')) {
            // Close any open list
            if (inList && listItems.length > 0) {
                sections[currentSection] += `<ul class="list-disc list-inside space-y-2 mb-4 ml-4">${listItems.join('')}</ul>`;
                listItems = [];
                inList = false;
            }
            currentSection = 'privacy';
            continue;
        } else if (trimmedLine.startsWith('## Términos de Servicio')) {
            // Close any open list
            if (inList && listItems.length > 0) {
                sections[currentSection] += `<ul class="list-disc list-inside space-y-2 mb-4 ml-4">${listItems.join('')}</ul>`;
                listItems = [];
                inList = false;
            }
            currentSection = 'terms';
            continue;
        }
        
        // Skip main title
        if (trimmedLine.startsWith('# ') && !trimmedLine.startsWith('##')) continue;
        
        // Process content based on current section
        if (currentSection && (currentSection === 'terms' || currentSection === 'privacy')) {
            // Separator
            if (trimmedLine === '---') {
                if (inList && listItems.length > 0) {
                    sections[currentSection] += `<ul class="list-disc list-inside space-y-2 mb-4 ml-4">${listItems.join('')}</ul>`;
                    listItems = [];
                    inList = false;
                }
                sections[currentSection] += '<hr class="my-8 border-gray-300 dark:border-gray-600">\n';
                continue;
            }
            
            // Headers
            if (trimmedLine.startsWith('### ')) {
                if (inList && listItems.length > 0) {
                    sections[currentSection] += `<ul class="list-disc list-inside space-y-2 mb-4 ml-4">${listItems.join('')}</ul>`;
                    listItems = [];
                    inList = false;
                }
                const headerText = trimmedLine.substring(4);
                sections[currentSection] += `<h3 class="text-xl font-bold text-gray-900 dark:text-white mt-6 mb-3">${headerText}</h3>\n`;
                continue;
            } else if (trimmedLine.startsWith('#### ')) {
                if (inList && listItems.length > 0) {
                    sections[currentSection] += `<ul class="list-disc list-inside space-y-2 mb-4 ml-4">${listItems.join('')}</ul>`;
                    listItems = [];
                    inList = false;
                }
                const headerText = trimmedLine.substring(5);
                sections[currentSection] += `<h4 class="text-lg font-bold text-gray-900 dark:text-white mt-4 mb-2">${headerText}</h4>\n`;
                continue;
            }
            
            // Lists
            if (trimmedLine.startsWith('- ') || trimmedLine.startsWith('* ')) {
                inList = true;
                let itemText = trimmedLine.substring(2);
                // Process inline formatting
                itemText = itemText.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900 dark:text-white">$1</strong>');
                itemText = itemText.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" class="text-green-500 hover:text-green-600 dark:text-green-400 dark:hover:text-green-300 underline" target="_blank" rel="noopener noreferrer">$1</a>');
                listItems.push(`<li class="text-gray-700 dark:text-gray-300 mb-2">${itemText}</li>\n`);
                continue;
            } else {
                // Close list if we were in one
                if (inList && listItems.length > 0) {
                    sections[currentSection] += `<ul class="list-disc list-inside space-y-2 mb-4 ml-4">${listItems.join('')}</ul>`;
                    listItems = [];
                    inList = false;
                }
            }
            
            // Empty lines
            if (!trimmedLine) {
                sections[currentSection] += '<br>\n';
                continue;
            }
            
            // Regular paragraphs
            let htmlLine = line;
            // Bold text
            htmlLine = htmlLine.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900 dark:text-white">$1</strong>');
            // Links
            htmlLine = htmlLine.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" class="text-green-500 hover:text-green-600 dark:text-green-400 dark:hover:text-green-300 underline" target="_blank" rel="noopener noreferrer">$1</a>');
            
            if (htmlLine.trim()) {
                sections[currentSection] += `<p class="text-gray-700 dark:text-gray-300 mb-4 leading-relaxed">${htmlLine}</p>\n`;
            }
        }
    }
    
    // Close any remaining list
    if (inList && listItems.length > 0) {
        sections[currentSection] += `<ul class="list-disc list-inside space-y-2 mb-4 ml-4">${listItems.join('')}</ul>`;
    }
    
    return sections;
}

// Open legal modal
async function openLegalModal(section = 'terms') {
    currentSection = section;
    const modal = document.getElementById('legalModal');
    const modalContent = document.getElementById('legalModalContent');
    const modalTitle = document.getElementById('legalModalTitle');
    const modalBody = document.getElementById('legalModalBody');
    
    // Reset full screen state
    isFullScreen = false;
    updateFullScreenState();
    
    // Set title
    if (section === 'terms') {
        modalTitle.textContent = 'Términos de Servicio';
    } else {
        modalTitle.textContent = 'Política de Privacidad';
    }
    
    // Show modal
    modal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
    
    // Load content
    modalBody.innerHTML = '<div class="flex items-center justify-center py-8"><div class="w-8 h-8 border-4 border-gray-200 dark:border-gray-700 border-t-green-500 rounded-full animate-spin"></div></div>';
    
    const content = await loadLegalContent();
    modalBody.innerHTML = content[section] || content.terms;
    
    // Scroll to top
    modalBody.scrollTop = 0;
}

// Close legal modal
function closeLegalModal() {
    const modal = document.getElementById('legalModal');
    modal.classList.add('hidden');
    document.body.style.overflow = '';
    isFullScreen = false;
    updateFullScreenState();
}

// Toggle full screen
function toggleFullScreen() {
    isFullScreen = !isFullScreen;
    updateFullScreenState();
}

// Update full screen state
function updateFullScreenState() {
    const modalContent = document.getElementById('legalModalContent');
    const maximizeIcon = document.getElementById('maximizeIcon');
    const minimizeIcon = document.getElementById('minimizeIcon');
    
    if (isFullScreen) {
        modalContent.classList.remove('max-w-4xl', 'max-h-[90vh]');
        modalContent.classList.add('w-full', 'h-full', 'max-w-full', 'max-h-full', 'rounded-none');
        maximizeIcon.classList.add('hidden');
        minimizeIcon.classList.remove('hidden');
    } else {
        modalContent.classList.remove('w-full', 'h-full', 'max-w-full', 'max-h-full', 'rounded-none');
        modalContent.classList.add('max-w-4xl', 'max-h-[90vh]');
        maximizeIcon.classList.remove('hidden');
        minimizeIcon.classList.add('hidden');
    }
}

// Accept legal terms
function acceptLegalTerms() {
    const acceptCheckbox = document.getElementById('acceptTerms');
    if (acceptCheckbox) {
        acceptCheckbox.checked = true;
        acceptCheckbox.dispatchEvent(new Event('change'));
    }
    closeLegalModal();
}

// Initialize event listeners
document.addEventListener('DOMContentLoaded', () => {
    const closeBtn = document.getElementById('closeLegalModal');
    const fullScreenBtn = document.getElementById('fullScreenToggle');
    const acceptBtn = document.getElementById('acceptLegalBtn');
    const modal = document.getElementById('legalModal');
    
    if (closeBtn) {
        closeBtn.addEventListener('click', closeLegalModal);
    }
    
    if (fullScreenBtn) {
        fullScreenBtn.addEventListener('click', toggleFullScreen);
    }
    
    if (acceptBtn) {
        acceptBtn.addEventListener('click', acceptLegalTerms);
    }
    
    // Close on backdrop click
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeLegalModal();
            }
        });
    }
    
    // Close on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
            closeLegalModal();
        }
    });
    
    // Enable/disable sign up button based on checkbox
    const acceptCheckbox = document.getElementById('acceptTerms');
    const signUpBtn = document.getElementById('signUpBtn');
    
    if (acceptCheckbox && signUpBtn) {
        acceptCheckbox.addEventListener('change', (e) => {
            signUpBtn.disabled = !e.target.checked;
        });
    }
});

// Make functions globally available
window.openLegalModal = openLegalModal;
window.closeLegalModal = closeLegalModal;

