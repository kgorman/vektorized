# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --upgrade pip

COPY . .

EXPOSE 5100
CMD ["flask", "run", "--host=0.0.0.0", "--port=5100"]