FROM python:3.11-slim

WORKDIR /app

# Minimal system deps — shapely/pyogrio/pyproj wheels are self-contained
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 7860

CMD ["solara", "run", "app.py", "--host", "0.0.0.0", "--port", "7860", "--no-open"]
