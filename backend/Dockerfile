FROM python:3.10-slim

WORKDIR /app

# System deps for gymnasium + OpenGL rendering
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY . .

# Create data directory (mounted as volume at runtime)
RUN mkdir -p /app/data

ENV RL_LAB_DATABASE_URL=sqlite+aiosqlite:////app/data/rl_lab.db
ENV RL_LAB_MLFLOW_TRACKING_URI=sqlite:////app/data/mlflow.db
ENV RL_LAB_DATA_DIR=/app/data

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
