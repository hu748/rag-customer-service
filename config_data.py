import os
from dotenv import load_dotenv

load_dotenv()

MD5_FILE_PATH = "./md.text"

collections_name = "rag"
persist_directory = "./chroma_db"

chunk_size = 1000
chunk_overlap = 100
separators = ["\n\n", "\n", "!", "。", "，", ",", "."]

max_split_char_number = 1000
similarity_threshold = 2

embedding_model_name = "text-embedding-v4"
chat_model_name = "qwen3-max"

DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")

session_config = {
    "configurable": {
        "session_id": "user_001"
    }
}