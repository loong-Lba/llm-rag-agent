import asyncio
# 导入fastmcp客户端
from fastmcp import Client
# 忽略警告
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

# MCPServer的访问地址
MCP_SERVER_URL = "http://127.0.0.1:9000/mcp"

"""
    封装一个函数，用来同步调用MCP服务器中的工具
    同步调用对于后期agent那一块的代码处理更方便
    由于MCP服务器中的工具是异步定义的，所以调用的时候也需要异步
    我们封装的这个函数就把异步的调用转为同步调用
"""
"""
    call_mcp_tool：一个同步函数，后期提供给agent中调用mcp服务器工具
        1、tool_name：工具的名称
        2、**kwargs：调用工具的参数，是一个可变参数
"""


def call_mcp_tool(tool_name, **kwargs):
    # 创建一个异步函数，来调用mcp服务器中的工具
    async def _call():
        # 异步调用MCP服务器中的工具 --- 调用完就释放
        async with Client(MCP_SERVER_URL) as client:
            # 调用MCP服务器中的工具
            return await client.call_tool(tool_name, kwargs)
    # 运行异步函数
    return asyncio.run(_call())


# 测试
if __name__ == '__main__':
    data = call_mcp_tool("find_email", sql="select * from users where username=%s", params="3060930023@qq.com")
    print(data)
