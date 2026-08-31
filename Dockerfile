FROM python:3.11-slim

LABEL maintainer="immichframe-light"
LABEL description="Minimalist digital photo frame for Immich - optimized for legacy iOS devices"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY templates/ templates/

EXPOSE 5000

CMD ["python", "app.py"]
