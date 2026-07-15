# 加载阿里云百炼平台模型 --- 千问模型
from langchain_openai import ChatOpenAI
import os


def load_model():
    return ChatOpenAI(
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        model="qwen3.7-plus",
        streaming=True,
    )
