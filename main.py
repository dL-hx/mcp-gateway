from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, APIRouter, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import json
from app import schemas, models, orm
from app.database import engine, get_db, Base
from typing import Optional, Dict, List
from app.mcp import MCPClient
from app.models import MCPServer  # 导入你的数据模型
import asyncio 
from fastapi.responses import JSONResponse

load_dotenv()


# 全局客户端缓存字典：{server_id: MCPClient}
mcp_clients: Dict[int, MCPClient] = {}

async def connect_and_cache_client(mcp_server: MCPServer) -> bool:
    """连接并缓存 MCP 客户端（如果已缓存则直接复用并校验心跳）"""
    
    # 1. 如果已在缓存中
    if mcp_server.id in mcp_clients:
        client = mcp_clients[mcp_server.id]
        try:
            await client.ping()
            return True
        except Exception as e:
            print(f"MCP Server {mcp_server.id} is offline {e}")
            # 关键修复：如果原本在缓存中但 ping 失败了，说明连接已死，必须剔除缓存并清理资源
            mcp_clients.pop(mcp_server.id, None)
            try:
                await client.cleanup()
            except Exception:
                pass
            return False
            
    # 2. 如果不在缓存中，建立新连接
    else:
        client = None
        try:
            server_params = json.loads(mcp_server.cfg)
            client = MCPClient(server_params, mcp_server.protocol)
            await client.connect_to_server()
            await client.ping()
            
            # 连接并 ping 成功，写入缓存
            mcp_clients[mcp_server.id] = client
            return True
        except Exception as e:
            print(f"MCP Server {mcp_server.id} is offline {e}")
            # 关键修复：连接失败时，必须清理刚刚创建的客户端资源，防止泄露
            if client:
                try:
                    await client.cleanup()
                except Exception:
                    pass
            return False


# 创建数据库表
models.Base.metadata.create_all(bind=engine)

app = FastAPI()
app_router = APIRouter(prefix = '/api')


# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app_router.get("/")
async def root():
    return {"message": "Hello World"}

# 创建 MCP Server 接口（修复了你源码中参数缺少 api_key 默认值的问题）
@app_router.post("/mcp_server", response_model=schemas.MCPServerResponse)
async def create_mcp_server(
    mcp_server_create: schemas.MCPServerCreate,
    db: Session = Depends(get_db),
):
    # 查询是否已经存在同名的 mcp server
    existing_mcp_server = orm.get_mcp_server_db(db, mcp_server_create.name)
    if existing_mcp_server:
        raise HTTPException(status_code=400, detail="MCP server with this name already exists")
    
    created_mcp_server = orm.create_mcp_server_db(db, mcp_server_create)
    return created_mcp_server


# 查询 MCP Server 列表# 查询 MCP Server 列表（带状态和工具）
@app_router.get("/mcp_server", response_model=List[schemas.MCPServerWithStatusResponse])
async def get_mcp_server_list(db: Session = Depends(get_db)):
    mcp_server_list = orm.get_mcp_server_list_db(db)
    
    async def fetch_server_status(server: models.MCPServer):
        """获取单个服务端的在线状态和工具"""
        # 1. 尝试连接并检查心跳
        is_online = await connect_and_cache_client(server)
        
        # 2. 如果在线，尝试获取工具列表
        tools_list = []
        if is_online and server.id in mcp_clients:
            try:
                # 从缓存的 client 中获取工具
                tools_response = await mcp_clients[server.id].list_tools()
                # 将工具对象转为字典，方便前端解析
                tools_list = [
                    {
                        "name": t.name,
                        "description": getattr(t, "description", "")
                    } 
                    for t in tools_response.tools
                ]
            except Exception as e:
                print(f"获取服务端 {server.id} 的工具列表失败: {e}")
                # 如果获取工具失败，视为离线
                is_online = False
                
        # 3. 返回给 Pydantic 模型的数据字典
        return {
            "id": server.id,
            "name": server.name,
            "desc": server.desc,
            "cfg": server.cfg,
            "protocol": server.protocol,
            "is_enabled": server.is_enabled,
            "is_online": is_online,
            "tools": tools_list
        }
    
    # 4. 使用 asyncio.gather 并发处理所有服务端的状态检查
    results = await asyncio.gather(*(fetch_server_status(server) for server in mcp_server_list))
    return results
