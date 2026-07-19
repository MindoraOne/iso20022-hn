FROM python:3.12-slim AS runtime

RUN groupadd -r pain001 && useradd -r -g pain001 pain001

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy templates before switching to non-root user
COPY pain001 /app/pain001
 
RUN mkdir -p /app/tmp && chown -R pain001:pain001 /app/tmp

# Sobreescribe Settings.temp_dir (default tempfile.gettempdir()) para que los
# CSV subidos se escriban dentro de /app, consistente con el directorio creado
# arriba y con los permisos ya asignados al usuario no-root.
ENV TEMP_DIR=/app/tmp

# El puerto real en runtime viene de la variable PORT (default 8000); EXPOSE es
# solo documentacion. El bind es 0.0.0.0 dentro del contenedor (obligatorio).
EXPOSE 8000

USER pain001

CMD ["sh", "-c", "exec uvicorn pain001.api.app_local:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2"]
