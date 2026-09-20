from mcp.server.mcpserver import MCPServer
import uvicorn

# v2 中直接实例化 MCPServer
mcp = MCPServer("Local Math Server")

@mcp.tool()
def add(a: float, b: float) -> float:
    """计算两个数相加 (a + b)"""
    return a + b

@mcp.tool()
def subtract(a: float, b: float) -> float:
    """计算两个数相减 (a - b)"""
    return a - b

@mcp.tool()
def multiply(a: float, b: float) -> float:
    """计算两个数相乘 (a * b)"""
    return a * b

@mcp.tool()
def divide(a: float, b: float) -> float:
    """计算两个数相除 (a / b)"""
    if b == 0:
        raise ValueError("除数不能为 0")
    return a / b

if __name__ == "__main__":
    # v2 中推荐手动获取 ASGI 应用并用 uvicorn 启动
    print("启动本地计算 MCP Server，监听 http://localhost:8002/mcp")
    app = mcp.streamable_http_app()
    uvicorn.run(app, host="0.0.0.0", port=8002)

# key 用来表示接口鉴权，真实 的后端是放在  Header 方式 
# {
#   "url": "http://localhost:8002/mcp?key=87a22f1ebdb9cf32a459d286c63b9bf9"
# }


"""

{
  "mcpServers": {
    "local-math-server": {
      "type": "streamableHttp",
      "url": "http://localhost:8002/mcp"
    }
  }
}
"""