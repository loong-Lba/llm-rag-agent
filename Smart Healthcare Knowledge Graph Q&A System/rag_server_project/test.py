import json

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

# 调用模型后的响应结果是一个字典，我们需要提取的就是字典中最后一个AIMessage的content的内容---响应结果
messages = response.get('messages',[])
if not messages:
    print("没有消息")
# 存储AIMessage中的内容
ai_content = []
# 遍历messages， 判断类型是否满足为AIMessage且内容不为空
for msg in messages:
    if isinstance(msg, AIMessage) and msg.content:
        ai_content.append(json.loads(msg.content))
# 输出结果 ---只要最后一个AIMessage的content
result = ai_content[-1]
if result:
    print(result)
else:
    print("没有结果")