FROM python:3.11-slim

RUN apt-get update && apt-get install -y libgomp1 && rm -rf /var/lib/apt/lists/*

# Copy uv binary từ image chính thức của uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Thư mục làm việc trong container
WORKDIR /app

# Copy file dependency trước để tận dụng cache Docker
COPY pyproject.toml uv.lock ./

# API chỉ cần nhóm serve, không kéo tool train/notebook/demo vào image.
RUN uv sync --frozen --no-default-groups --group serve --no-install-project --no-cache

# Copy source code sau
COPY . .

# Expose cổng FastAPI
EXPOSE 8000

# Chạy app
CMD ["/app/.venv/bin/uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

