// Reset Password Page JavaScript
// const getApiBaseUrl = () => window.API_BASE_URL || 'http://localhost:8080'; // Development
const getApiBaseUrl = () => window.API_BASE_URL || 'https://api.bullanalytics.io'; // Production
const AUTH_API_BASE_URL = `${getApiBaseUrl()}/auth`;

document.addEventListener('DOMContentLoaded', () => {
    // Extraer token_hash de la URL (viene del email de recuperación de Supabase)
    // Supabase envía el token como token_hash en los query parameters
    const urlParams = new URLSearchParams(window.location.search);
    const hashParams = new URLSearchParams(window.location.hash.substring(1));
    
    // Intentar obtener token_hash de los query params (flujo PKCE)
    let token = urlParams.get('token_hash');
    let tokenType = urlParams.get('type');
    
    // Si no está en query params, intentar del hash (flujo implícito)
    if (!token) {
        token = hashParams.get('access_token') || hashParams.get('token') || urlParams.get('token');
    }
    
    if (!token) {
        showMessage('Token de recuperación no válido o faltante. Por favor, solicita un nuevo enlace.', 'error');
        document.getElementById('resetPasswordForm').classList.add('hidden');
        return;
    }
    
    // Guardar token y tipo para usar en el reset
    window.resetToken = token;
    window.resetTokenType = tokenType || 'recovery';
    
    const resetPasswordBtn = document.getElementById('resetPasswordBtn');
    const resetPassword = document.getElementById('resetPassword');
    const resetConfirmPassword = document.getElementById('resetConfirmPassword');
    
    resetPasswordBtn.addEventListener('click', () => handleResetPassword(token));
    
    // Permitir submit con Enter
    resetPassword.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleResetPassword(token);
    });
    resetConfirmPassword.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleResetPassword(token);
    });
});

async function handleResetPassword(token) {
    const password = document.getElementById('resetPassword').value;
    const confirmPassword = document.getElementById('resetConfirmPassword').value;
    
    if (!password || !confirmPassword) {
        showMessage('Por favor completa todos los campos', 'error');
        return;
    }
    
    if (password.length < 6) {
        showMessage('La contraseña debe tener al menos 6 caracteres', 'error');
        return;
    }
    
    if (password !== confirmPassword) {
        showMessage('Las contraseñas no coinciden', 'error');
        return;
    }
    
    const resetPasswordBtn = document.getElementById('resetPasswordBtn');
    const originalText = resetPasswordBtn.textContent;
    resetPasswordBtn.disabled = true;
    resetPasswordBtn.textContent = 'Restableciendo...';
    
    try {
        const response = await fetch(`${AUTH_API_BASE_URL}/reset-password`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                token: token,
                password: password,
                confirm_password: confirmPassword
            }),
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || data.message || 'Error al restablecer contraseña');
        }
        
        // Mostrar mensaje de éxito
        const resetPasswordForm = document.getElementById('resetPasswordForm');
        const successMessage = document.getElementById('successMessage');
        
        resetPasswordForm.classList.add('hidden');
        successMessage.classList.remove('hidden');
        
    } catch (error) {
        console.error('Error en reset password:', error);
        showMessage(error.message || 'Error al restablecer contraseña. El token puede haber expirado.', 'error');
    } finally {
        resetPasswordBtn.disabled = false;
        resetPasswordBtn.textContent = originalText;
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

