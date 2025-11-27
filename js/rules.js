// Rules Page JavaScript

const API_BASE_URL = 'http://localhost:8080/api';

document.addEventListener('DOMContentLoaded', () => {
    loadRules();

    // Modal handlers
    document.getElementById('createRuleBtn').addEventListener('click', () => {
        document.getElementById('ruleModal').style.display = 'flex';
    });

    document.getElementById('closeModal').addEventListener('click', () => {
        document.getElementById('ruleModal').style.display = 'none';
        document.getElementById('ruleForm').reset();
    });

    // Form submission
    document.getElementById('ruleForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        await createRule();
    });
});

async function loadRules() {
    const loadingEl = document.getElementById('rulesLoading');
    const containerEl = document.getElementById('rulesContainer');
    const listEl = document.getElementById('rulesList');
    const emptyEl = document.getElementById('emptyState');

    loadingEl.style.display = 'flex';
    containerEl.style.display = 'none';

    try {
        const response = await fetch(`${API_BASE_URL}/rules`);

        if (!response.ok) {
            throw new Error('Error al cargar reglas');
        }

        const rules = await response.json();

        loadingEl.style.display = 'none';
        containerEl.style.display = 'block';

        if (rules.length === 0) {
            listEl.style.display = 'none';
            emptyEl.style.display = 'block';
        } else {
            listEl.innerHTML = '';
            rules.forEach(rule => {
                const card = createRuleCard(rule);
                listEl.appendChild(card);
            });
            listEl.style.display = 'flex';
            emptyEl.style.display = 'none';
        }

    } catch (error) {
        console.error('Error loading rules:', error);
        loadingEl.innerHTML = `
            <p style="color: #dc3545;">❌ Error al cargar las reglas.</p>
        `;
    }
}

function createRuleCard(rule) {
    const card = document.createElement('div');
    card.className = 'rule-card';

    const typeLabels = {
        'price_below': 'Precio debajo',
        'price_above': 'Precio encima',
        'pe_below': 'P/E debajo',
        'pe_above': 'P/E encima',
        'max_distance': 'Distancia del máximo'
    };

    card.innerHTML = `
        <div class="rule-info">
            <div class="rule-name">${rule.name || 'Regla sin nombre'}</div>
            <div class="rule-details">
                <span class="rule-badge">${typeLabels[rule.type] || rule.type}</span>
                <span class="rule-detail">📊 ${rule.ticker}</span>
                <span class="rule-detail">🎯 ${rule.value}</span>
                <span class="rule-detail">📧 ${rule.email}</span>
            </div>
        </div>
        <div class="rule-actions">
            <button class="btn-icon delete" onclick="deleteRule(${rule.id})" title="Eliminar">
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
        type: document.getElementById('ruleType').value,
        ticker: document.getElementById('ruleTicker').value.toUpperCase(),
        value: parseFloat(document.getElementById('ruleValue').value),
        email: document.getElementById('ruleEmail').value
    };

    try {
        const response = await fetch(`${API_BASE_URL}/rules`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        if (!response.ok) {
            throw new Error('Error al crear regla');
        }

        document.getElementById('closeModal').click();
        loadRules();

    } catch (error) {
        console.error('Error creating rule:', error);
        alert('Error al crear la regla. Por favor, intenta de nuevo.');
    }
}

async function deleteRule(ruleId) {
    if (!confirm('¿Estás seguro de que quieres eliminar esta regla?')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/rules/${ruleId}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            throw new Error('Error al eliminar regla');
        }

        loadRules();

    } catch (error) {
        console.error('Error deleting rule:', error);
        alert('Error al eliminar la regla.');
    }
}
