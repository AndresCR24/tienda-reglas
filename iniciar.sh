#!/usr/bin/env bash
# Levanta el servidor y abre la aplicacion en el navegador.
set -e
cd "$(dirname "$0")"

if [ ! -d .venv ]; then
  echo "Creando entorno virtual..."
  python3 -m venv .venv
  ./.venv/bin/pip install -q --upgrade pip
  ./.venv/bin/pip install -q -r requirements.txt
fi

PUERTO="${1:-8000}"
URL="http://127.0.0.1:$PUERTO"

# Abre el navegador cuando el servidor ya este respondiendo.
(
  for _ in $(seq 1 60); do
    if curl -sf "$URL/api/tienda" > /dev/null 2>&1; then
      command -v open > /dev/null && open "$URL" || echo "Abra $URL en su navegador"
      exit 0
    fi
    sleep 0.5
  done
) &

echo "Servidor en $URL  (Ctrl+C para detener)"
exec ./.venv/bin/python -m uvicorn backend.api.main:app --port "$PUERTO" --reload
