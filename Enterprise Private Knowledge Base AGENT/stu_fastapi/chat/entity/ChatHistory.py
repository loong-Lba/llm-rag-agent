from dataclasses import dataclass
from pydantic import BaseModel, Field

# 定义聊天记录的数据结构，用于接收前端数据、自动校验字段、生成API文档
@dataclass
class ChatHistory(BaseModel):
    question: str = Field(description='问题')
    answer: str = Field(description='答案')
    parentId: int = Field(description='父级id')
    userId: int = Field(description='用户id')