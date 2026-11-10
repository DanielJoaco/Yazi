# Yazy Turing Machine

Aplicacion web local para calcular los puntajes de Yazy usando una Maquina de Turing Multicinta.

## Requisitos

- Python 3 instalado.
- Navegador web moderno.
- Terminal con `fish` o una shell compatible.

## Preparar el entorno

Abre una terminal ubicada en la raiz del proyecto y ejecuta:

```fish
# Crear el entorno virtual solo si todavia no existe
python3 -m venv .venv

# Instalar las dependencias
./.venv/bin/pip install -r requirements.txt
```

Si el entorno `.venv` ya existe, no es necesario crearlo nuevamente.

## Levantar el backend

Abre una terminal y ejecuta:

```fish
./.venv/bin/uvicorn api.index:app --reload --host 127.0.0.1 --port 8000
```

La API quedara disponible en:

- API: http://127.0.0.1:8000
- Documentacion interactiva: http://127.0.0.1:8000/docs
- Comprobacion de salud: http://127.0.0.1:8000/api/health

La comprobacion de salud debe responder:

```json
{"status":"ok"}
```

Mantén esta terminal abierta.

## Levantar el frontend

Abre una segunda terminal y ejecuta:

```fish
python3 -m http.server 5500 --directory frontend
```

Luego abre en el navegador:

http://127.0.0.1:5500

El frontend se conecta automaticamente con la API en `http://127.0.0.1:8000/api`.

## Uso durante el desarrollo

- Mantén abiertas las dos terminales.
- El backend se recarga automaticamente gracias a `--reload`.
- Si modificas archivos del frontend, recarga el navegador con `Ctrl + Shift + R`.
- Para detener cualquiera de los servidores, presiona `Ctrl + C` en su terminal.

## Solucion de problemas

### La API no responde

Comprueba que el backend este ejecutandose y visita:

http://127.0.0.1:8000/api/health

### El frontend no carga

Comprueba que el servidor del frontend este ejecutandose en el puerto `5500` y abre:

http://127.0.0.1:5500

### El puerto ya esta ocupado

Cierra el proceso que usa el puerto o cambia el puerto del servidor correspondiente. Si cambias el puerto del backend, actualiza tambien `frontend/js/api.js`.
