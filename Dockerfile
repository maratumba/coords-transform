FROM python:3.12-slim
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y proj-bin

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY . /app
WORKDIR /app
RUN uv sync --frozen --no-cache

CMD ["/app/.venv/bin/fastapi", "run", "main.py", "--port", "8000", "--host", "0.0.0.0"]
