"""
    这里的方法就是通过智能体agent对象来完成：
    1. 问题识别
    2. 判定是否需要调用工具
    3. 如果需要调用工具，调用哪一个工具或哪几个工具
    4. 如果不需要调工具，直接通过LLM输出结果
"""
import ast
import json
from ...common import ResponseUtil
from langchain_core.messages import AIMessage, ToolMessage


def _content_to_text(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                if "text" in item:
                    parts.append(str(item["text"]))
                else:
                    parts.append(json.dumps(item, ensure_ascii=False))
            else:
                parts.append(str(item))
        return "".join(parts)
    if isinstance(content, dict):
        return json.dumps(content, ensure_ascii=False)
    return str(content)


def _parse_possible_json(value):
    if isinstance(value, (dict, list)):
        return value
    text = _content_to_text(value).strip()
    if not text:
        return text
    for parser in (json.loads, ast.literal_eval):
        try:
            return parser(text)
        except Exception:
            continue
    return text


def _extract_messages(response):
    return response.get("messages", []) if isinstance(response, dict) else []


def _extract_tool_calls(messages, tool_name):
    calls = []
    for msg in messages:
        if isinstance(msg, AIMessage):
            tool_calls = getattr(msg, "tool_calls", None) or []
            for call in tool_calls:
                if call.get("name") == tool_name:
                    args = _parse_possible_json(call.get("args", {}))
                    if isinstance(args, dict):
                        calls.append(args)
                    else:
                        calls.append({})
    return calls


def _extract_tool_results(messages, tool_name):
    results = []
    for msg in messages:
        if isinstance(msg, ToolMessage):
            name = getattr(msg, "name", "")
            if name == tool_name:
                results.append(_parse_possible_json(msg.content))
    return results


def _find_email_in_data(data):
    if isinstance(data, dict):
        if "email" in data and data.get("email"):
            return data.get("email")
        for value in data.values():
            email = _find_email_in_data(value)
            if email:
                return email
    if isinstance(data, list):
        for item in data:
            email = _find_email_in_data(item)
            if email:
                return email
    return ""


def _contains_success(data, *keywords):
    if isinstance(data, (dict, list)):
        text = json.dumps(data, ensure_ascii=False)
    else:
        text = _content_to_text(data)
    return any(keyword in text for keyword in keywords)


def _normalize_send_email_result(response):
    messages = _extract_messages(response)
    find_email_results = _extract_tool_results(messages, "find_email")
    send_email_calls = _extract_tool_calls(messages, "send_email")
    send_email_results = _extract_tool_results(messages, "send_email")

    receiver = ""
    for call in send_email_calls:
        receiver = call.get("receiver", "") or receiver

    if not receiver:
        for result in find_email_results:
            receiver = _find_email_in_data(result) or receiver

    if send_email_results and any(_contains_success(item, "发送成功") for item in send_email_results):
        return {
            "code": 200,
            "msg": "发送成功",
            "data": receiver,
        }

    raw_result = ResponseUtil.response_util(response)
    if isinstance(raw_result, dict):
        code = str(raw_result.get("code", "")).strip()
        msg = str(raw_result.get("msg", "") or "").strip()
        data = raw_result.get("data", "") or receiver
        if code == "200" or "发送成功" in msg:
            return {
                "code": 200,
                "msg": "发送成功",
                "data": data,
            }
        if code == "404" or "未找到" in msg:
            return {
                "code": 404,
                "msg": msg or "未找到该用户名绑定的邮箱，请确认用户名是否正确。"
            }
        return {
            "code": 500,
            "msg": msg or "发送失败"
        }

    text = str(raw_result).strip()
    if "发送成功" in text:
        return {
            "code": 200,
            "msg": "发送成功",
            "data": receiver,
        }
    if "未找到" in text:
        return {
            "code": 404,
            "msg": "未找到该用户名绑定的邮箱，请确认用户名是否正确。"
        }
    return {
        "code": 500,
        "msg": text or "发送失败"
    }


def _normalize_verify_code_result(response):
    messages = _extract_messages(response)
    verify_results = _extract_tool_results(messages, "verify_code")

    if verify_results and any(_contains_success(item, "验证成功", "验证码正确", "验证通过") for item in verify_results):
        return {
            "code": 200,
            "msg": "登录成功"
        }

    raw_result = ResponseUtil.response_util(response)
    if isinstance(raw_result, dict):
        code = str(raw_result.get("code", "")).strip()
        msg = str(raw_result.get("msg", "") or "").strip()
        if code == "200" or "验证通过" in msg or "验证码正确" in msg or "登录成功" in msg:
            return {
                "code": 200,
                "msg": "登录成功"
            }
        return {
            "code": 500,
            "msg": msg or "验证码错误或已过期，请重新获取。"
        }

    text = str(raw_result).strip()
    if "验证通过" in text or "验证码正确" in text or "登录成功" in text or "验证成功" in text:
        return {
            "code": 200,
            "msg": "登录成功"
        }
    return {
        "code": 500,
        "msg": text or "验证码错误或已过期，请重新获取。"
    }


# 邮箱登录
def send_email(username, agent):
    response = agent.invoke({
        "messages": [
            {"role": "user", "content": f"请帮我给用户{username}发送验证码"}
        ]
    })
    return _normalize_send_email_result(response)


# 验证验证码
def verify_code(receiver, code, agent):
    response = agent.invoke({
        "messages": [
            {"role": "user", "content": f"验证验证码，邮箱号为{receiver}，验证码为{code}"}
        ]
    })
    return _normalize_verify_code_result(response)
