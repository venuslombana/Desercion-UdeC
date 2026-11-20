FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY data ./data
COPY seed.py export_ddl.py docker-entrypoint.sh ./
RUN sed -i "s/\r$//" docker-entrypoint.sh
RUN useradd --create-home --uid 1000 appuser && chown -R appuser /app
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s --retries=5 CMD python -c "import os, urllib.request; urllib.request.urlopen('http://localhost:%s/api/health' % os.getenv('PORT', '8000'))"
ENTRYPOINT ["sh", "./docker-entrypoint.sh"]
