from langchain_mcp_adapters.client import MultiServerMCPClient


async def get_mcp_studio_tools_async(tool_path, tool_name):
    """
    创建MCP客户端并获取工具
    返回: (client, tools) 元组，调用者负责关闭 client
    """
    client = MultiServerMCPClient(
        {
            tool_name: {
                "command": "python",
                "args": [tool_path],
                "transport": "stdio",
            },
        }
    )

    all_tools = await client.get_tools()
    return client, all_tools

