FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.8.22 /uv /uvx /bin/

COPY . /app
WORKDIR /app

RUN uv sync --frozen --no-cache

EXPOSE 8000
CMD ["/app/.venv/bin/fastapi", "run", "app/main.py", "--port", "80", "--host", "0.0.0.0"]
