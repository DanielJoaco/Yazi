"""
API REST que recibe los dados y las casillas bloqueadas, e invoca al autómata formal.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Optional

# Importación desde el módulo backend
from automata.tm.mntm import MNTM
from backend.turing_engine import build_yazy_mntm, calculate_available_scores

app = FastAPI(
    title="Yazy Turing Evaluator API",
    description="API que evalúa tiradas de Yazy utilizando una MNTM",
    version="1.0.0"
)

# Configuración de CORS para permitir la comunicación con el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instancia global del autómata MNTM de automata-lib
MNTM_ENGINE: MNTM = build_yazy_mntm()


# ==========================================
# ESTRUCTURAS DE ENTRADA Y SALIDA
# ==========================================

class EvaluateRollRequest(BaseModel):
    """Estructura de los datos que envía el frontend."""
    dice: List[int] = Field(..., min_items=5, max_items=5, description="Lista con los 5 dados (1 al 6)")
    blocked_categories: Optional[List[str]] = Field(default=[], description="Casillas jugadas que se omiten del cálculo")

class EvaluateRollResponse(BaseModel):
    """Estructura de la respuesta que devuelve la API."""
    success: bool
    scores: Dict[str, int]


# ==========================================
# ENDPOINTS REST
# ==========================================

@app.get("/api/health")
def health_check():
    """
    Endpoint de comprobación de salud. 
    Usado por los servidores para confirmar que la aplicación está activa.
    """
    return {"status": "ok"}


@app.post("/api/evaluate-roll", response_model=EvaluateRollResponse)
def evaluate_roll(payload: EvaluateRollRequest):
    """
    Recibe los dados y casillas bloqueadas, y retorna el diccionario de puntajes calculados.
    """
    # 1. Validación para asegurar que los dados tengan valores válidos (1 a 6)
    if any(d < 1 or d > 6 for d in payload.dice):
        raise HTTPException(status_code=400, detail="Los dados deben estar comprendidos entre 1 y 6.")

    # 2. Formatear la cadena de entrada y verificar aceptación formal en la MNTM
    dice_str = ",".join(map(str, payload.dice)) + "#"
    is_accepted = MNTM_ENGINE.accepts_input(dice_str) if MNTM_ENGINE.validate() else True

    # 3. Calcular los puntajes únicamente para las casillas libres
    scores = calculate_available_scores(payload.dice, payload.blocked_categories)

    # 4. Retornar la respuesta con el éxito del autómata y los puntajes
    return EvaluateRollResponse(
        success=is_accepted,
        scores=scores
    )