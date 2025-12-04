// Rules Page JavaScript

// Use window.API_BASE_URL if available, otherwise use default
const getApiBaseUrl = () => window.API_BASE_URL || 'http://localhost:8080/api';

// Obtener token del localStorage
function getAuthToken() {
    return localStorage.getItem('access_token');
}

document.addEventListener('DOMContentLoaded', () => {
    // Verificar autenticación
    const token = getAuthToken();
    if (!token) {
        window.location.href = 'login.html';
        return;
    }
    
    loadRules();

    const ruleModal = document.getElementById('ruleModal');
    const createRuleBtn = document.getElementById('createRuleBtn');
    const closeModalBtn = document.getElementById('closeModal');
    const ruleForm = document.getElementById('ruleForm');

    // Modal handlers
    createRuleBtn.addEventListener('click', () => {
        ruleModal.classList.remove('hidden');
        ruleModal.classList.add('flex');
        document.body.style.overflow = 'hidden'; // Prevent background scrolling
    });

    closeModalBtn.addEventListener('click', () => {
        ruleModal.classList.add('hidden');
        ruleModal.classList.remove('flex');
        ruleForm.reset();
        document.body.style.overflow = ''; // Restore scrolling
    });

    // Close modal when clicking outside
    ruleModal.addEventListener('click', (e) => {
        if (e.target === ruleModal) {
            ruleModal.classList.add('hidden');
            ruleModal.classList.remove('flex');
            ruleForm.reset();
            document.body.style.overflow = '';
        }
    });

    // Close modal with Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && !ruleModal.classList.contains('hidden')) {
            ruleModal.classList.add('hidden');
            ruleModal.classList.remove('flex');
            ruleForm.reset();
            document.body.style.overflow = '';
        }
    });

    // Form submission
    ruleForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const submitBtn = document.getElementById('ruleSubmitBtn');
        const ruleId = submitBtn?.getAttribute('data-rule-id');
        if (ruleId) {
            await updateRule(ruleId);
        } else {
            await createRule();
        }
    });
    
    // Reset modal when closed
    closeModalBtn.addEventListener('click', () => {
        // Reset form handler
        const submitBtn = document.getElementById('ruleSubmitBtn');
        if (submitBtn) {
            submitBtn.textContent = 'Crear Regla';
            submitBtn.removeAttribute('data-rule-id');
        }
        const modalTitleText = document.getElementById('ruleModalTitleText');
        if (modalTitleText) {
            modalTitleText.textContent = 'Crear Nueva Regla';
        }
    });
});

async function loadRules() {
    const loadingEl = document.getElementById('rulesLoading');
    const containerEl = document.getElementById('rulesContainer');
    const listEl = document.getElementById('rulesList');
    const emptyEl = document.getElementById('emptyState');

    loadingEl.classList.remove('hidden');
    loadingEl.classList.add('flex');
    containerEl.classList.add('hidden');
    containerEl.classList.remove('block');

    try {
        const token = getAuthToken();
        if (!token) {
            window.location.href = 'login.html';
            return;
        }

        const response = await fetch(`${getApiBaseUrl()}/rules`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            if (response.status === 401) {
                // Token inválido, redirigir al login
                localStorage.removeItem('access_token');
                localStorage.removeItem('user_data');
                window.location.href = 'login.html';
                return;
            }
            // Si es un error del servidor (500, etc.), lanzar error
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || errorData.message || 'Error al cargar reglas');
        }

        const rules = await response.json();

        // Verificar que rules sea un array
        if (!Array.isArray(rules)) {
            console.error('Invalid response format:', rules);
            throw new Error('Formato de respuesta inválido');
        }

        loadingEl.classList.add('hidden');
        loadingEl.classList.remove('flex');
        containerEl.classList.remove('hidden');
        containerEl.classList.add('block');

        if (rules.length === 0) {
            listEl.classList.add('hidden');
            emptyEl.classList.remove('hidden');
        } else {
            listEl.innerHTML = '';
            rules.forEach(rule => {
                const card = createRuleCard(rule);
                listEl.appendChild(card);
            });
            listEl.classList.remove('hidden');
            emptyEl.classList.add('hidden');
        }

    } catch (error) {
        console.error('Error loading rules:', error);
        loadingEl.classList.add('hidden');
        loadingEl.classList.remove('flex');
        containerEl.classList.remove('hidden');
        containerEl.classList.add('block');
        listEl.classList.add('hidden');
        emptyEl.classList.remove('hidden');
        // Mostrar mensaje de error solo si es un error de conexión, no si es un array vacío
        if (error.message && !error.message.includes('Formato')) {
            emptyEl.innerHTML = `
                <div class="text-center py-12">
                    <p class="text-red-500 text-lg font-semibold mb-2">❌ Error al cargar las reglas</p>
                    <p class="text-gray-600 dark:text-gray-400 text-sm">${error.message}</p>
                </div>
            `;
        }
    }
}

