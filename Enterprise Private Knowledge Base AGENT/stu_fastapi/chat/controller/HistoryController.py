from chat.service import HistoryService
from fastapi import APIRouter
from chat.entity.ChatHistory import ChatHistory

history_router = APIRouter()


# 历史记录
@history_router.get('/list')
def find_history_by_user_id(userId):
    return HistoryService.find_history_by_user_id(userId)



# 获取完整的对话记录
@history_router.get('/findHistoryById')
def find_history_by_id(historyId):
    return HistoryService.find_history_by_id(historyId)


# 保存继续对话的结果
@history_router.post('/openHistorySaveData')
def open_history_save_data(history: ChatHistory):
    return HistoryService.open_history_save_data(history)

# 删除历史对话记录（删除相同的history_id和他的儿子记录）
@history_router.delete('/deleteHistoryByRootId')
def delete_history_by_root_id(history_id):
    return HistoryService.delete_history_by_root_id(history_id)


# 第一次输入问题，ai回答后，更新这个空对话
    # 第一次输入问题，ai回答后，更新这个空对话
@history_router.put('/updateHistoryById')
def update_history_by_id(history_id:str, question:str, answer:str):
    return HistoryService.update_history_by_id(history_id, question, answer)