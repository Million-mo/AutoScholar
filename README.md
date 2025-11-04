# AutoScholar - 论文分析报告生成系统

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

AI 驱动的学术论文自动化分析工具，能够从 Hugging Face Daily Papers 等来源爬取最新论文，利用大语言模型（LLM）生成高质量的中文分析报告，并输出为 Markdown 格式文档。

## ✨ 核心功能

- 📰 **自动爬取论文**：从 Hugging Face Daily Papers 获取最新学术论文
- 🤖 **AI 智能分析**：支持多种 LLM（OpenAI、通义千问、智谱 AI、Kimi）生成专业分析报告
- 📝 **Markdown 输出**：自动生成结构化、易读的 Markdown 格式报告
- ⏰ **定时任务**：支持定时爬取和批量生成（当前版本需手动触发）
- 🔄 **手动触发**：通过 REST API 灵活控制任务执行
- 💾 **数据持久化**：PostgreSQL 存储论文和报告数据
- 🔌 **可扩展架构**：模块化设计，易于扩展论文源和发布平台

## 🏗️ 系统架构

```
┌─────────────────┐
│   API Layer     │  FastAPI REST API
├─────────────────┤
│  Orchestrator   │  业务编排层
├─────────────────┤
│ Service Layer   │  爬虫、LLM、文档生成
├─────────────────┤
│   Data Layer    │  PostgreSQL + 文件系统
└─────────────────┘
```

## 📋 系统要求

- Python 3.10+
- PostgreSQL 13+
- 至少 4GB RAM
- 50GB+ 磁盘空间

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone <repository-url>
cd article-analysis-report-generation-1762172961
```

### 2. 安装依赖

```bash
# 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，配置必要的参数
# 重点配置：
# - DATABASE_* : 数据库连接信息
# - OPENAI_API_KEY / QWEN_API_KEY 等：LLM API 密钥
# - API_KEY: API 访问密钥（可选）
```

### 4. 初始化数据库

```bash
# 确保 PostgreSQL 已启动
# 创建数据库
createdb autoscholar

# 数据库迁移（表结构会自动创建）
```

### 5. 启动服务

```bash
# 开发模式
python run.py

# 或使用 uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. 访问 API 文档

打开浏览器访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 📖 使用指南

### API 使用示例

#### 1. 爬取论文

```bash
curl -X POST "http://localhost:8000/api/v1/tasks/crawl" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "huggingface",
    "limit": 10
  }'
```

#### 2. 批量生成报告

```bash
curl -X POST "http://localhost:8000/api/v1/tasks/generate" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "llm_provider": "openai"
  }'
```

#### 3. 为特定论文生成报告

```bash
curl -X POST "http://localhost:8000/api/v1/tasks/generate" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "paper_id": "arxiv-2401.12345",
    "llm_provider": "qwen",
    "force_regenerate": false
  }'
```

#### 4. 查看论文列表

```bash
curl "http://localhost:8000/api/v1/papers?limit=10&source=HUGGINGFACE"
```

#### 5. 查看报告列表

```bash
curl "http://localhost:8000/api/v1/reports?limit=10"
```

#### 6. 查看任务执行状态

```bash
curl "http://localhost:8000/api/v1/tasks/1"
```

### 生成的报告结构

生成的 Markdown 报告包含以下部分：

1. **核心观点总结** - 论文最重要的贡献
2. **研究背景** - 问题和研究动机
3. **技术创新点** - 新方法、新技术
4. **实验与结果** - 关键实验和结果
5. **应用价值** - 实际应用场景
6. **局限性分析** - 不足和改进方向
7. **推荐阅读人群** - 适合的读者群体

报告文件保存在：`data/reports/YYYY/MM/` 目录下

## ⚙️ 配置说明

### LLM 提供商配置

系统支持多种 LLM 提供商：