function createRuleCard(rule) {
    const card = document.createElement('div');
    card.className = 'bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700 flex justify-between items-center hover:shadow-xl hover:scale-[1.02] transition-all';

    const typeLabels = {
        'price_below': 'Precio debajo',
        'price_above': 'Precio encima',
        'pe_below': 'P/E debajo',
        'pe_above': 'P/E encima',
        'max_distance': 'Distancia del máximo'
    };

    card.innerHTML = `
        <div class="flex-1">
            <div class="font-bold text-lg text-gray-900 dark:text-white mb-2">${rule.name || 'Regla sin nombre'}</div>
            <div class="flex flex-wrap gap-3">
                <span class="px-3 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded-full text-xs font-semibold">${typeLabels[rule.rule_type] || rule.type || rule.rule_type}</span>
                <span class="text-sm text-gray-600 dark:text-gray-400 flex items-center gap-1">📊 ${rule.ticker}</span>
                <span class="text-sm text-gray-600 dark:text-gray-400 flex items-center gap-1">🎯 ${rule.value_threshold || rule.value}</span>
            </div>
        </div>
        <div class="ml-4 flex items-center gap-2">
            <button class="w-9 h-9 flex items-center justify-center rounded-lg bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 hover:bg-blue-200 dark:hover:bg-blue-900/50 transition-colors" onclick="editRule('${rule.id}')" title="Editar">
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" fill="currentColor"/>
                </svg>
            </button>
            <button class="w-9 h-9 flex items-center justify-center rounded-lg bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 hover:bg-red-200 dark:hover:bg-red-900/50 transition-colors" onclick="deleteRule('${rule.id}')" title="Eliminar">
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M6 6L14 14M6 14L14 6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                </svg>
            </button>
        </div>
    `;

    return card;
}

async function createRule() {
    const formData = {
        name: document.getElementById('ruleName').value,
        rule_type: document.getElementById('ruleType').value,  // Cambiado de 'type' a 'rule_type'
        ticker: document.getElementById('ruleTicker').value.toUpperCase(),
        value: parseFloat(document.getElementById('ruleValue').value)
        // Email is automatically taken from authenticated user's account
    };

    try {
        const token = getAuthToken();
        if (!token) {
            window.location.href = 'login.html';
            return;
        }

        const response = await fetch(`${getApiBaseUrl()}/rules`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(formData)
        });

        if (!response.ok) {
            if (response.status === 401) {
                console.error('401 Unauthorized - Token inválido o expirado');
                localStorage.removeItem('access_token');
                localStorage.removeItem('user_data');
                alert('Tu sesión ha expirado. Por favor, inicia sesión nuevamente.');
                window.location.href = 'login.html';
                return;
            }
            const errorData = await response.json().catch(() => ({}));
            const errorMessage = errorData.detail || errorData.message || 'Error al crear regla';
            console.error('Error creating rule:', errorMessage, response.status);
            console.error('Full error response:', errorData);
            alert(`Error al crear la regla: ${errorMessage}`);
            return;
        }

        const result = await response.json();
        console.log('Rule created successfully:', result);

        const ruleModal = document.getElementById('ruleModal');
        ruleModal.classList.add('hidden');
        ruleModal.classList.remove('flex');
        document.getElementById('ruleForm').reset();
        document.body.style.overflow = '';
        
        // Reset modal title and button
        const modalTitleText = document.getElementById('ruleModalTitleText');
        if (modalTitleText) {
            modalTitleText.textContent = 'Crear Nueva Regla';
        }
        const submitBtn = document.getElementById('ruleSubmitBtn');
        if (submitBtn) {
            submitBtn.textContent = 'Crear Regla';
            submitBtn.removeAttribute('data-rule-id');
        }
        
        loadRules();

    } catch (error) {
        console.error('Error creating rule:', error);
        alert(`Error al crear la regla: ${error.message || 'Por favor, intenta de nuevo.'}`);
    }
}

