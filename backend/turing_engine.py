from collections import Counter
from functools import lru_cache
from itertools import combinations_with_replacement

from automata.base.exceptions import InvalidSymbolError, RejectionException
from automata.tm.mntm import MNTM

# --------------------------------------------------------------------------
# Constantes
# --------------------------------------------------------------------------
BLANK = "."                                # simbolo blanco de las cintas
DIGITS = "123456"                          # caras del dado
LETTERS = "abcdefghijklmnopqrstuvwxyz_"    # solo para aceptar "ones,threes" tras el '#'

# Orden FIJO de las 11 casillas. La cinta 3 escribe los puntajes en este orden,
# separados por comas, y la funcion _decode_tape3 los lee en este mismo orden.
CATEGORIES = (
	"ones", "twos", "threes", "fours", "fives", "sixes",
	"trio", "poker", "full_house", "straight", "yazy",
)

# Puntajes fijos (reglas del PDF, seccion 4)
FULL_HOUSE_POINTS = 25
STRAIGHT_POINTS = 40
YAZY_POINTS = 50

# Nombres aceptados despues del '#'  ->  nombre canonico de CATEGORIES.
# Si el backend usa otro nombre, basta con agregarlo aqui.
ALIASES = {
	"ones": "ones", "one": "ones", "unos": "ones",
	"twos": "twos", "two": "twos", "dos": "twos",
	"threes": "threes", "three": "threes", "tres": "threes",
	"fours": "fours", "four": "fours", "cuatros": "fours",
	"fives": "fives", "five": "fives", "cincos": "fives",
	"sixes": "sixes", "six": "sixes", "seises": "sixes",
	"trio": "trio", "three_of_a_kind": "trio",
	"poker": "poker", "poquer": "poker", "four_of_a_kind": "poker",
	"full_house": "full_house", "fullhouse": "full_house", "full": "full_house",
	"straight": "straight", "escalera": "straight",
	"yazy": "yazy", "yahtzee": "yazy",
}


def _scores_for_sorted_dice(dice):
	"""
	dice: tupla ordenada de 5 caracteres, p. ej. ('3','3','3','5','6').
	Devuelve la cadena que la cinta 3 debe contener al final:
	los 11 puntajes en el orden de CATEGORIES separados por comas.
	"""
	freq = Counter(dice)
	total = sum(int(d) for d in dice)
	most = max(freq.values())

	scores = [int(face) * freq[face] for face in DIGITS]            # simples
	scores.append(total if most >= 3 else 0)                        # trio
	scores.append(total if most >= 4 else 0)                        # poker
	scores.append(FULL_HOUSE_POINTS if sorted(freq.values()) == [2, 3] else 0)
	scores.append(STRAIGHT_POINTS if dice in (tuple("12345"), tuple("23456")) else 0)
	scores.append(YAZY_POINTS if most == 5 else 0)                  # yazy
	return ",".join(str(s) for s in scores)


def build_yazy_mntm():
	"""Construye y retorna la Maquina de Turing Multicinta (3 cintas)."""
	T = {}  # tabla de transiciones

	def add(state, reads, new_state, *writes_dirs):
		"""Agrega UNA transicion: (estado, lectura de las 3 cintas) -> (nuevo estado, (escribe, mueve) x 3)."""
		T.setdefault(state, {})[reads] = [(new_state, tuple(writes_dirs))]

	N = (BLANK, "N")  # "no escribir nada nuevo" (BLANK en lectura) y quedarse quieto

	# ---- CINTA 1: valida "d,d,d,d,d#" y se TRUNCA al llegar al '#' --------
	for k in range(1, 6):                                   # dado numero k
		for d in DIGITS:
			add(("A", k), (d, BLANK, BLANK), ("B", k), (d, "R"), N, N)
		if k < 5:
			add(("B", k), (",", BLANK, BLANK), ("A", k + 1), (",", "R"), N, N)
		else:
			# Aqui trunca: no avanza mas alla del '#', lo de la derecha nunca se lee
			add(("B", 5), ("#", BLANK, BLANK), ("rew", 0), ("#", "N"), N, N)

	# ---- CINTA 2: copia los dados ORDENADOS (primero los 1, luego 2, ...) --
	# Hace 6 pasadas por la cinta 1; en la pasada f copia solo los dados == f.
	for f in range(1, 7):
		for d in DIGITS:
			w2 = (d, "R") if d == str(f) else N
			add(("scan", f), (d, BLANK, BLANK), ("scan", f), (d, "R"), w2, N)
		add(("scan", f), (",", BLANK, BLANK), ("scan", f), (",", "R"), N, N)
		if f < 6:
			add(("scan", f), ("#", BLANK, BLANK), ("rew", f), ("#", "N"), N, N)
		else:
			add(("scan", f), ("#", BLANK, BLANK), "back2", ("#", "N"), (BLANK, "L"), N)

	# ---- Rebobinar la cinta 1 hasta su inicio entre pasada y pasada --------
	for f in range(0, 6):
		for s in DIGITS + ",#":
			add(("rew", f), (s, BLANK, BLANK), ("rew", f), (s, "L"), N, N)
		add(("rew", f), (BLANK, BLANK, BLANK), ("scan", f + 1), (BLANK, "R"), N, N)

	# ---- Rebobinar la cinta 2 hasta su inicio ------------------------------
	for c in DIGITS:
		add("back2", ("#", c, BLANK), "back2", ("#", "N"), (c, "L"), N)
	add("back2", ("#", BLANK, BLANK), "eval_start", ("#", "N"), (BLANK, "R"), N)

	# ---- CINTA 3: evaluacion de reglas -------------------------------------
	results = set()  # cadenas de puntajes distintas que la maquina puede escribir

	def name(p):
		return "eval_start" if not p else ("e", p)

	def gen(p):
		"""Lee de la cinta 2 los dados ya ordenados (no decrecientes) uno por uno.
		Al completar los 5, la cinta 3 queda lista para escribir los puntajes."""
		if len(p) < 5:
			for c in DIGITS:
				if not p or c >= p[-1]:
					add(name(p), ("#", c, BLANK), name(p + (c,)), ("#", "N"), (c, "R"), N)
					gen(p + (c,))
		else:
			result = _scores_for_sorted_dice(p)
			results.add(result)
			add(name(p), ("#", BLANK, BLANK), ("emit", result), ("#", "N"), N, N)

	gen(())

	# ---- CINTA 3: escritura de la cadena de puntajes -----------------------
	# El estado ("emit", resto) escribe el primer caracter de "resto" y pasa a
	# ("emit", resto[1:]). Estados con el mismo "resto" se comparten entre jugadas.
	for result in results:
		for i in range(len(result)):
			nxt = ("emit", result[i + 1:]) if i + 1 < len(result) else "qf"
			add(("emit", result[i:]), ("#", BLANK, BLANK), nxt, ("#", "N"), N, (result[i], "R"))

	# ---- Conjunto de estados ----------------------------------------------
	states = set(T.keys())
	for trans in T.values():
		for res in trans.values():
			states.add(res[0][0])
	states.add("qf")

	return MNTM(
		states=states,
		input_symbols=set(DIGITS + ",#" + LETTERS),
		tape_symbols=set("0123456789" + ",#" + LETTERS + BLANK),  # 0-9: la cinta 3 escribe puntajes
		n_tapes=3,
		transitions=T,
		initial_state=("A", 1),
		blank_symbol=BLANK,
		final_states={"qf"},
	)