| 提供商 | 环境变量前缀 | 说明 |
|--------|-------------|------|
| OpenAI | `OPENAI_` | GPT-4 等模型 |
| 通义千问 | `QWEN_` | 阿里云大模型 |
| 智谱 AI | `ZHIPU_` | GLM-4 等模型 |
| Kimi | `KIMI_` | 月之暗面模型 |

配置示例（.env 文件）：

```env
# OpenAI
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.7

# 通义千问
QWEN_API_KEY=sk-xxx
QWEN_MODEL=qwen-max

# 默认和备用提供商
LLM_DEFAULT_PROVIDER=openai
LLM_FALLBACK_PROVIDER=qwen
```

### 数据库配置

```env
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=autoscholar
DATABASE_USER=autoscholar_user
DATABASE_PASSWORD=your_password
```

### 存储配置

```env
STORAGE_REPORTS_PATH=./data/reports
STORAGE_TEMP_PATH=./data/temp
STORAGE_LOG_PATH=./data/logs
```

## 📁 项目结构

```
.
├── app/
│   ├── api/               # API 路由
│   │   └── routes.py
│   ├── core/              # 核心配置
│   │   ├── config.py      # 配置管理
│   │   ├── database.py    # 数据库连接
│   │   └── logging.py     # 日志配置
│   ├── models/            # 数据模型
│   │   ├── paper.py       # 论文模型
│   │   ├── report.py      # 报告模型
│   │   └── task.py        # 任务模型
│   ├── schemas/           # Pydantic 模式
│   │   └── schemas.py
│   ├── services/          # 业务服务
│   │   ├── crawler.py     # 爬虫服务
│   │   ├── llm_service.py # LLM 服务
│   │   ├── document_generator.py  # 文档生成
│   │   └── orchestrator.py        # 业务编排
│   ├── utils/             # 工具函数
│   └── main.py            # 应用入口
├── data/                  # 数据目录
│   ├── reports/           # 生成的报告
│   ├── temp/              # 临时文件
│   └── logs/              # 日志文件
├── tests/                 # 测试
├── requirements.txt       # 依赖列表
├── .env.example           # 环境变量模板
├── pyproject.toml         # 项目配置
└── README.md              # 本文件
```

## 🔧 开发指南

### 运行测试

```bash
pytest tests/ -v --cov=app
```

### 代码格式化

```bash
black app/
flake8 app/
```

### 类型检查

```bash
mypy app/
```

## 🛣️ 路线图

### 已完成

- ✅ 核心功能开发
  - ✅ Hugging Face 爬虫
  - ✅ 多 LLM 集成
  - ✅ Markdown 报告生成
  - ✅ REST API 接口
  - ✅ 数据持久化

### 计划中

- ⏳ 定时任务调度（APScheduler 集成）
- ⏳ 更多论文源（arXiv API、Google Scholar）
- ⏳ 多平台发布
  - 微信公众号
  - 小红书
  - 知乎
  - Medium
- ⏳ Web 管理后台
- ⏳ 报告模板自定义
- ⏳ 多语言支持（中英文双语）

## ❓ 常见问题

### Q: 如何切换 LLM 提供商？

A: 可以在 `.env` 文件中设置 `LLM_DEFAULT_PROVIDER`，或在 API 请求中指定 `llm_provider` 参数。

### Q: 报告生成失败怎么办？

A: 检查：
1. LLM API 密钥是否正确
2. API 额度是否充足
3. 网络连接是否正常
4. 查看日志文件：`data/logs/error.log`

### Q: 如何备份数据？

A: 定期备份：
1. PostgreSQL 数据库（使用 `pg_dump`）
2. `data/reports/` 目录

### Q: 支持本地部署的开源模型吗？

A: 当前版本使用云端 API，后续版本将支持本地模型（如 LLaMA、ChatGLM 等）。

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📧 联系方式

如有问题或建议，请提交 Issue 或联系项目维护者。

---

**注意**：本项目仅供学术研究和学习使用，请遵守相关网站的 robots.txt 和使用条款。
