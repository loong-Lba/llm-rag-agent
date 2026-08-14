import json

from chat.dao import HistoryDao
from common import ResponseUtil


# 获取某个用户的所有会话列表（侧边栏）
def find_history_by_user_id(user_id):
    result = HistoryDao.find_history_by_user_id(user_id)
    # 存储数据的列表
    history_list = []
    # 处理结果
    for item in result:
        history_list.append({
            'historyId': item['history_id'],
            'question': item['question'],
            'answer': item['answer'],
            # 格式化时间
            'createTime': item['create_time'].strftime('%Y-%m-%d %H:%M:%S'),
        })
    return ResponseUtil.response_json(200, 'success', history_list)


#获取某一个会话的完整对话记录（聊天窗口）
def find_history_by_id(history_id):
    result = HistoryDao.find_history_by_id(history_id)
    data_list = []
    for item in result:
        question = item.get('question') or ''
        answer = item.get('answer') or ''
        if question:
            data_list.append({
                'role': 'user',
                'content': question,
            })
        if answer:
            data_list.append({
                'role': 'assistant',
                'content': answer,
                'rag': _parse_rag_metadata(item.get('rag_metadata')),
            })
    return ResponseUtil.response_json(200, 'success', data_list)


def _parse_rag_metadata(raw_metadata):
    if not raw_metadata:
        return None
    try:
        return json.loads(raw_metadata)
    except (TypeError, ValueError):
        return None

# 保存继续对话的结果
def open_history_save_data(history):
    result = HistoryDao.open_history_save_data(history)
    if result:          # 如果保存成功（result为True或非空）
        return ResponseUtil.response_json(200, 'success', None)
    return ResponseUtil.response_json(500, 'error', None)

# 删除历史对话记录（删除相同的history_id和他的儿子记录）
def delete_history_by_root_id(history_id):
    return HistoryDao.delete_history_by_root_id(history_id)



# 第一次输入问题，ai回答后，更新这个空对话
def update_history_by_id(history_id, question, answer):
    return HistoryDao.update_history_by_id(history_id, question, answer)