// Login Page JavaScript
// Conecta con app_supabase.py (puerto 8080)

const AUTH_API_BASE_URL = 'http://localhost:8080/auth';

// Estado de autenticación
let currentMode = 'signin'; // 'signin' o 'signup'
let accessToken = null;

document.addEventListener('DOMContentLoaded', () => {
    initializeTabs();
    initializeForms();
    checkAuthStatus();
    
    // Set max date for date picker (must be 13+ years old)
    const dateInput = document.getElementById('signUpDateOfBirth');
    if (dateInput) {
        const maxDate = new Date();
        maxDate.setFullYear(maxDate.getFullYear() - 13);
        dateInput.max = maxDate.toISOString().split('T')[0];
    }
});

// Inicializar tabs
function initializeTabs() {
    const signInTab = document.getElementById('signInTab');
    const signUpTab = document.getElementById('signUpTab');
    const signInForm = document.getElementById('signInForm');
    const signUpForm = document.getElementById('signUpForm');

    signInTab.addEventListener('click', () => {
        currentMode = 'signin';
        signInTab.classList.add('text-green-500', 'border-green-500');
        signInTab.classList.remove('text-gray-500', 'dark:text-gray-400');
        signUpTab.classList.remove('text-green-500', 'border-green-500');
        signUpTab.classList.add('text-gray-500', 'dark:text-gray-400');
        signInForm.classList.remove('hidden');
        signUpForm.classList.add('hidden');
        clearMessage();
    });

    signUpTab.addEventListener('click', () => {
        currentMode = 'signup';
        signUpTab.classList.add('text-green-500', 'border-green-500');
        signUpTab.classList.remove('text-gray-500', 'dark:text-gray-400');
        signInTab.classList.remove('text-green-500', 'border-green-500');
        signInTab.classList.add('text-gray-500', 'dark:text-gray-400');
        signUpForm.classList.remove('hidden');
        signInForm.classList.add('hidden');
        clearMessage();
    });
}

// Inicializar formularios
function initializeForms() {
    const signInBtn = document.getElementById('signInBtn');
    const signUpBtn = document.getElementById('signUpBtn');

    signInBtn.addEventListener('click', handleSignIn);
    signUpBtn.addEventListener('click', handleSignUp);

    // Permitir submit con Enter
    document.getElementById('signInEmail').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleSignIn();
    });
    document.getElementById('signInPassword').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleSignIn();
    });
    document.getElementById('signUpEmail').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleSignUp();
    });
    document.getElementById('signUpPassword').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleSignUp();
    });
    document.getElementById('signUpConfirmPassword').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleSignUp();
    });
}

// Manejar Sign In
async function handleSignIn() {
    const email = document.getElementById('signInEmail').value.trim();
    const password = document.getElementById('signInPassword').value;

    if (!email || !password) {
        showMessage('Por favor completa todos los campos', 'error');
        return;
    }

    const signInBtn = document.getElementById('signInBtn');
    const originalText = signInBtn.textContent;
    signInBtn.disabled = true;
    signInBtn.textContent = 'Iniciando sesión...';

    try {
        const response = await fetch(`${AUTH_API_BASE_URL}/signin`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email, password }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || data.message || 'Error al iniciar sesión');
        }

        // Guardar token y datos del usuario
        accessToken = data.access_token;
        localStorage.setItem('access_token', accessToken);
        localStorage.setItem('user_data', JSON.stringify(data.user));

        showMessage('¡Bienvenido! Redirigiendo...', 'success');
        
        // Redirigir a la URL guardada o al dashboard
        const redirectUrl = localStorage.getItem('redirect_after_login') || 'dashboard.html';
        localStorage.removeItem('redirect_after_login');
        
        setTimeout(() => {
            window.location.href = redirectUrl;
        }, 1000);

    } catch (error) {
        console.error('Error en sign in:', error);
        showMessage(error.message || 'Error al iniciar sesión. Verifica tus credenciales.', 'error');
    } finally {
        signInBtn.disabled = false;
        signInBtn.textContent = originalText;
    }
}

// Manejar Sign Up
async function handleSignUp() {
    const email = document.getElementById('signUpEmail').value.trim();
    const password = document.getElementById('signUpPassword').value;
    const confirmPassword = document.getElementById('signUpConfirmPassword').value;
    const country = document.getElementById('signUpCountry').value;
    const dateOfBirth = document.getElementById('signUpDateOfBirth').value;

    // Validaciones
    if (!email || !password || !confirmPassword || !country || !dateOfBirth) {
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

    // Validar fecha de nacimiento (debe ser mayor de 13 años)
    const birthDate = new Date(dateOfBirth);
    const today = new Date();
    const age = (today - birthDate) / (1000 * 60 * 60 * 24 * 365.25);
    
    if (age < 13) {
        showMessage('Debes ser mayor de 13 años para registrarte', 'error');
        return;
    }

    const signUpBtn = document.getElementById('signUpBtn');
    const originalText = signUpBtn.textContent;
    signUpBtn.disabled = true;
    signUpBtn.textContent = 'Creando cuenta...';

    try {
        const response = await fetch(`${AUTH_API_BASE_URL}/signup`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                email, 
                password, 
                confirm_password: confirmPassword,
                country: country,
                date_of_birth: dateOfBirth
            }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || data.message || 'Error al crear cuenta');
        }

        // Guardar token y datos del usuario
        accessToken = data.access_token;
        localStorage.setItem('access_token', accessToken);
        localStorage.setItem('user_data', JSON.stringify(data.user));

        showMessage('¡Cuenta creada exitosamente! Redirigiendo...', 'success');
        
        // Redirigir a la URL guardada o al dashboard
        const redirectUrl = localStorage.getItem('redirect_after_login') || 'dashboard.html';
        localStorage.removeItem('redirect_after_login');
        
        setTimeout(() => {
            window.location.href = redirectUrl;
        }, 1500);

    } catch (error) {
        console.error('Error en sign up:', error);
        showMessage(error.message || 'Error al crear cuenta. El email puede estar en uso.', 'error');
    } finally {
        signUpBtn.disabled = false;
        signUpBtn.textContent = originalText;
    }
}

// OAuth removed - using traditional email/password registration only

// Verificar estado de autenticación
function checkAuthStatus() {
    const token = localStorage.getItem('access_token');
    if (token) {
        // Si ya hay token, verificar si es válido
        verifyToken(token);
    }
}

// Verificar token
async function verifyToken(token) {
    try {
        const response = await fetch(`${AUTH_API_BASE_URL.replace('/auth', '')}/api/v1/user/me`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
            },
        });

        if (response.ok) {
            // Token válido, redirigir a la URL guardada o al dashboard
            const redirectUrl = localStorage.getItem('redirect_after_login') || 'dashboard.html';
            localStorage.removeItem('redirect_after_login');
            window.location.href = redirectUrl;
        } else {
            // Token inválido, limpiar
            localStorage.removeItem('access_token');
            localStorage.removeItem('user_data');
        }
    } catch (error) {
        console.error('Error verificando token:', error);
        localStorage.removeItem('access_token');
        localStorage.removeItem('user_data');
    }
}

// Mostrar mensaje
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

// Limpiar mensaje
function clearMessage() {
    const messageEl = document.getElementById('authMessage');
    messageEl.classList.add('hidden');
    messageEl.textContent = '';
}

// Exportar funciones para uso global
window.handleSignIn = handleSignIn;
window.handleSignUp = handleSignUp;