@lru_cache(maxsize=1)
def _get_machine():
	"""La maquina es inmutable: se construye una sola vez y se reutiliza."""
	return build_yazy_mntm()


def _normalize(input_string):
	"""Quita espacios y pasa a minusculas ('3,3,3,5,6#Ones, Threes' -> '3,3,3,5,6#ones,threes')."""
	if not isinstance(input_string, str):
		raise ValueError("La entrada debe ser una cadena de texto.")
	return "".join(input_string.split()).lower()


def _parse_used_cells(used_part):
	"""Convierte 'ones,threes' en {'ones','threes'} usando nombres canonicos."""
	if used_part == "":
		return set()
	used = set()
	for raw in used_part.split(","):
		if raw not in ALIASES:
			raise ValueError(f"Casilla desconocida despues del '#': '{raw}'")
		used.add(ALIASES[raw])
	return used


def _decode_tape3(tape3_text):
	"""'0,0,9,0,5,6,23,0,0,0,0' -> {'ones': 0, ..., 'yazy': 0}"""
	values = tape3_text.split(",")
	if len(values) != len(CATEGORIES):
		raise RuntimeError(f"La cinta 3 tiene un formato inesperado: '{tape3_text}'")
	return {cat: int(v) for cat, v in zip(CATEGORIES, values)}


def calculate_all_scores(input_string, machine=None):
	"""
	Ejecuta la MNTM sobre la cadena completa y retorna el diccionario COMPLETO
	de puntajes (las 11 casillas, sin filtrar). Lanza ValueError si la entrada
	no cumple el formato.
	"""
	text = _normalize(input_string)
	if text.count("#") != 1:
		raise ValueError("La entrada debe contener exactamente un '#'.")
	_parse_used_cells(text.split("#")[1])        # valida los nombres antes de correr

	machine = machine or _get_machine()
	try:
		config = next(iter(machine.read_input(text)))
	except (RejectionException, InvalidSymbolError) as exc:
		raise ValueError(f"Entrada invalida '{input_string}': {exc}") from exc

	tape3 = "".join(config.tapes[2].tape).strip(BLANK)
	return _decode_tape3(tape3)


def _reference_scores(dice):
	"""Implementacion independiente (sin la maquina) para comparar en las pruebas."""
	d = sorted(dice)
	total = sum(d)
	counts = [d.count(v) for v in range(1, 7)]
	out = {name: v * counts[v - 1] for v, name in enumerate(CATEGORIES[:6], start=1)}
	out["trio"] = total if max(counts) >= 3 else 0
	out["poker"] = total if max(counts) >= 4 else 0
	out["full_house"] = 25 if (3 in counts and 2 in counts) else 0
	out["straight"] = 40 if d in ([1, 2, 3, 4, 5], [2, 3, 4, 5, 6]) else 0
	out["yazy"] = 50 if max(counts) == 5 else 0
	return out


def calculate_available_scores(input_string, scores=None, machine=None):
	"""
	1. Toma el diccionario completo de puntajes (si no se pasa en `scores`,
	   lo calcula ejecutando la MNTM).
	2. Lee la subcadena despues del '#' (casillas inhabilitadas).
	3. Elimina esas casillas del diccionario.
	4. Retorna el diccionario limpio {casilla: puntaje}.

	Las casillas disponibles que no logran combinacion quedan con 0
	(el jugador todavia puede tacharlas).
	"""
	text = _normalize(input_string)
	if text.count("#") != 1:
		raise ValueError("La entrada debe contener exactamente un '#'.")
	used = _parse_used_cells(text.split("#")[1])

	if scores is None:
		scores = calculate_all_scores(text, machine)

	return {cat: pts for cat, pts in scores.items() if cat not in used}