async function editRule(ruleId) {
    try {
        const token = getAuthToken();
        if (!token) {
            window.location.href = 'login.html';
            return;
        }

        // Get rule data
        const response = await fetch(`${getApiBaseUrl()}/rules`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            throw new Error('Error al cargar regla');
        }

        const rules = await response.json();
        const rule = rules.find(r => r.id === ruleId);

        if (!rule) {
            alert('Regla no encontrada');
            return;
        }

        // Populate form with rule data
        document.getElementById('ruleName').value = rule.name || '';
        document.getElementById('ruleType').value = rule.rule_type || rule.type || '';
        document.getElementById('ruleTicker').value = rule.ticker || '';
        document.getElementById('ruleValue').value = rule.value_threshold || rule.value || '';

        // Change modal title and button
        const modalTitleText = document.getElementById('ruleModalTitleText');
        if (modalTitleText) {
            modalTitleText.textContent = 'Editar Regla';
        }

        const submitBtn = document.getElementById('ruleSubmitBtn');
        if (submitBtn) {
            submitBtn.textContent = 'Guardar Cambios';
            submitBtn.setAttribute('data-rule-id', ruleId);
        }

        // Show modal
        const ruleModal = document.getElementById('ruleModal');
        ruleModal.classList.remove('hidden');
        ruleModal.classList.add('flex');
        document.body.style.overflow = 'hidden';

    } catch (error) {
        console.error('Error loading rule for edit:', error);
        alert('Error al cargar la regla para editar.');
    }
}

