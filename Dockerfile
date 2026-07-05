FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p /app/data/reports /app/data/uploads

EXPOSE 3141

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3141"]
