FROM python:3.12-slim
 
RUN groupadd -r pain001 && useradd -r -g pain001 pain001
 
WORKDIR /app
 
COPY requirements.dev.txt ./
RUN pip install --no-cache-dir -r requirements.dev.txt

# Copy templates before switching to non-root user
COPY pain001 /app/pain001
 
RUN mkdir -p /app/tmp && chown -R pain001:pain001 /app/tmp
 
EXPOSE 8000
 
USER pain001
 
CMD ["uvicorn", "pain001.api.app_local:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "2"]
 