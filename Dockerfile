FROM python:3.11-slim

WORKDIR /app

# dependencies for yolo and stuff
RUN apt-get update && \
    apt-get install -y --no-install-recommends libgl1 libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

# other deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 6767 6969

CMD ["python", "service_a.py"]

