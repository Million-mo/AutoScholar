# 快速开始指南

## 5分钟快速上手

### 前提条件

确保已安装：
- Python 3.10+
- PostgreSQL 13+

### 步骤 1：环境准备

```bash
# 克隆项目
cd /path/to/project

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 步骤 2：配置

```bash
# 复制环境变量模板
cp .env.example .env
```

**编辑 `.env` 文件，配置以下内容：**

```env
# 数据库（必须）
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=autoscholar
DATABASE_USER=your_username
DATABASE_PASSWORD=your_password

# LLM API（至少配置一个）
OPENAI_API_KEY=sk-xxxxx
# 或
QWEN_API_KEY=sk-xxxxx

# API 密钥（可选，用于保护接口）
API_KEY=your_secret_key
```

### 步骤 3：初始化数据库

```bash
# 创建数据库
createdb autoscholar

# 或使用 psql
psql -U postgres -c "CREATE DATABASE autoscholar;"
```

### 步骤 4：启动服务

```bash
python run.py
```

看到以下输出表示启动成功：
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### 步骤 5：测试

**方式 1：访问 API 文档**
打开浏览器：http://localhost:8000/docs

**方式 2：使用 curl**

```bash
# 健康检查
curl http://localhost:8000/health

# 爬取论文
curl -X POST "http://localhost:8000/api/v1/tasks/crawl" \
  -H "X-API-Key: your_secret_key" \
  -H "Content-Type: application/json" \
  -d '{"source": "huggingface", "limit": 5}'

# 生成报告
curl -X POST "http://localhost:8000/api/v1/tasks/generate" \
  -H "X-API-Key: your_secret_key" \
  -H "Content-Type: application/json" \
  -d '{"llm_provider": "openai"}'
```

**方式 3：使用示例脚本**

```bash
# 编辑脚本中的 API_KEY
vim scripts/example_usage.sh

# 运行示例
./scripts/example_usage.sh
```

## 常用命令

### 查看论文

```bash
# 列出所有论文
curl "http://localhost:8000/api/v1/papers?limit=10"

# 查看特定论文
curl "http://localhost:8000/api/v1/papers/arxiv-2401.12345"
```

### 查看报告

```bash
# 列出所有报告
curl "http://localhost:8000/api/v1/reports?limit=10"

# 查看某篇论文的报告
curl "http://localhost:8000/api/v1/papers/arxiv-2401.12345/reports"
```

### 查看任务

```bash
# 列出任务
curl "http://localhost:8000/api/v1/tasks?limit=10"

# 查看特定任务
curl "http://localhost:8000/api/v1/tasks/1"
```

## 生成的报告位置

报告保存在：`data/reports/YYYY/MM/` 目录下

例如：
```
data/reports/2025/01/20250118_arxiv_2401.12345_multimodal.md
```

## 下一步

- 📖 阅读完整文档：[README.md](README.md)
- 🚀 部署到生产环境：[DEPLOYMENT.md](DEPLOYMENT.md)
- 📊 查看项目总结：[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)
- 🔧 自定义配置：查看 `.env.example` 中的所有选项

## 故障排查

### 数据库连接失败

```bash
# 检查 PostgreSQL 是否运行
psql -U postgres -c "SELECT 1;"

# 检查数据库是否存在
psql -U postgres -l | grep autoscholar
```

### API 启动失败

```bash
# 检查端口占用
lsof -i :8000

# 查看详细错误
cat data/logs/error.log
```

### LLM 调用失败

```bash
# 检查 API 密钥配置
cat .env | grep API_KEY

# 查看错误日志
tail -f data/logs/error.log
```

## 获取帮助

- 查看 API 文档：http://localhost:8000/docs
- 查看日志：`data/logs/app.log` 和 `data/logs/error.log`
- 提交 Issue：GitHub Issues

---

**祝使用愉快！** 🎉
