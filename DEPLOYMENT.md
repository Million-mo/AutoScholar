# 部署指南

## 快速部署（开发环境）

### 前置要求
- Python 3.10+
- PostgreSQL 13+

### 步骤

1. **安装依赖**
```bash
pip install -r requirements.txt
```

2. **配置环境**
```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库和 LLM API 密钥
```

3. **初始化数据库**
```bash
createdb autoscholar
```

4. **启动服务**
```bash
python run.py
```

## 生产环境部署

### Docker 部署（推荐）

创建 `Dockerfile`:
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
COPY run.py .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

使用 docker-compose:
```bash
docker-compose up -d
```

### 监控和维护

- 日志位置: `data/logs/`
- 数据库备份: 使用 pg_dump
- 监控指标: API 响应时间、任务成功率、磁盘空间

详细部署说明请参考 README.md
