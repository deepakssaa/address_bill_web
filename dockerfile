FROM python:3.13-slim

# ---------- SYSTEM DEPENDENCIES FOR WEASYPRINT ----------
RUN apt-get update && apt-get install -y \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    shared-mime-info \
    fonts-noto-core \
    fonts-noto-extra \
    && rm -rf /var/lib/apt/lists/*

# ---------- WORKDIR ----------
WORKDIR /app

# ---------- COPY FILES ----------
COPY . .

# ---------- PYTHON DEPENDENCIES ----------
RUN pip install --no-cache-dir -r requirements.txt

# ---------- RENDER PORT ----------
ENV PORT=10000

# ---------- START SERVER ----------
CMD ["gunicorn", "-b", "0.0.0.0:10000", "app:app"]
