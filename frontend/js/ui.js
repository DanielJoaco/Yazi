export function updateTurnHeader(player, rollsLeft) {
    document.getElementById('current-turn').textContent = player === 'p1' ? 'Jugador 1' : 'Jugador 2 / Bot';
    document.getElementById('rolls-left').textContent = rollsLeft;
}

export function animateAndSetDice(diceValues, lockedMask, callback) {
    const diceElements = document.querySelectorAll('.die');
    
    // Iniciar animación solo en los dados no bloqueados
    diceElements.forEach((el, index) => {
        if (!lockedMask[index]) {
            el.classList.add('rolling');
            // Cambiar valores rápidamente para efecto visual
            el.textContent = '🎲'; 
        }
    });

    // Esperar a que termine la animación (400ms definido en CSS)
    setTimeout(() => {
        diceElements.forEach((el, index) => {
            el.classList.remove('rolling');
            el.textContent = diceValues[index];
        });
        if (callback) callback();
    }, 400);
}

export function toggleDieSelection(index) {
    const dieEl = document.getElementById(`die-${index}`);
    dieEl.classList.toggle('locked');
    return dieEl.classList.contains('locked');
}

export function resetDiceVisuals() {
    document.querySelectorAll('.die').forEach(el => {
        el.classList.remove('locked');
        el.textContent = '?';
    });
}

export function clearPreviews() {
    document.querySelectorAll('.score.preview').forEach(el => {
        if (!el.classList.contains('used')) {
            el.textContent = '-';
            el.classList.remove('preview');
        }
    });
}

export function renderScorePreviews(scores, currentPlayer) {
    clearPreviews();
    for (const [category, value] of Object.entries(scores)) {
        // Ahora buscamos el botón con el id correspondiente
        const btn = document.getElementById(`score-${category}-${currentPlayer}`);
        if (btn && !btn.classList.contains('used')) {
            btn.textContent = value;
            btn.classList.add('preview');
        }
    }
}

export function updateInteractiveCells(currentPlayer) {
    // Quitar interactividad de todos los botones de score
    document.querySelectorAll('.score').forEach(el => el.classList.remove('active-turn'));
    
    // Habilitar solo los botones del jugador actual que no estén usados
    document.querySelectorAll(`.score.${currentPlayer}-score`).forEach(el => {
        if (!el.classList.contains('used')) {
            el.classList.add('active-turn');
        }
    });
}

export function lockScoreCell(category, player, finalScore) {
    const btn = document.getElementById(`score-${category}-${player}`);
    btn.textContent = finalScore;
    btn.classList.remove('preview', 'active-turn');
    btn.classList.add('used');
}