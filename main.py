from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from app import schemas, models, orm
from app.database import engine, get_db, Base
from typing import List

load_dotenv()

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


# 查询 MCP Server 列表
@app_router.get("/mcp_server", response_model=List[schemas.MCPServerResponse])
async def get_mcp_server_list(db: Session = Depends(get_db)):
    mcp_server_list = orm.get_mcp_server_list_db(db)
    return mcp_server_list

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





app.include_router(app_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)