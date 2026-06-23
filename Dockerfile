FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用
COPY app.py .

# 暴露端口
EXPOSE 7860

# 启动
CMD ["streamlit", "run", "app.py", "--server.port=7860", "--server.address=0.0.0.0"]
