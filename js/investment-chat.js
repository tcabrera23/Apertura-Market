// Investment Chat Widget JavaScript
// Use window.N8N_WEBHOOK_URL if available, otherwise define it
const N8N_WEBHOOK_URL = window.N8N_WEBHOOK_URL || 'https://dev.n8n.tomascabrera.site/webhook/8958bcf0-8fa3-4947-b389-86ba88f44290/chat';
window.N8N_WEBHOOK_URL = N8N_WEBHOOK_URL;

// Generate or retrieve session ID
function getSessionId() {
    let sessionId = sessionStorage.getItem('investmentChatSessionId');
    if (!sessionId) {
        sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        sessionStorage.setItem('investmentChatSessionId', sessionId);
    }
    return sessionId;
}

document.addEventListener('DOMContentLoaded', async () => {
    // Check if user has a paid plan before showing chat widget
    const API_BASE_URL = window.API_BASE_URL || 'https://api.bullanalytics.io/api';
    const chatWidget = document.getElementById('investmentChatWidget');
    
    // Function to get auth token
    function getAuthToken() {
        return localStorage.getItem('access_token');
    }
    
    // Check user plan
    async function checkUserPlan() {
        const token = getAuthToken();
        if (!token) {
            // User not logged in, hide chat
            if (chatWidget) chatWidget.style.display = 'none';
            return false;
        }
        
        try {
            const response = await fetch(`${API_BASE_URL}/subscriptions/current`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            
            if (!response.ok) {
                // If error fetching subscription, hide chat
                if (chatWidget) chatWidget.style.display = 'none';
                return false;
            }
            
            const subscription = await response.json();
            const planName = subscription?.plan_name;
            
            // Only show chat for paid plans (plus or pro)
            // Check if user HAS plus or pro plan
            if (planName === 'plus' || planName === 'pro') {
                // User has paid plan, show chat
                if (chatWidget) chatWidget.style.display = 'block';
                return true;
            }
            
            // Hide chat for any other plan (free, gratis, gratuito, null, etc.)
            if (chatWidget) chatWidget.style.display = 'none';
            return false;
        } catch (error) {
            console.error('Error checking user plan:', error);
            // On error, hide chat as precaution
            if (chatWidget) chatWidget.style.display = 'none';
            return false;
        }
    }
    
    // Check plan first
    const hasPaidPlan = await checkUserPlan();
    if (!hasPaidPlan) {
        console.log('Chat widget hidden: User does not have a paid plan');
        return; // Don't initialize chat if user doesn't have paid plan
    }
    
    // Chat widget toggle
    const chatToggle = document.getElementById('investmentChatToggle');
    const chatWindow = document.getElementById('investmentChatWindow');
    const chatIcon = document.getElementById('investmentChatIcon');
    const closeIcon = document.getElementById('investmentCloseIcon');
    const chatCloseBtn = document.getElementById('investmentChatCloseBtn');
    const fullWindowToggle = document.getElementById('investmentFullWindowToggle');
    const maximizeIcon = document.getElementById('investmentMaximizeIcon');
    const minimizeIcon = document.getElementById('investmentMinimizeIcon');

    let isFullWindow = false;

    function openChat() {
        chatWindow.classList.remove('hidden');
        chatIcon.classList.add('hidden');
        closeIcon.classList.remove('hidden');
        // On mobile, prevent background scrolling
        if (window.innerWidth < 768) {
            document.body.style.overflow = 'hidden';
        }
        // Initialize window state
        updateFullWindowState();
    }

    function closeChat() {
        chatWindow.classList.add('hidden');
        chatIcon.classList.remove('hidden');
        closeIcon.classList.add('hidden');
        isFullWindow = false;
        updateFullWindowState();
        document.body.style.overflow = ''; // Restore scrolling
    }

    function toggleFullWindow() {
        isFullWindow = !isFullWindow;
        updateFullWindowState();
    }

    function updateFullWindowState() {
        if (isFullWindow) {
            // Full window mode - covers entire screen
            chatWindow.classList.remove('md:bottom-24', 'md:right-6', 'md:w-96', 'md:h-[600px]', 'md:rounded-2xl');
            chatWindow.classList.add('inset-0', 'w-full', 'h-full', 'rounded-none');
            maximizeIcon.classList.add('hidden');
            minimizeIcon.classList.remove('hidden');
        } else {
            // Normal mode - responsive
            chatWindow.classList.remove('inset-0', 'w-full', 'h-full', 'rounded-none');
            // On mobile (< 768px), always full screen
            if (window.innerWidth < 768) {
                chatWindow.classList.add('bottom-0', 'right-0', 'left-0', 'top-0', 'w-full', 'h-full', 'rounded-none');
                chatWindow.classList.remove('md:bottom-24', 'md:right-6', 'md:w-96', 'md:h-[600px]', 'md:rounded-2xl');
            } else {
                // On desktop, show as window
                chatWindow.classList.add('md:bottom-24', 'md:right-6', 'md:w-96', 'md:h-[600px]', 'md:rounded-2xl');
                chatWindow.classList.remove('bottom-0', 'right-0', 'left-0', 'top-0', 'w-full', 'h-full', 'rounded-none');
            }
            maximizeIcon.classList.remove('hidden');
            minimizeIcon.classList.add('hidden');
        }
    }

    // Handle window resize
    window.addEventListener('resize', () => {
        if (!chatWindow.classList.contains('hidden')) {
            if (!isFullWindow) {
                if (window.innerWidth < 768) {
                    chatWindow.classList.add('bottom-0', 'right-0', 'left-0', 'top-0', 'w-full', 'h-full', 'rounded-none');
                    chatWindow.classList.remove('md:bottom-24', 'md:right-6', 'md:w-96', 'md:h-[600px]', 'md:rounded-2xl');
                } else {
                    chatWindow.classList.remove('bottom-0', 'right-0', 'left-0', 'top-0', 'w-full', 'h-full', 'rounded-none');
                    chatWindow.classList.add('md:bottom-24', 'md:right-6', 'md:w-96', 'md:h-[600px]', 'md:rounded-2xl');
                }
            }
        }
    });

    chatToggle.addEventListener('click', () => {
        const isHidden = chatWindow.classList.contains('hidden');
        if (isHidden) {
            openChat();
        } else {
            closeChat();
        }
    });

    chatCloseBtn.addEventListener('click', () => {
        closeChat();
    });

    fullWindowToggle.addEventListener('click', () => {
        toggleFullWindow();
    });

    // Close chat with Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && !chatWindow.classList.contains('hidden')) {
            closeChat();
        }
    });
});