# 查询 MCP Server 详情
@app_router.get("/mcp_server/{mcp_server_id}", response_model=schemas.MCPServerResponse)
async def get_mcp_server(mcp_server_id: int, db: Session = Depends(get_db)):
    mcp_server = orm.get_mcp_server_by_id_db(db, mcp_server_id)
    if not mcp_server:
        raise HTTPException(status_code=404, detail="MCP server not found")
    return mcp_server




# 更新 MCP Server
@app_router.put("/mcp_server/{mcp_server_id}", response_model=schemas.MCPServerResponse)
async def update_mcp_server(mcp_server_id: int, mcp_server_update: schemas.MCPServerUpdate, db: Session = Depends(get_db)):
    updated_mcp_server = orm.update_mcp_server_db(db, mcp_server_id, mcp_server_update)
    if not updated_mcp_server:
        raise HTTPException(status_code=404, detail="MCP server not found")
    return updated_mcp_server


# 删除MCP Server
@app_router.delete("/mcp_server/{mcp_server_id}", response_model=schemas.MCPServerResponse)
async def delete_mcp_server(mcp_server_id: int, db: Session = Depends(get_db)):
    mcp_server = orm.get_mcp_server_by_id_db(db, mcp_server_id)
    if not mcp_server:
        raise HTTPException(status_code=404, detail="MCP server not found")
    
    orm.delete_mcp_server_db(db, mcp_server_id)
    return mcp_server


# 启用/停用 MCP Server
@app_router.put("/mcp_server/{mcp_server_id}/toggle", response_model=schemas.MCPServerToggleResponse)
async def toggle_mcp_server(mcp_server_id: int, db: Session = Depends(get_db)):
    mcp_server = orm.toggle_mcp_server_db(db, mcp_server_id)
    if not mcp_server:
        raise HTTPException(status_code=404, detail="MCP server not found")
    return mcp_server



# 刷新 MCP Server 的在线状态
@app_router.put("/mcp_server/{mcp_server_id}/refresh", response_model=dict)
async def refresh_mcp_server(mcp_server_id: int, db: Session = Depends(get_db)):
    mcp_server = orm.get_mcp_server_by_id_db(db, mcp_server_id)
    if not mcp_server:
        raise HTTPException(status_code=404, detail="MCP server not found")
    is_online = await connect_and_cache_client(mcp_server)
    return {"is_online": is_online}

@app_router.post("/mcp_server/list_tools")
async def list_tools(con_cfg: schemas.ConnectionCfg, db: Session = Depends(get_db)):
    client = None
    connected = False  # 关键标记：只有连接成功才需要清理
    error_msg = None
    
    try:
        server_params = json.loads(con_cfg.cfg)
        protocol = con_cfg.protocol
        
        client = MCPClient(server_params, protocol)
        await client.connect_to_server()
        connected = True  # 连接成功，标记为需要清理
        
        tools_response = await client.list_tools()
        
        tools_list = [
            {
                "name": tool.name,
                "description": getattr(tool, "description", ""),
                "inputSchema": getattr(tool, "inputSchema", {})
            } 
            for tool in tools_response.tools
        ]
        
        # 成功返回前先清理
        if connected:
            try:
                await client.cleanup()
            except BaseException as ce:
                print(f"⚠️ cleanup 异常（已忽略）: {ce}")
        
        return {"tools": tools_list}
        
    except BaseException as e:
        error_msg = f"Failed to list tools: {str(e)}"
        print(f"❌ {error_msg}")
    
    # 关键：只有连接成功过的才清理。连接失败时，SDK 内部已经自己清理了
    if connected and client is not None:
        try:
            await client.cleanup()
        except BaseException as ce:
            print(f"⚠️ cleanup 异常（已忽略）: {ce}")
    
    return JSONResponse(status_code=500, content={"detail": error_msg})


app.include_router(app_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)