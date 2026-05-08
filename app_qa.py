import time
from rag import RAGService
import streamlit as st
import config_data as config
import os

st.set_page_config(page_title="智能客服", page_icon="🤖", layout="wide")

st.title("🤖 智能客服")
st.divider()

if "api_key" not in st.session_state:
    st.session_state["api_key"] = config.DASHSCOPE_API_KEY

if "message" not in st.session_state:
    st.session_state["message"] = [{"role": "assistant", "content": "你好！有什么可以帮助你的吗？"}]

if "rag" not in st.session_state:
    st.session_state["rag"] = None

if "session_id" not in st.session_state:
    st.session_state["session_id"] = "user_001"

if "collection_stats" not in st.session_state:
    st.session_state["collection_stats"] = None

if "use_rag" not in st.session_state:
    st.session_state["use_rag"] = True

def init_rag_service():
    if st.session_state["api_key"] and not st.session_state["rag"]:
        st.session_state["rag"] = RAGService(api_key=st.session_state["api_key"])
    return st.session_state["rag"]

def update_collection_stats():
    rag = init_rag_service()
    if rag:
        stats = rag.get_collection_stats()
        st.session_state["collection_stats"] = stats

def get_history_sessions():
    history_dir = "./chat_history"
    sessions = []
    if os.path.exists(history_dir):
        for filename in os.listdir(history_dir):
            file_path = os.path.join(history_dir, filename)
            if os.path.isfile(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        import json
                        messages = json.load(f)
                        if messages:
                            first_message = messages[0]
                            preview = first_message.get('data', {}).get('content', '')[:30] if isinstance(first_message, dict) else str(first_message)[:30]
                        else:
                            preview = "空会话"
                except:
                    preview = "无法读取"
                sessions.append({
                    'id': filename,
                    'preview': preview,
                    'mtime': os.path.getmtime(file_path)
                })
        sessions.sort(key=lambda x: x['mtime'], reverse=True)
    return sessions

def load_session_history(session_id):
    history_dir = "./chat_history"
    file_path = os.path.join(history_dir, session_id)
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                import json
                messages = json.load(f)
                chat_messages = []
                for msg in messages:
                    if isinstance(msg, dict) and 'data' in msg:
                        role = msg['data'].get('type', 'assistant')
                        if role == 'human':
                            role = 'user'
                        elif role == 'ai':
                            role = 'assistant'
                        content = msg['data'].get('content', '')
                        chat_messages.append({"role": role, "content": content})
                if chat_messages:
                    return chat_messages
        except:
            pass
    return [{"role": "assistant", "content": "你好！有什么可以帮助你的吗？"}]

with st.sidebar:
    st.header("⚙️ 设置")
    
    api_key_input = st.text_input(
        "DashScope API Key",
        value=st.session_state["api_key"],
        type="password",
        placeholder="请输入您的 DashScope API Key"
    )
    
    if st.button("应用 API Key"):
        if api_key_input:
            st.session_state["api_key"] = api_key_input
            st.session_state["rag"] = RAGService(api_key=api_key_input)
            update_collection_stats()
            st.success("API Key 已应用！")
        else:
            st.warning("请输入有效的 API Key")
    
    st.divider()
    
    st.header("📚 知识库管理")
    
    with st.expander("📋 支持的文件格式", expanded=True):
        st.markdown("""
        **文本文件**: `.txt`, `.md`, `.json`
        \n**PDF文档**: `.pdf`
        \n**Word文档**: `.docx`
        \n**Excel表格**: `.xlsx`, `.xls`
        
        **提示**:
        - 支持多文件同时上传
        - 重复文件名会自动跳过
        - 文件大小建议不超过 10MB
        - PDF 文档需确保可复制（扫描件可能无法解析）
        """)
    
    uploaded_files = st.file_uploader(
        "📁 选择要上传的文件",
        type=["txt", "md", "json", "pdf", "docx", "xlsx", "xls"],
        accept_multiple_files=True,
        help="支持：txt, md, json, pdf, docx, xlsx, xls",
        key="file_uploader"
    )
    
    if st.button("上传到知识库"):
        if not st.session_state["api_key"]:
            st.error("请先配置 API Key！")
        elif not uploaded_files:
            st.warning("请先选择要上传的文件！")
        else:
            rag = init_rag_service()
            if rag:
                with st.spinner("正在处理文件..."):
                    temp_dir = "./temp_uploads"
                    os.makedirs(temp_dir, exist_ok=True)
                    
                    file_paths = []
                    existing_files = set()
                    success_count = 0
                    failed_files = []
                    
                    for uploaded_file in uploaded_files:
                        file_name = uploaded_file.name
                        file_path = os.path.join(temp_dir, file_name)
                        
                        if file_name in existing_files:
                            st.warning(f"⚠️ 跳过重复文件: {file_name}")
                            continue
                        existing_files.add(file_name)
                        
                        try:
                            with open(file_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                            file_paths.append(file_path)
                        except Exception as e:
                            failed_files.append(f"{file_name}: 写入失败 - {str(e)}")
                    
                    if file_paths:
                        try:
                            result = rag.add_files(file_paths)
                            
                            if result["success"]:
                                update_collection_stats()
                                st.success(f"✅ 成功处理 {len(file_paths)} 个文件，共添加 {result['total_count']} 个文档片段")
                                
                                if result.get('results'):
                                    for res in result['results']:
                                        if res['success']:
                                            st.info(f"📄 {os.path.basename(res['file'])}: 成功添加 {res['count']} 个片段")
                                        else:
                                            error_msg = res.get('error', '未知错误')
                                            st.warning(f"⚠️ {os.path.basename(res['file'])}: {error_msg}")
                            else:
                                st.error(f"❌ 上传失败: {result['message']}")
                        finally:
                            for file_path in file_paths:
                                if os.path.exists(file_path):
                                    os.remove(file_path)
                    else:
                        st.warning("⚠️ 没有可上传的文件")
                    
                    if failed_files:
                        st.error("以下文件处理失败:")
                        for fail in failed_files:
                            st.write(f"- {fail}")
    
    st.divider()
    
    st.subheader("知识库统计")
    if st.session_state["collection_stats"]:
        stats = st.session_state["collection_stats"]
        if stats["success"]:
            st.metric("文档片段数", stats["document_count"])
        else:
            st.warning(stats["message"])
    else:
        rag = init_rag_service()
        if rag:
            update_collection_stats()
            if st.session_state["collection_stats"]:
                stats = st.session_state["collection_stats"]
                if stats["success"]:
                    st.metric("文档片段数", stats["document_count"])
    
    if st.button("刷新统计"):
        update_collection_stats()
        st.success("已刷新")
    
    if st.button("清空知识库", type="secondary"):
        rag = init_rag_service()
        if rag:
            result = rag.clear_collection()
            if result["success"]:
                update_collection_stats()
                st.success(result["message"])
            else:
                st.error(result["message"])
    
    st.divider()
    
    st.header("💬 历史会话")
    sessions = get_history_sessions()
    
    if sessions:
        for session in sessions:
            is_active = session['id'] == st.session_state["session_id"]
            button_key = f"session_{session['id']}"
            if st.button(
                f"📝 {session['id']}\n{session['preview']}...",
                key=button_key,
                disabled=is_active,
                type="primary" if is_active else "secondary"
            ):
                st.session_state["session_id"] = session['id']
                st.session_state["message"] = load_session_history(session['id'])
                st.success(f"已切换到会话: {session['id']}")
                st.rerun()
    else:
        st.info("暂无历史会话")
    
    st.divider()
    
    session_id_input = st.text_input(
        "新建会话 ID",
        placeholder="输入新会话名称"
    )
    if st.button("创建新会话"):
        if session_id_input:
            st.session_state["session_id"] = session_id_input
            st.session_state["message"] = [{"role": "assistant", "content": "你好！有什么可以帮助你的吗？"}]
            st.success(f"已创建新会话: {session_id_input}")
        else:
            st.warning("请输入会话名称")
    
    if st.button("清空当前对话"):
        st.session_state["message"] = [{"role": "assistant", "content": "你好！有什么可以帮助你的吗？"}]
        st.success("对话已清空")

update_collection_stats()

col1, col2 = st.columns([3, 1])
with col1:
    st.subheader("对话")
with col2:
    rag_mode = st.toggle(
        "📚 知识库模式",
        value=st.session_state["use_rag"],
        help="开启时使用知识库回答，关闭时使用普通聊天"
    )
    st.session_state["use_rag"] = rag_mode

for message in st.session_state["message"]:
    with st.chat_message(message["role"]):
        st.write(message["content"])

prompt = st.chat_input("请输入你的问题...")

if prompt:
    if not st.session_state["api_key"]:
        st.error("请先在侧边栏配置 API Key！")
    else:
        rag = init_rag_service()
        if not rag:
            st.error("RAG 服务初始化失败！")
        else:
            st.chat_message("user").write(prompt)
            st.session_state["message"].append({"role": "user", "content": prompt})
            
            ai_res_list = []
            with st.spinner("AI 思考中..."):
                session_config = {
                    "configurable": {
                        "session_id": st.session_state["session_id"]
                    }
                }
                
                res = rag.chat(prompt, session_config, use_rag=st.session_state["use_rag"])
                
                def capture(generator, cache_list):
                    for chunk in generator:
                        cache_list.append(chunk)
                        yield chunk
                
                with st.chat_message("assistant"):
                    st.write_stream(capture(res, ai_res_list))
                
                st.session_state["message"].append({"role": "assistant", "content": "".join(ai_res_list)})
