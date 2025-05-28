# ---------- Base image ----------
FROM python:3.12-slim

# ---------- OS dependencies (kompilatory, nagłówki) ----------
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

# ---------- Workdir ----------
WORKDIR /app

# ---------- Python deps ----------
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ---------- Project files ----------
COPY . .

# ---------- Port & launch ----------
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]