from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
import config_data as config
import os

class VectorStoreService(object):
    def __init__(self, embedding):
        self.embedding = embedding
        self.vector_store = Chroma(
            collection_name=config.collections_name,
            embedding_function=self.embedding,
            persist_directory=config.persist_directory
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,
            separators=config.separators,
        )

    def get_retriever(self):
        return self.vector_store.as_retriever(search_kwargs={"k": config.similarity_threshold})

    def add_documents(self, documents):
        if not documents:
            return 0
        
        split_docs = self.text_splitter.split_documents(documents)
        self.vector_store.add_documents(split_docs)
        return len(split_docs)

    def add_text(self, text, metadata=None):
        docs = [Document(page_content=text, metadata=metadata or {})]
        return self.add_documents(docs)

    def _extract_text_from_pdf(self, file_path):
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            raise ValueError(f"PDF解析失败: {str(e)}")

    def _extract_text_from_docx(self, file_path):
        try:
            from docx import Document
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            raise ValueError(f"Word文档解析失败: {str(e)}")

    def _extract_text_from_excel(self, file_path):
        try:
            import pandas as pd
            df = pd.read_excel(file_path)
            text = df.to_string(index=False)
            return text.strip()
        except Exception as e:
            raise ValueError(f"Excel文档解析失败: {str(e)}")

    def _extract_text_from_file(self, file_path):
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        if ext == ".pdf":
            return self._extract_text_from_pdf(file_path)
        elif ext == ".docx":
            return self._extract_text_from_docx(file_path)
        elif ext in [".xlsx", ".xls"]:
            return self._extract_text_from_excel(file_path)
        elif ext in [".txt", ".md", ".json"]:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            raise ValueError(f"不支持的文件格式: {ext}")

    def add_file(self, file_path, metadata=None):
        if not os.path.exists(file_path):
            return 0
        
        try:
            text = self._extract_text_from_file(file_path)
            
            doc_metadata = metadata or {}
            doc_metadata['source'] = file_path
            doc_metadata['file_name'] = os.path.basename(file_path)
            
            if text:
                return self.add_text(text, doc_metadata)
            else:
                return 0
        except Exception as e:
            raise e

    def get_collection_stats(self):
        return self.vector_store.get()

    def clear_all_documents(self):
        self.vector_store.delete_collection()
        self.vector_store = Chroma(
            collection_name=config.collections_name,
            embedding_function=self.embedding,
            persist_directory=config.persist_directory
        )

    @staticmethod
    def get_supported_formats():
        return ["txt", "md", "json", "pdf", "docx", "xlsx", "xls"]

if __name__ == '__main__':
    from langchain_community.embeddings import DashScopeEmbeddings
    retriever = VectorStoreService(DashScopeEmbeddings(model="text-embedding-v4", dashscope_api_key="sk-8f296b06c5cd4d10aa13d8eae463e6a8")).get_retriever()
    res = retriever.invoke("我的体重180斤,尺码推荐")
    print(res)