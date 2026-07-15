import json

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

def response_util(response):
    # 调用模型后的响应结果是一个字典，我们需要提取的就是字典中最后一个AIMessage的content的内容---响应结果
    messages = response.get('messages', [])
    if not messages:
        return {"code": 500, "msg": "没有消息"}

    ai_contents = []
    for msg in messages:
        if isinstance(msg, AIMessage) and msg.content:
            ai_contents.append(msg.content)

    if not ai_contents:
        return {"code": 500, "msg": "没有消息"}

    result = ai_contents[-1]
    try:
        return json.loads(result)
    except Exception:
        return result

