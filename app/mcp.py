"""
用于 mcpclient连接 mcp server

三种协议
sse_server
stdio_server
streamable_server

"""
from typing import Optional, Dict, Any
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamable_http_client


class MCPClient:
    """MCP 客户端，支持 stdio、sse、streamable http 三种协议"""

    def __init__(self, server_params: dict, protocol: str):
        self.session: Optional[ClientSession] = None
        self.server_params = server_params
        self.protocol = protocol
        self._stream_context = None
        self._session_context = None

    async def connect_to_server(self) -> bool:
        """连接 MCP Server"""
        try:
            # 1. 根据协议类型建立对应的连接上下文
            if self.protocol == "stdio":
                params = StdioServerParameters(
                    command=self.server_params.get("command"),
                    args=self.server_params.get("args", []),
                    env=self.server_params.get("env")
                )
                self._stream_context = stdio_client(params)
                
            elif self.protocol == "sse":
                self._stream_context = sse_client(self.server_params["url"])
                
            elif self.protocol in ("streamable http", "streamable_http"):
                self._stream_context = streamable_http_client(self.server_params["url"])
                
            else:
                raise ValueError(f"Invalid protocol: {self.protocol}")

            # 2. 统一获取流对象（兼容不同协议返回值的差异）
            entered = await self._stream_context.__aenter__()
            read_stream, write_stream = entered[0], entered[1]

            # 3. 建立并初始化 MCP 会话
            self._session_context = ClientSession(read_stream, write_stream)
            self.session = await self._session_context.__aenter__()
            
            await self.session.initialize()
            print(f"✅ Connected to MCP Server via {self.protocol}")
            return True

        except Exception as e:
            print(f"❌ Failed to connect to server: {str(e)}")
            if hasattr(e, '_cause') and e.__cause__:
                print(f"Caused by: {str(e.__cause__)}")
            if hasattr(e, '__context__') and e.__context__:
                print(f"Context: {str(e.__context__)}")
            raise

    async def ping(self) -> Any:
        """检查 MCP Server 是否在线（心跳）"""
        if not self.session:
            raise RuntimeError("Client is not connected. Call connect_to_server() first.")
        
        # 兼容不同版本的 MCP SDK
        if hasattr(self.session, 'send_ping'):
            response = await self.session.send_ping()
        elif hasattr(self.session, 'ping'):
            response = await self.session.ping()
        else:
            # 如果都没有，用 list_tools 作为兜底健康检查
            response = await self.session.list_tools()
            
        return response

    async def call_tool(self, tool_name: str, tool_params: dict) -> Any:
        """调用 MCP Server 提供的工具"""
        if not self.session:
            raise RuntimeError("Client is not connected. Call connect_to_server() first.")
            
        response = await self.session.call_tool(tool_name, tool_params)
        return response

    async def list_tools(self) -> Any:
        """获取 MCP Server 提供的工具列表"""
        if not self.session:
            raise RuntimeError("Client is not connected. Call connect_to_server() first.")
            
        response = await self.session.list_tools()
        return response

    async def cleanup(self):
        """安全断开连接，释放资源。保证 100% 不抛异常"""
        session_ctx = getattr(self, '_session_context', None)
        stream_ctx = getattr(self, '_stream_context', None)
        
        # 清理 session context
        if session_ctx:
            try:
                await session_ctx.__aexit__(None, None, None)
            except BaseException as e:
                print(f"⚠️ session __aexit__ 异常（已忽略）: {type(e).__name__}: {e}")
            finally:
                self._session_context = None
                self.session = None
        
        # 清理 stream context
        if stream_ctx:
            try:
                await stream_ctx.__aexit__(None, None, None)
            except BaseException as e:
                print(f"⚠️ stream __aexit__ 异常（已忽略）: {type(e).__name__}: {e}")
            finally:
                self._stream_context = None
        
        print("🔌 Disconnected from MCP Server")