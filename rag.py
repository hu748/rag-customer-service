from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableWithMessageHistory, RunnableLambda
from file_history import get_history
from vector_stores import VectorStoreService
from langchain_community.embeddings import DashScopeEmbeddings
import config_data as config
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_models.tongyi import ChatTongyi


def print_prompt(prompt):
    print("*" * 20)
    print(prompt.to_string())
    print("*" * 20)
    return prompt


class RAGService(object):
    def __init__(self, api_key=None):
        self.api_key = api_key or config.DASHSCOPE_API_KEY
        
        if self.api_key:
            self.vector_service = VectorStoreService(
                embedding=DashScopeEmbeddings(model=config.embedding_model_name, dashscope_api_key=self.api_key)
            )
            self.chat_model = ChatTongyi(
                model=config.chat_model_name,
                api_key=self.api_key
            )
        else:
            self.vector_service = None
            self.chat_model = None
        
        self.rag_chain = self._get_rag_chain()
        self.chat_chain = self._get_chat_chain()
    
    def _get_rag_chain(self):
        if not self.api_key or not self.vector_service:
            return None
        
        retriever = self.vector_service.get_retriever()
        
        def format_document(docs: list[Document]):
            if not docs:
                return "无相关参考资料"
            formatted_str = ""
            for doc in docs:
                formatted_str += f"文档片段:{doc.page_content}\n文档元数据:{doc.metadata}\n\n"
            return formatted_str
        
        def temp1(value: dict) -> str:
            return value["input"]
        
        def temp2(value):
            new_value = {}
            new_value["input"] = value["input"]["input"]
            new_value["context"] = value["context"]
            new_value["history"] = value["input"]["history"]
            return new_value
        
        chain = (
            {
                "input": RunnablePassthrough(),
                "context": RunnableLambda(temp1) | retriever | format_document
            } | RunnableLambda(temp2) | self.prompt_template | print_prompt | self.chat_model | StrOutputParser()
        )
        
        conversation_chain = RunnableWithMessageHistory(
            chain,
            get_history,
            input_messages_key="input",
            history_messages_key="history"
        )
        return conversation_chain
    
    def _get_chat_chain(self):
        if not self.api_key or not self.chat_model:
            return None
        
        chat_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "你是一个智能助手，请根据历史对话和用户提问提供友好、专业的回答。"),
                MessagesPlaceholder("history"),
                ("user", "{input}")
            ]
        )
        
        chain = chat_prompt | self.chat_model | StrOutputParser()
        
        conversation_chain = RunnableWithMessageHistory(
            chain,
            get_history,
            input_messages_key="input",
            history_messages_key="history"
        )
        return conversation_chain
    
    @property
    def prompt_template(self):
        return ChatPromptTemplate.from_messages(
            [
                ("system", "以我提供的资料为主简洁和专业的回答用户问题.参考资料:{context}"),
                ("system", "并且以我提供的用户对话为历史记录,如下:"),
                MessagesPlaceholder("history"),
                ("user", "请回答用户提问{input}")
            ]
        )
    
    def chat(self, prompt, session_config, use_rag=True):
        if not self.api_key:
            return "请先配置 API Key"
        
        if use_rag and self.rag_chain:
            return self.rag_chain.stream({"input": prompt}, session_config)
        elif self.chat_chain:
            return self.chat_chain.stream({"input": prompt}, session_config)
        else:
            return "模型初始化失败，请检查 API Key"
    
    def chat_sync(self, prompt, session_config, use_rag=True):
        if not self.api_key:
            return "请先配置 API Key"
        
        if use_rag and self.rag_chain:
            return self.rag_chain.invoke({"input": prompt}, session_config)
        elif self.chat_chain:
            return self.chat_chain.invoke({"input": prompt}, session_config)
        else:
            return "模型初始化失败，请检查 API Key"
    
    def add_document(self, text, metadata=None):
        if not self.api_key or not self.vector_service:
            return {"success": False, "message": "请先配置 API Key"}
        
        try:
            count = self.vector_service.add_text(text, metadata)
            return {"success": True, "message": f"成功添加 {count} 个文档片段", "count": count}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def add_file(self, file_path, metadata=None):
        if not self.api_key or not self.vector_service:
            return {"success": False, "message": "请先配置 API Key"}
        
        try:
            count = self.vector_service.add_file(file_path, metadata)
            if count == 0:
                return {"success": False, "message": "文件不存在或内容为空"}
            return {"success": True, "message": f"成功添加 {count} 个文档片段", "count": count}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def add_files(self, file_paths, metadata=None):
        if not self.api_key or not self.vector_service:
            return {"success": False, "message": "请先配置 API Key"}
        
        total_count = 0
        results = []
        
        for file_path in file_paths:
            try:
                count = self.vector_service.add_file(file_path, metadata)
                total_count += count
                results.append({"file": file_path, "count": count, "success": count > 0})
            except Exception as e:
                results.append({"file": file_path, "success": False, "error": str(e)})
        
        return {
            "success": True,
            "message": f"成功处理 {len(file_paths)} 个文件，共添加 {total_count} 个文档片段",
            "total_count": total_count,
            "results": results
        }
    
    def get_collection_stats(self):
        if not self.api_key or not self.vector_service:
            return {"success": False, "message": "请先配置 API Key"}
        
        try:
            stats = self.vector_service.get_collection_stats()
            return {
                "success": True,
                "document_count": len(stats.get('ids', [])),
                "stats": stats
            }
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def clear_collection(self):
        if not self.api_key or not self.vector_service:
            return {"success": False, "message": "请先配置 API Key"}
        
        try:
            self.vector_service.clear_all_documents()
            return {"success": True, "message": "知识库已清空"}
        except Exception as e:
            return {"success": False, "message": str(e)}


if __name__ == "__main__":
    session_config = {
        "configurable": {
            "session_id": "user_001"
        }
    }
    
    api_key = config.DASHSCOPE_API_KEY
    if not api_key:
        api_key = input("请输入您的 DashScope API Key: ")
    
    service = RAGService(api_key=api_key)
    
    res = service.chat_sync("我体重180斤,尺码推荐", session_config, use_rag=True)
    print("RAG模式回答:", res)
    
    res2 = service.chat_sync("你好", session_config, use_rag=False)
    print("普通聊天模式回答:", res2)
