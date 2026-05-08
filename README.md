🤖 RAG 智能客服助手
基于 Streamlit + FastAPI + LangChain + Chroma 构建的检索增强生成（RAG）智能问答系统
支持本地知识库管理、多会话对话、流式回答、API 服务化部署
✨ 项目特性
📚 本地知识库管理：支持 TXT / MD / JSON 文件上传
💬 双模式对话：RAG 知识库模式 + 普通聊天模式
🔄 流式输出：AI 回答实时显示，体验流畅
🧩 多会话管理：创建、切换、保存、删除历史对话
🌐 API 服务：FastAPI 提供同步 / 流式接口，方便二次开发
📦 轻量化部署：本地一键启动，无需复杂环境
🧱 技术栈
前端界面：Streamlit
后端服务：FastAPI
大模型：通义千问（DashScope）
向量库：Chroma
框架：LangChain
存储：本地文件 + 向量数据库
🚀 快速开始
1. 克隆项目
bash
运行
git clone https://github.com/hu748/rag-customer-service.git
cd 你的仓库名
2. 安装依赖
bash
运行
pip install -r requirements.txt
3. 配置 API Key
在项目根目录创建 .env 文件：
env
DASHSCOPE_API_KEY=你的阿里云百炼API Key
4. 启动 Web 界面
bash
运行
streamlit run app_qa.py
访问：http://localhost:8501
5. 启动 API 服务
bash
运行
python api.py
API 文档：http://localhost:8000/docs
📁 项目结构
plaintext
├── app_qa.py          # Streamlit 主界面
├── api.py             # FastAPI 接口服务
├── rag.py             # RAG 核心逻辑
├── vector_stores.py   # 向量库管理
├── file_history.py    # 会话历史存储
├── config_data.py     # 配置文件
├── requirements.txt   # 依赖清单
├── .env               # 环境变量（不上传 GitHub）
├── .gitignore         # Git 忽略文件
└── README.md          # 项目说明
📌 功能使用说明
配置 API Key
在侧边栏输入 DashScope API Key 并应用
上传知识库
支持 .txt/.md/.json 文件，自动切片入库
开始对话
可切换「知识库模式」，支持多会话
管理会话
查看历史、创建新会话、清空对话
API 调用
支持同步问答、流式问答、会话删除接口
🧪 API 接口列表
GET /health 健康检查
POST /chat 同步聊天
POST /chat/stream 流式聊天
DELETE /session/{session_id} 删除会话
完整文档：http://localhost:8000/docs
📝 注意事项
API Key 请妥善保管，不要上传到 GitHub
知识库文件默认存储在 ./chroma_db
会话历史保存在 ./chat_history
支持批量上传，大文件建议拆分后上传
📄 License
MIT License
🤝 贡献
欢迎提交 Issue 与 PR！
🧡 作者
基于 LangChain + RAG 开发
欢迎 Star 支持～
<img width="1817" height="1004" alt="image" src="https://github.com/user-attachments/assets/c1915d79-7a1d-42bf-8216-e0a6ac709f88" />

