from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from rag import RAGService
import config_data as config
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="智能客服 API", description="基于 RAG 的智能客服服务", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

rag_services = {}

class ChatRequest(BaseModel):
    message: str
    session_id: str = "user_001"
    use_rag: bool = True
    api_key: str = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    use_rag: bool

class StreamChatResponse(BaseModel):
    chunk: str
    session_id: str

@app.post("/chat", response_model=ChatResponse, summary="同步聊天接口")
async def chat(request: ChatRequest):
    """
    同步聊天接口，返回完整的回答
    
    - **message**: 用户输入的消息
    - **session_id**: 会话 ID，用于维护对话历史
    - **use_rag**: 是否使用 RAG 知识库模式
    - **api_key**: DashScope API Key（可选，优先使用传入的 key）
    """
    try:
        api_key = request.api_key or config.DASHSCOPE_API_KEY
        
        if not api_key:
            raise HTTPException(status_code=400, detail="API Key 未配置")
        
        if request.session_id not in rag_services:
            rag_services[request.session_id] = RAGService(api_key=api_key)
        
        service = rag_services[request.session_id]
        service.api_key = api_key
        
        session_config = {
            "configurable": {
                "session_id": request.session_id
            }
        }
        
        response = service.chat_sync(request.message, session_config, use_rag=request.use_rag)
        
        return ChatResponse(
            response=response,
            session_id=request.session_id,
            use_rag=request.use_rag
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/stream", summary="流式聊天接口")
async def chat_stream(request: ChatRequest):
    """
    流式聊天接口，逐步返回回答内容
    
    - **message**: 用户输入的消息
    - **session_id**: 会话 ID，用于维护对话历史
    - **use_rag**: 是否使用 RAG 知识库模式
    - **api_key**: DashScope API Key（可选，优先使用传入的 key）
    """
    try:
        api_key = request.api_key or config.DASHSCOPE_API_KEY
        
        if not api_key:
            raise HTTPException(status_code=400, detail="API Key 未配置")
        
        if request.session_id not in rag_services:
            rag_services[request.session_id] = RAGService(api_key=api_key)
        
        service = rag_services[request.session_id]
        service.api_key = api_key
        
        session_config = {
            "configurable": {
                "session_id": request.session_id
            }
        }
        
        stream = service.chat(request.message, session_config, use_rag=request.use_rag)
        
        async def generate():
            for chunk in stream:
                yield {
                    "chunk": chunk,
                    "session_id": request.session_id
                }
        
        return generate()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/session/{session_id}", summary="删除会话")
async def delete_session(session_id: str):
    """
    删除指定会话及其历史记录
    
    - **session_id**: 要删除的会话 ID
    """
    if session_id in rag_services:
        del rag_services[session_id]
        return {"message": f"会话 {session_id} 已删除"}
    else:
        raise HTTPException(status_code=404, detail="会话不存在")

@app.get("/health", summary="健康检查")
async def health_check():
    """
    健康检查接口
    """
    return {"status": "healthy", "service": "RAG Chat Service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)