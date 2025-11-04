#!/bin/bash
# AutoScholar API 使用示例脚本

API_BASE="http://localhost:8000/api/v1"
API_KEY="your_api_key"

echo "=== AutoScholar API 使用示例 ==="
echo ""

# 1. 健康检查
echo "1. 健康检查..."
curl -s http://localhost:8000/health | jq .
echo ""

# 2. 爬取论文
echo "2. 爬取 Hugging Face Daily Papers..."
curl -s -X POST "${API_BASE}/tasks/crawl" \
  -H "X-API-Key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "huggingface",
    "limit": 5
  }' | jq .
echo ""

# 等待爬取完成
echo "等待 5 秒..."
sleep 5

# 3. 查看论文列表
echo "3. 查看已爬取的论文..."
curl -s "${API_BASE}/papers?limit=3" | jq '.[] | {paper_id, title, status}'
echo ""

# 4. 批量生成报告
echo "4. 批量生成报告（使用 OpenAI）..."
curl -s -X POST "${API_BASE}/tasks/generate" \
  -H "X-API-Key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "llm_provider": "openai"
  }' | jq .
echo ""

# 5. 查看报告列表
echo "5. 查看生成的报告..."
sleep 3
curl -s "${API_BASE}/reports?limit=3" | jq '.[] | {id, paper_id, llm_model, status}'
echo ""

# 6. 查看任务执行历史
echo "6. 查看任务执行历史..."
curl -s "${API_BASE}/tasks?limit=5" | jq '.[] | {id, task_type, status, created_at}'
echo ""

echo "=== 使用示例完成 ==="
echo ""
echo "提示："
echo "- 修改 API_KEY 变量为你的实际 API 密钥"
echo "- 确保服务已启动: python run.py"
echo "- 配置了有效的 LLM API 密钥"
echo "- 安装了 jq 用于格式化 JSON 输出: brew install jq"
