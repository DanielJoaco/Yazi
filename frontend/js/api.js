const API_BASE = window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost' 
    ? 'http://127.0.0.1:8000/api' 
    : '/api';

export async function evaluateRoll(dice, blockedCategories) {
    try {
        const response = await fetch(`${API_BASE}/evaluate-roll`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                dice: dice,
                blocked_categories: blockedCategories
            })
        });

        if (!response.ok) {
            const errorBody = await response.json().catch(() => null);
            throw new Error(errorBody?.detail || 'Error al conectar con la API del autómata');
        }
        return await response.json();
    } catch (error) {
        console.error("API Error:", error);
        return null;
    }
}