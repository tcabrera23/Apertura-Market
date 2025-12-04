// Forgot Password Page JavaScript
// const getApiBaseUrl = () => window.API_BASE_URL || 'http://localhost:8080'; // Development
const getApiBaseUrl = () => window.API_BASE_URL || 'https://api.bullanalytics.io'; // Production
const AUTH_API_BASE_URL = `${getApiBaseUrl()}/auth`;

document.addEventListener('DOMContentLoaded', () => {
    const forgotPasswordBtn = document.getElementById('forgotPasswordBtn');
    const forgotEmail = document.getElementById('forgotEmail');
    
    forgotPasswordBtn.addEventListener('click', handleForgotPassword);
    
    // Permitir submit con Enter
    forgotEmail.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleForgotPassword();
    });
});

async function handleForgotPassword() {
    const email = document.getElementById('forgotEmail').value.trim();
    
    if (!email) {
        showMessage('Por favor ingresa tu email', 'error');
        return;
    }
    
    // Validar formato de email básico
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        showMessage('Por favor ingresa un email válido', 'error');
        return;
    }
    
    const forgotPasswordBtn = document.getElementById('forgotPasswordBtn');
    const originalText = forgotPasswordBtn.textContent;
    forgotPasswordBtn.disabled = true;
    forgotPasswordBtn.textContent = 'Enviando...';
    
    try {
        const response = await fetch(`${AUTH_API_BASE_URL}/forgot-password`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email }),
        });
        
        const data = await response.json();
        
        // Siempre mostrar mensaje de éxito (por seguridad, no revelar si el email existe)
        const forgotPasswordForm = document.getElementById('forgotPasswordForm');
        const successMessage = document.getElementById('successMessage');
        
        forgotPasswordForm.classList.add('hidden');
        successMessage.classList.remove('hidden');
        
    } catch (error) {
        console.error('Error en forgot password:', error);
        // Aún así mostrar mensaje de éxito (por seguridad)
        const forgotPasswordForm = document.getElementById('forgotPasswordForm');
        const successMessage = document.getElementById('successMessage');
        
        forgotPasswordForm.classList.add('hidden');
        successMessage.classList.remove('hidden');
    } finally {
        forgotPasswordBtn.disabled = false;
        forgotPasswordBtn.textContent = originalText;
    }
}

function showMessage(message, type = 'info') {
    const messageEl = document.getElementById('authMessage');
    messageEl.textContent = message;
    messageEl.classList.remove('hidden', 'bg-red-50', 'text-red-800', 'border-red-200', 
                                'bg-green-50', 'text-green-800', 'border-green-200',
                                'bg-blue-50', 'text-blue-800', 'border-blue-200',
                                'error-message');
    
    if (type === 'error') {
        messageEl.classList.add('bg-red-50', 'dark:bg-red-900/20', 'text-red-800', 'dark:text-red-200', 
                                'border', 'border-red-200', 'dark:border-red-800', 'error-message');
    } else if (type === 'success') {
        messageEl.classList.add('bg-green-50', 'dark:bg-green-900/20', 'text-green-800', 'dark:text-green-200', 
                                'border', 'border-green-200', 'dark:border-green-800');
    } else {
        messageEl.classList.add('bg-blue-50', 'dark:bg-blue-900/20', 'text-blue-800', 'dark:text-blue-200', 
                                'border', 'border-blue-200', 'dark:border-blue-800');
    }
}

