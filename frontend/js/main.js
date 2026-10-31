import { evaluateRoll } from './api.js';
import * as ui from './ui.js';

// Estado de la partida en el cliente
const gameState = {
    turn: 'p1',
    rollsLeft: 3,
    dice: [1, 1, 1, 1, 1],
    lockedMask: [false, false, false, false, false],
    blockedCategories: { p1: [], p2: [] },
    currentEvaluations: {}
};

// Referencias del DOM
const btnRoll = document.getElementById('btn-roll');
const btnReset = document.getElementById('btn-reset');

// ==========================================
// INICIALIZACIÓN
// ==========================================
function initGame() {
    ui.updateTurnHeader(gameState.turn, gameState.rollsLeft);
    ui.updateInteractiveCells(gameState.turn);
    
    // Listeners de los dados
    document.querySelectorAll('.die').forEach((dieEl, index) => {
        dieEl.addEventListener('click', () => {
            // Solo permitir bloquear si ya se hizo al menos un lanzamiento
            if (gameState.rollsLeft < 3 && gameState.rollsLeft > 0) {
                gameState.lockedMask[index] = ui.toggleDieSelection(index);
            }
        });
    });

    // Listeners de las celdas de puntuación
    document.querySelectorAll('.score').forEach(cell => {
        cell.addEventListener('click', (e) => handleScoreClick(e.target));
    });

    btnRoll.addEventListener('click', handleRoll);
    btnReset.addEventListener('click', () => location.reload()); // Reinicio rústico rápido
}

// ==========================================
// FLUJO DE LANZAMIENTO
// ==========================================
async function handleRoll() {
    if (gameState.rollsLeft <= 0) return;

    btnRoll.disabled = true;

    // 1. Generar dados aleatorios en el cliente (1 al 6)
    gameState.dice = gameState.dice.map((val, idx) => 
        gameState.lockedMask[idx] ? val : Math.floor(Math.random() * 6) + 1
    );

    gameState.rollsLeft--;
    ui.updateTurnHeader(gameState.turn, gameState.rollsLeft);

    // 2. Animar los dados y procesar con la API al terminar la animación
    ui.animateAndSetDice(gameState.dice, gameState.lockedMask, async () => {
        const currentBlocked = gameState.blockedCategories[gameState.turn];
        
        // Llamada a la API Stateless
        const result = await evaluateRoll(gameState.dice, currentBlocked);
        
        if (result && result.success) {
            gameState.currentEvaluations = result.scores;
            ui.renderScorePreviews(result.scores, gameState.turn);
        }
        
        btnRoll.disabled = gameState.rollsLeft === 0;
    });
}

// ==========================================
// FIJACIÓN DE PUNTAJE Y CAMBIO DE TURNO
// ==========================================
function handleScoreClick(cellElement) {
    // Ignorar si no es el turno, la celda ya se usó, o no se ha lanzado el dado aún
    if (!cellElement.classList.contains('active-turn') || gameState.rollsLeft === 3) return;

    // Extraer categoría del TR padre (ej: data-category="threes")
    const category = cellElement.parentElement.getAttribute('data-category');
    const finalScore = gameState.currentEvaluations[category] || 0;

    // 1. Bloquear celda
    ui.lockScoreCell(category, gameState.turn, finalScore);
    gameState.blockedCategories[gameState.turn].push(category);

    // 2. Calcular totales (Lógica básica en cliente)
    updateTotals(gameState.turn, finalScore);

    // 3. Cambiar de turno
    gameState.turn = gameState.turn === 'p1' ? 'p2' : 'p1';
    gameState.rollsLeft = 3;
    gameState.lockedMask = [false, false, false, false, false];
    gameState.currentEvaluations = {};

    // 4. Reset visual
    ui.resetDiceVisuals();
    ui.clearPreviews();
    ui.updateTurnHeader(gameState.turn, gameState.rollsLeft);
    ui.updateInteractiveCells(gameState.turn);
    btnRoll.disabled = false;
}

function updateTotals(player, addedScore) {
    const totalEl = document.getElementById(`total-${player}`);
    const currentTotal = parseInt(totalEl.textContent) || 0;
    totalEl.textContent = currentTotal + addedScore;
}

// Iniciar aplicación
document.addEventListener('DOMContentLoaded', initGame);