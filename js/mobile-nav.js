// Mobile navigation handler
document.addEventListener('DOMContentLoaded', () => {
    // Create mobile menu button if it doesn't exist
    const nav = document.querySelector('nav');
    if (!nav) return;

    const navContainer = nav.querySelector('.max-w-7xl');
    if (!navContainer) return;

    const navContent = navContainer.querySelector('.flex.justify-between');
    if (!navContent) return;

    // Check if mobile menu button already exists
    let mobileMenuBtn = navContent.querySelector('#mobileMenuBtn');
    
    if (!mobileMenuBtn) {
        // Create mobile menu button
        mobileMenuBtn = document.createElement('button');
        mobileMenuBtn.id = 'mobileMenuBtn';
        mobileMenuBtn.className = 'md:hidden p-2 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors';
        mobileMenuBtn.innerHTML = `
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path id="menuIcon" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path>
                <path id="closeIcon" class="hidden" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
            </svg>
        `;
        
        // Add button to the right side of the nav (after dark mode toggle)
        const rightSection = navContent.querySelector('.flex.items-center.gap-4');
        if (rightSection) {
            rightSection.appendChild(mobileMenuBtn);
        }
    }

    // Create or get mobile menu
    let mobileMenu = document.getElementById('mobileMenu');
    
    if (!mobileMenu) {
        // Create mobile menu
        mobileMenu = document.createElement('div');
        mobileMenu.id = 'mobileMenu';
        mobileMenu.className = 'hidden md:hidden bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700';
        
        // Get navigation links from desktop menu
        const desktopMenu = navContent.querySelector('ul.hidden.md\\:flex');
        if (desktopMenu) {
            const navLinks = Array.from(desktopMenu.querySelectorAll('li a'));
            
            mobileMenu.innerHTML = `
                <nav class="px-4 py-4 space-y-2">
                    ${navLinks.map(link => `
                        <a href="${link.href}" class="block px-4 py-3 rounded-lg text-gray-600 dark:text-gray-300 hover:bg-green-50 dark:hover:bg-gray-700 hover:text-green-500 dark:hover:text-green-400 transition-colors font-medium ${link.classList.contains('text-green-500') ? 'bg-green-50 dark:bg-gray-700 text-green-500 dark:text-green-400' : ''}">
                            ${link.textContent}
                        </a>
                    `).join('')}
                </nav>
            `;
        }
        
        navContainer.appendChild(mobileMenu);
    }

    // Toggle mobile menu
    mobileMenuBtn.addEventListener('click', () => {
        const menuIcon = document.getElementById('menuIcon');
        const closeIcon = document.getElementById('closeIcon');
        
        if (mobileMenu.classList.contains('hidden')) {
            mobileMenu.classList.remove('hidden');
            mobileMenu.classList.add('block');
            menuIcon.classList.add('hidden');
            closeIcon.classList.remove('hidden');
        } else {
            mobileMenu.classList.add('hidden');
            mobileMenu.classList.remove('block');
            menuIcon.classList.remove('hidden');
            closeIcon.classList.add('hidden');
        }
    });

    // Close mobile menu when clicking on a link
    const mobileLinks = mobileMenu.querySelectorAll('a');
    mobileLinks.forEach(link => {
        link.addEventListener('click', () => {
            mobileMenu.classList.add('hidden');
            mobileMenu.classList.remove('block');
            const menuIcon = document.getElementById('menuIcon');
            const closeIcon = document.getElementById('closeIcon');
            menuIcon.classList.remove('hidden');
            closeIcon.classList.add('hidden');
        });
    });
});

