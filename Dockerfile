FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .

EXPOSE 3141
CMD ["codetrap-agent", "serve", "--host", "0.0.0.0", "--port", "3141", "--data-dir", "/data"]