// Send message to n8n webhook
async function sendInvestmentChatMessage() {
    const chatInput = document.getElementById('investmentChatInput');
    const chatMessages = document.getElementById('investmentChatMessages');
    const message = chatInput.value.trim();

    if (!message) {
        return;
    }

    // Add user message to chat
    addInvestmentChatMessage(message, 'user');
    chatInput.value = '';

    // Show loading
    const loadingId = addInvestmentChatMessage('Pensando...', 'assistant', true);

    try {
        const sessionId = getSessionId();
        
        const response = await fetch(N8N_WEBHOOK_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                chatInput: message,
                sessionId: sessionId
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();

        // Remove loading message
        const loadingEl = document.getElementById(loadingId);
        if (loadingEl) {
            loadingEl.remove();
        }

        // Extract response from n8n output
        // Try different possible response structures
        let responseText = '';
        
        // Check for result.output (string or object)
        if (result.output) {
            if (typeof result.output === 'string') {
                responseText = result.output;
            } else if (result.output.data) {
                if (typeof result.output.data === 'string') {
                    responseText = result.output.data;
                } else if (result.output.data.message) {
                    responseText = result.output.data.message;
                } else if (result.output.data.response) {
                    responseText = result.output.data.response;
                } else if (result.output.data.text) {
                    responseText = result.output.data.text;
                } else {
                    responseText = JSON.stringify(result.output.data, null, 2);
                }
            } else if (result.output.message) {
                responseText = result.output.message;
            } else if (result.output.response) {
                responseText = result.output.response;
            } else {
                responseText = JSON.stringify(result.output, null, 2);
            }
        } else if (result.data) {
            // If response is directly in data
            if (typeof result.data === 'string') {
                responseText = result.data;
            } else if (result.data.message) {
                responseText = result.data.message;
            } else if (result.data.response) {
                responseText = result.data.response;
            } else {
                responseText = JSON.stringify(result.data, null, 2);
            }
        } else if (result.message) {
            responseText = result.message;
        } else if (result.response) {
            responseText = result.response;
        } else if (result.text) {
            responseText = result.text;
        } else if (typeof result === 'string') {
            responseText = result;
        } else {
            // Fallback: show the whole response
            responseText = JSON.stringify(result, null, 2);
        }

        if (responseText) {
            // Check if response is already HTML or markdown
            const isHtml = /<[a-z][\s\S]*>/i.test(responseText);
            
            let htmlContent;
            if (isHtml) {
                // Already HTML, just clean and style it
                htmlContent = cleanAndStyleHtml(responseText);
            } else {
                // Markdown, parse it
                htmlContent = parseMarkdownToHtml(responseText);
            }
            
            addInvestmentChatMessage(htmlContent, 'assistant', false, '', true);
        } else {
            addInvestmentChatMessage(
                'Lo siento, no pude procesar la respuesta del asistente. Por favor, intenta de nuevo.',
                'assistant',
                false,
                'text-red-600 dark:text-red-400'
            );
        }

    } catch (error) {
        console.error('Error sending chat message:', error);
        
        // Remove loading message
        const loadingEl = document.getElementById(loadingId);
        if (loadingEl) {
            loadingEl.remove();
        }

        addInvestmentChatMessage(
            `❌ Error de conexión: ${error.message}\n\nPor favor, verifica tu conexión e intenta de nuevo.`,
            'assistant',
            false,
            'text-red-600 dark:text-red-400'
        );
    }
}

function addInvestmentChatMessage(message, sender, isLoading = false, textColor = '', isHtml = false) {
    const chatMessages = document.getElementById('investmentChatMessages');
    const messageId = `msg-${Date.now()}-${Math.random()}`;
    
    const messageDiv = document.createElement('div');
    messageDiv.id = messageId;
    messageDiv.className = `flex items-start gap-3 ${isLoading ? 'opacity-70' : ''}`;
    
    if (sender === 'user') {
        messageDiv.innerHTML = `
            <div class="flex-1"></div>
            <div class="flex-1 bg-gradient-to-r from-green-500 to-green-600 text-white rounded-lg p-3 max-w-[80%]">
                <p class="text-sm whitespace-pre-wrap">${escapeHtml(message)}</p>
            </div>
        `;
    } else {
        messageDiv.innerHTML = `
            <div class="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 overflow-hidden">
                <img src="images/agent.png" alt="BullAgent" class="w-full h-full object-cover">
            </div>
            <div class="flex-1 bg-gray-100 dark:bg-gray-700 rounded-lg p-3">
                <div class="text-sm text-gray-700 dark:text-gray-300 ${textColor} ${isHtml ? '' : 'whitespace-pre-wrap'}">${isHtml ? message : escapeHtml(message)}</div>
            </div>
        `;
    }
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return messageId;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function parseMarkdownToHtml(markdown) {
    if (!markdown) return '';
    
    let html = markdown;
    
    // Replace \n with actual newlines
    html = html.replace(/\\n/g, '\n');
    
    // Parse markdown tables - more robust approach
    const lines = html.split('\n');
    const processedLines = [];
    let inTable = false;
    let tableRows = [];
    
    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        const trimmedLine = line.trim();
        
        // Check if line is a table row (starts and ends with |)
        if (trimmedLine.startsWith('|') && trimmedLine.endsWith('|') && trimmedLine.length > 2) {
            // Check if it's a separator row (contains only dashes and pipes)
            if (/^\|[\s\-:]+\|$/.test(trimmedLine)) {
                // Skip separator rows
                continue;
            }
            
            // It's a data row
            inTable = true;
            const cells = trimmedLine.slice(1, -1).split('|').map(cell => cell.trim());
            tableRows.push(cells);
        } else {
            // Not a table row
            if (inTable && tableRows.length > 0) {
                // Process accumulated table rows
                let tableHtml = '<div class="overflow-x-auto my-4"><table class="w-full border-collapse border border-gray-300 dark:border-gray-600 text-sm">';
                
                tableRows.forEach((row, rowIndex) => {
                    const isHeader = rowIndex === 0;
                    const tag = isHeader ? 'th' : 'td';
                    const cellClass = isHeader 
                        ? 'px-4 py-2 bg-gray-100 dark:bg-gray-800 font-semibold border-b border-gray-300 dark:border-gray-600'
                        : 'px-4 py-2 border-b border-gray-200 dark:border-gray-600';
                    
                    tableHtml += '<tr>';
                    row.forEach(cell => {
                        const processedCell = parseInlineMarkdown(cell);
                        tableHtml += `<${tag} class="${cellClass}">${processedCell}</${tag}>`;
                    });
                    tableHtml += '</tr>';
                });
                
                tableHtml += '</table></div>';
                processedLines.push(tableHtml);
                tableRows = [];
                inTable = false;
            }
            
            if (trimmedLine) {
                processedLines.push(line);
            }
        }
    }
    
    // Handle table at end of text
    if (inTable && tableRows.length > 0) {
        let tableHtml = '<div class="overflow-x-auto my-4"><table class="w-full border-collapse border border-gray-300 dark:border-gray-600 text-sm">';
        
        tableRows.forEach((row, rowIndex) => {
            const isHeader = rowIndex === 0;
            const tag = isHeader ? 'th' : 'td';
            const cellClass = isHeader 
                ? 'px-4 py-2 bg-gray-100 dark:bg-gray-800 font-semibold border-b border-gray-300 dark:border-gray-600'
                : 'px-4 py-2 border-b border-gray-200 dark:border-gray-600';
            
            tableHtml += '<tr>';
            row.forEach(cell => {
                const processedCell = parseInlineMarkdown(cell);
                tableHtml += `<${tag} class="${cellClass}">${processedCell}</${tag}>`;
            });
            tableHtml += '</tr>';
        });
        
        tableHtml += '</table></div>';
        processedLines.push(tableHtml);
    }
    
    html = processedLines.join('\n');
    
    // Parse bold text (**text**)
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong class="font-bold text-gray-900 dark:text-white">$1</strong>');
    
    // Parse bullet points (• or -)
    html = html.replace(/^[\s]*[•\-]\s+(.+)$/gm, '<li class="ml-4 mb-1">$1</li>');
    
    // Wrap consecutive list items in ul
    html = html.replace(/(<li[^>]*>.*?<\/li>(?:\s*<li[^>]*>.*?<\/li>)*)/gs, (match) => {
        return `<ul class="list-disc list-inside my-2 space-y-1">${match}</ul>`;
    });
    
    // Parse section headers (lines that are bold and standalone)
    html = html.replace(/^(\*\*[^*]+\*\*)$/gm, '<h3 class="font-bold text-lg mt-4 mb-2 text-gray-900 dark:text-white">$1</h3>');
    html = html.replace(/\*\*/g, ''); // Remove remaining **
    
    // Parse numbered lists
    html = html.replace(/^\d+\.\s+(.+)$/gm, '<li class="ml-4 mb-1 list-decimal">$1</li>');
    html = html.replace(/(<li class="ml-4 mb-1 list-decimal">.*?<\/li>(?:\s*<li class="ml-4 mb-1 list-decimal">.*?<\/li>)*)/gs, (match) => {
        return `<ol class="list-decimal list-inside my-2 space-y-1">${match.replace(/ class="ml-4 mb-1 list-decimal"/g, '')}</ol>`;
    });
    
    // Parse code blocks (```code```)
    html = html.replace(/```([^`]+)```/g, '<pre class="bg-gray-800 dark:bg-gray-900 text-gray-100 p-3 rounded-lg overflow-x-auto my-2"><code>$1</code></pre>');
    
    // Parse inline code (`code`)
    html = html.replace(/`([^`]+)`/g, '<code class="bg-gray-200 dark:bg-gray-800 px-1 py-0.5 rounded text-sm font-mono">$1</code>');
    
    // Parse paragraphs (double newlines)
    html = html.split(/\n\n+/).map(para => {
        para = para.trim();
        if (!para) return '';
        // Don't wrap if it's already a block element
        if (para.startsWith('<') && (para.startsWith('<h') || para.startsWith('<ul') || para.startsWith('<ol') || para.startsWith('<table') || para.startsWith('<div') || para.startsWith('<pre'))) {
            return para;
        }
        return `<p class="mb-2">${para}</p>`;
    }).join('\n');
    
    // Parse single newlines as <br>
    html = html.replace(/\n/g, '<br>');
    
    // Clean up empty paragraphs
    html = html.replace(/<p class="mb-2"><br><\/p>/g, '');
    html = html.replace(/<p class="mb-2"><\/p>/g, '');
    
    return html;
}

function parseInlineMarkdown(text) {
    if (!text) return '';
    
    let html = text;
    
    // Parse bold
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong class="font-bold">$1</strong>');
    
    // Parse italic
    html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    
    // Escape HTML
    html = escapeHtml(html);
    
    // Re-apply bold (since escapeHtml removed it)
    html = html.replace(/&lt;strong class="font-bold"&gt;([^&]+)&lt;\/strong&gt;/g, '<strong class="font-bold">$1</strong>');
    html = html.replace(/&lt;em&gt;([^&]+)&lt;\/em&gt;/g, '<em>$1</em>');
    
    return html;
}

function cleanAndStyleHtml(html) {
    if (!html) return '';
    
    // First, normalize whitespace - replace multiple newlines/spaces with single space
    html = html.replace(/\s+/g, ' ');
    
    // Remove spaces between tags (but preserve content)
    html = html.replace(/>\s+</g, '><');
    
    // Add back single space after opening tags for readability (except for inline elements)
    html = html.replace(/><([^/])/g, '> <$1');
    
    // Remove spaces before closing tags
    html = html.replace(/\s+<\//g, '</');
    
    // Style tables - wrap in container and add classes
    html = html.replace(/<table(\s[^>]*)?>/gi, (match, attrs = '') => {
        // Check if class already exists
        if (/class\s*=/i.test(attrs)) {
            return match.replace(/class\s*=\s*["']([^"']*)["']/i, (m, classes) => {
                return `class="${classes} w-full border-collapse border border-gray-300 dark:border-gray-600 text-sm"`;
            });
        }
        return `<div class="overflow-x-auto my-4"><table class="w-full border-collapse border border-gray-300 dark:border-gray-600 text-sm"${attrs}>`;
    });
    html = html.replace(/<\/table>/gi, '</table></div>');
    
    // Style table headers - add classes if not present
    html = html.replace(/<th(\s[^>]*)?>/gi, (match, attrs = '') => {
        if (/class\s*=/i.test(attrs)) {
            return match.replace(/class\s*=\s*["']([^"']*)["']/i, (m, classes) => {
                return `class="${classes} px-4 py-2 bg-gray-100 dark:bg-gray-800 font-semibold border-b border-gray-300 dark:border-gray-600"`;
            });
        }
        return `<th class="px-4 py-2 bg-gray-100 dark:bg-gray-800 font-semibold border-b border-gray-300 dark:border-gray-600"${attrs}>`;
    });
    
    // Style table cells - add classes if not present
    html = html.replace(/<td(\s[^>]*)?>/gi, (match, attrs = '') => {
        if (/class\s*=/i.test(attrs)) {
            return match.replace(/class\s*=\s*["']([^"']*)["']/i, (m, classes) => {
                return `class="${classes} px-4 py-2 border-b border-gray-200 dark:border-gray-600"`;
            });
        }
        return `<td class="px-4 py-2 border-b border-gray-200 dark:border-gray-600"${attrs}>`;
    });
    
    // Style table rows
    html = html.replace(/<tr(\s[^>]*)?>/gi, (match, attrs = '') => {
        if (/class\s*=/i.test(attrs)) {
            return match;
        }
        return `<tr class="hover:bg-gray-50 dark:hover:bg-gray-800/50"${attrs}>`;
    });
    
    // Style headings - add classes if not present
    html = html.replace(/<h1(\s[^>]*)?>/gi, (match, attrs = '') => {
        if (/class\s*=/i.test(attrs)) {
            return match.replace(/class\s*=\s*["']([^"']*)["']/i, (m, classes) => {
                return `class="${classes} text-2xl font-bold mt-6 mb-4 text-gray-900 dark:text-white"`;
            });
        }
        return `<h1 class="text-2xl font-bold mt-6 mb-4 text-gray-900 dark:text-white"${attrs}>`;
    });
    
    html = html.replace(/<h2(\s[^>]*)?>/gi, (match, attrs = '') => {
        if (/class\s*=/i.test(attrs)) {
            return match.replace(/class\s*=\s*["']([^"']*)["']/i, (m, classes) => {
                return `class="${classes} text-xl font-bold mt-5 mb-3 text-gray-900 dark:text-white"`;
            });
        }
        return `<h2 class="text-xl font-bold mt-5 mb-3 text-gray-900 dark:text-white"${attrs}>`;
    });
    
    html = html.replace(/<h3(\s[^>]*)?>/gi, (match, attrs = '') => {
        if (/class\s*=/i.test(attrs)) {
            return match.replace(/class\s*=\s*["']([^"']*)["']/i, (m, classes) => {
                return `class="${classes} text-lg font-bold mt-4 mb-2 text-gray-900 dark:text-white"`;
            });
        }
        return `<h3 class="text-lg font-bold mt-4 mb-2 text-gray-900 dark:text-white"${attrs}>`;
    });
    
    // Style paragraphs - add classes if not present
    html = html.replace(/<p(\s[^>]*)?>/gi, (match, attrs = '') => {
        if (/class\s*=/i.test(attrs)) {
            return match.replace(/class\s*=\s*["']([^"']*)["']/i, (m, classes) => {
                return `class="${classes} mb-3 text-gray-700 dark:text-gray-300 leading-relaxed"`;
            });
        }
        return `<p class="mb-3 text-gray-700 dark:text-gray-300 leading-relaxed"${attrs}>`;
    });
    
    // Style strong tags - add classes if not present
    html = html.replace(/<strong(\s[^>]*)?>/gi, (match, attrs = '') => {
        if (/class\s*=/i.test(attrs)) {
            return match.replace(/class\s*=\s*["']([^"']*)["']/i, (m, classes) => {
                return `class="${classes} font-bold text-gray-900 dark:text-white"`;
            });
        }
        return `<strong class="font-bold text-gray-900 dark:text-white"${attrs}>`;
    });
    
    // Style lists
    html = html.replace(/<ul(\s[^>]*)?>/gi, (match, attrs = '') => {
        if (/class\s*=/i.test(attrs)) {
            return match.replace(/class\s*=\s*["']([^"']*)["']/i, (m, classes) => {
                return `class="${classes} list-disc list-inside my-3 space-y-1 ml-4"`;
            });
        }
        return `<ul class="list-disc list-inside my-3 space-y-1 ml-4"${attrs}>`;
    });
    
    html = html.replace(/<ol(\s[^>]*)?>/gi, (match, attrs = '') => {
        if (/class\s*=/i.test(attrs)) {
            return match.replace(/class\s*=\s*["']([^"']*)["']/i, (m, classes) => {
                return `class="${classes} list-decimal list-inside my-3 space-y-1 ml-4"`;
            });
        }
        return `<ol class="list-decimal list-inside my-3 space-y-1 ml-4"${attrs}>`;
    });
    
    html = html.replace(/<li(\s[^>]*)?>/gi, (match, attrs = '') => {
        if (/class\s*=/i.test(attrs)) {
            return match.replace(/class\s*=\s*["']([^"']*)["']/i, (m, classes) => {
                return `class="${classes} mb-1 text-gray-700 dark:text-gray-300"`;
            });
        }
        return `<li class="mb-1 text-gray-700 dark:text-gray-300"${attrs}>`;
    });
    
    return html;
}

// Make sendInvestmentChatMessage available globally
window.sendInvestmentChatMessage = sendInvestmentChatMessage;

