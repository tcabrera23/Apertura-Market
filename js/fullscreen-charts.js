// Fullscreen chart functionality for dashboard
document.addEventListener('DOMContentLoaded', () => {
    // Wait for charts to be rendered
    setTimeout(() => {
        addFullscreenButtons();
    }, 2000);
});

function addFullscreenButtons() {
    // Find all chart containers
    const chartContainers = document.querySelectorAll('[id$="-charts-container"]');
    
    chartContainers.forEach(container => {
        if (!container || container.children.length === 0) return;
        
        // Get the grid container with charts
        const gridContainer = container.querySelector('.grid');
        if (!gridContainer) return;
        
        // Add fullscreen button to each chart panel
        const chartPanels = gridContainer.querySelectorAll('[style*="background-color"]');
        
        chartPanels.forEach((panel, index) => {
            // Skip if button already exists
            if (panel.querySelector('.fullscreen-btn')) return;
            
            // Find the header div
            const header = panel.querySelector('.flex.items-center.justify-between');
            if (!header) return;
            
            // Create fullscreen button
            const fullscreenBtn = document.createElement('button');
            fullscreenBtn.className = 'fullscreen-btn p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors';
            fullscreenBtn.title = 'Pantalla completa';
            fullscreenBtn.innerHTML = `
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"></path>
                </svg>
            `;
            
            // Add click handler
            fullscreenBtn.addEventListener('click', () => {
                toggleFullscreen(panel);
            });
            
            // Add button to header
            header.appendChild(fullscreenBtn);
        });
    });
}

function toggleFullscreen(panel) {
    if (!document.fullscreenElement) {
        // Enter fullscreen
        if (panel.requestFullscreen) {
            panel.requestFullscreen();
        } else if (panel.webkitRequestFullscreen) {
            panel.webkitRequestFullscreen();
        } else if (panel.msRequestFullscreen) {
            panel.msRequestFullscreen();
        }
        
        // Add fullscreen styling
        panel.style.maxHeight = '100vh';
        panel.style.overflow = 'auto';
        
        // Update button icon
        const btn = panel.querySelector('.fullscreen-btn');
        if (btn) {
            btn.innerHTML = `
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 9V4.5M9 9H4.5M9 9L3.75 3.75M9 15v4.5M9 15H4.5M9 15l-5.25 5.25M15 9h4.5M15 9V4.5M15 9l5.25-5.25M15 15h4.5M15 15v4.5m0-4.5l5.25 5.25"></path>
                </svg>
            `;
        }
    } else {
        // Exit fullscreen
        if (document.exitFullscreen) {
            document.exitFullscreen();
        } else if (document.webkitExitFullscreen) {
            document.webkitExitFullscreen();
        } else if (document.msExitFullscreen) {
            document.msExitFullscreen();
        }
    }
}

// Listen for fullscreen changes
document.addEventListener('fullscreenchange', handleFullscreenChange);
document.addEventListener('webkitfullscreenchange', handleFullscreenChange);
document.addEventListener('mozfullscreenchange', handleFullscreenChange);
document.addEventListener('MSFullscreenChange', handleFullscreenChange);

function handleFullscreenChange() {
    const fullscreenElement = document.fullscreenElement || document.webkitFullscreenElement || document.mozFullScreenElement || document.msFullscreenElement;
    
    if (!fullscreenElement) {
        // Exited fullscreen - restore button icon
        const buttons = document.querySelectorAll('.fullscreen-btn');
        buttons.forEach(btn => {
            btn.innerHTML = `
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"></path>
                </svg>
            `;
        });
    }
}

// Re-add fullscreen buttons when charts are re-rendered
if (typeof window.renderAnalysisCharts !== 'undefined') {
    const originalRenderAnalysisCharts = window.renderAnalysisCharts;
    window.renderAnalysisCharts = function(...args) {
        originalRenderAnalysisCharts.apply(this, args);
        setTimeout(() => {
            addFullscreenButtons();
        }, 500);
    };
}