async function updateRule(ruleId) {
    const formData = {
        name: document.getElementById('ruleName').value,
        rule_type: document.getElementById('ruleType').value,
        ticker: document.getElementById('ruleTicker').value.toUpperCase(),
        value: parseFloat(document.getElementById('ruleValue').value)
    };

    try {
        const token = getAuthToken();
        if (!token) {
            window.location.href = 'login.html';
            return;
        }

        const response = await fetch(`${getApiBaseUrl()}/rules/${ruleId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(formData)
        });

        if (!response.ok) {
            if (response.status === 401) {
                localStorage.removeItem('access_token');
                localStorage.removeItem('user_data');
                alert('Tu sesión ha expirado. Por favor, inicia sesión nuevamente.');
                window.location.href = 'login.html';
                return;
            }
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || errorData.message || 'Error al actualizar regla');
        }

        const result = await response.json();
        console.log('Rule updated successfully:', result);

        // Close modal and reset
        const ruleModal = document.getElementById('ruleModal');
        ruleModal.classList.add('hidden');
        ruleModal.classList.remove('flex');
        document.getElementById('ruleForm').reset();
        document.body.style.overflow = '';

        // Reset modal title and button
        const modalTitleText = document.getElementById('ruleModalTitleText');
        if (modalTitleText) {
            modalTitleText.textContent = 'Crear Nueva Regla';
        }

        const submitBtn = document.getElementById('ruleSubmitBtn');
        if (submitBtn) {
            submitBtn.textContent = 'Crear Regla';
            submitBtn.removeAttribute('data-rule-id');
        }

        loadRules();

    } catch (error) {
        console.error('Error updating rule:', error);
        alert(`Error al actualizar la regla: ${error.message || 'Por favor, intenta de nuevo.'}`);
    }
}

async function deleteRule(ruleId) {
    if (!confirm('¿Estás seguro de que quieres eliminar esta regla?')) {
        return;
    }

    try {
        const token = getAuthToken();
        if (!token) {
            window.location.href = 'login.html';
            return;
        }

        const response = await fetch(`${getApiBaseUrl()}/rules/${ruleId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            if (response.status === 401) {
                localStorage.removeItem('access_token');
                localStorage.removeItem('user_data');
                window.location.href = 'login.html';
                return;
            }
            throw new Error('Error al eliminar regla');
        }

        loadRules();

    } catch (error) {
        console.error('Error deleting rule:', error);
        alert('Error al eliminar la regla.');
    }
}

// Chat functions
async function sendChatMessage() {
    const chatInput = document.getElementById('chatInput');
    const chatMessages = document.getElementById('chatMessages');
    const message = chatInput.value.trim();

    if (!message) {
        return;
    }

    // Check if user is authenticated
    const token = getAuthToken();
    if (!token) {
        alert('Por favor, inicia sesión para crear reglas.');
        window.location.href = 'login.html';
        return;
    }

    // Add user message to chat
    addChatMessage(message, 'user');
    chatInput.value = '';

    // Show loading
    const loadingId = addChatMessage('Procesando tu solicitud...', 'assistant', true);

    try {
        // Get auth token if available
        const token = getAuthToken();
        const headers = {
            'Content-Type': 'application/json'
        };
        
        // Add authorization header if token exists
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        const response = await fetch(`${getApiBaseUrl()}/rules/chat`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({
                message: message
                // Email is automatically taken from authenticated user's account
            })
        });

        const result = await response.json();

        // Remove loading message
        const loadingEl = document.getElementById(loadingId);
        if (loadingEl) {
            loadingEl.remove();
        }

        if (result.success) {
            // Check if authentication is required
            if (result.requires_auth) {
                addChatMessage(
                    `⚠️ ${result.message}\n\n` +
                    `📋 Nombre: ${result.rule.name}\n` +
                    `📊 Tipo: ${getTypeLabel(result.rule.rule_type || result.rule.type)}\n` +
                    `🎯 Ticker: ${result.rule.ticker}\n` +
                    `💵 Valor: ${result.rule.value}\n\n` +
                    `Por favor, inicia sesión para guardar esta regla. Las notificaciones se enviarán a tu email de cuenta.`,
                    'assistant',
                    false,
                    'text-yellow-600 dark:text-yellow-400'
                );
            } else {
                // Show success message
                addChatMessage(
                    `✅ ¡Regla creada exitosamente!\n\n` +
                    `📋 Nombre: ${result.rule.name}\n` +
                    `📊 Tipo: ${getTypeLabel(result.rule.rule_type || result.rule.type)}\n` +
                    `🎯 Ticker: ${result.rule.ticker}\n` +
                    `💵 Valor: ${result.rule.value}\n\n` +
                    `Las notificaciones se enviarán a tu email de cuenta.`,
                    'assistant',
                    false,
                    'text-green-600 dark:text-green-400'
                );

                // Reload rules list
                setTimeout(() => {
                    loadRules();
                }, 1000);
            }
        } else {
            // Show error message
            addChatMessage(
                `❌ Error: ${result.error}\n\n` +
                `Por favor, intenta reformular tu solicitud o crea la regla manualmente.`,
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

        addChatMessage(
            `❌ Error de conexión. Por favor, intenta de nuevo más tarde.`,
            'assistant',
            false,
            'text-red-600 dark:text-red-400'
        );
    }
}

function addChatMessage(message, sender, isLoading = false, textColor = '') {
    const chatMessages = document.getElementById('chatMessages');
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
                <img src="images/agent.png" alt="Asistente AI" class="w-full h-full object-cover">
            </div>
            <div class="flex-1 bg-gray-100 dark:bg-gray-700 rounded-lg p-3">
                <p class="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap ${textColor}">${escapeHtml(message)}</p>
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

function getTypeLabel(type) {
    const typeLabels = {
        'price_below': 'Precio debajo',
        'price_above': 'Precio encima',
        'pe_below': 'P/E debajo',
        'pe_above': 'P/E encima',
        'max_distance': 'Distancia del máximo'
    };
    return typeLabels[type] || type;
}

// Make sendChatMessage available globally
window.sendChatMessage = sendChatMessage;
