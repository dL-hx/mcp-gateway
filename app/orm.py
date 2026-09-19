from sqlalchemy.orm import Session
from . import models, schemas

# 根据 name 查询 MCP Server
def get_mcp_server_db(db: Session, name: str):
    return db.query(models.MCPServer).filter(models.MCPServer.name == name).first()


# 创建 MCP Server
def create_mcp_server_db(db: Session, mcp_server: schemas.MCPServerCreate):
    db_mcp_server = models.MCPServer(
        name=mcp_server.name,
        desc=mcp_server.desc,
        cfg=mcp_server.cfg,
        protocol=mcp_server.protocol,
        is_enabled=mcp_server.is_enabled
    )
    db.add(db_mcp_server)
    db.commit()
    db.refresh(db_mcp_server)
    return db_mcp_server


# 根据 ID 查询 MCP Server
def get_mcp_server_by_id_db(db: Session, mcp_server_id: int):
    return db.query(models.MCPServer).filter(models.MCPServer.id == mcp_server_id).first()

# 查询 MCP Server 列表
def get_mcp_server_list_db(db: Session):
    return db.query(models.MCPServer).all()


def update_mcp_server_db(db: Session, mcp_server_id: int, mcp_server_update: schemas.MCPServerUpdate):
    """更新 MCP Server 数据"""
    mcp_server = get_mcp_server_by_id_db(db, mcp_server_id)
    if mcp_server:
        # 使用 model_dump(exclude_unset=True) 只更新传入的字段
        update_data = mcp_server_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(mcp_server, key, value)
        
        db.commit()
        db.refresh(mcp_server)
    return mcp_server


def delete_mcp_server_db(db: Session, mcp_server_id: int):
    """删除 MCP Server 数据"""
    mcp_server = get_mcp_server_by_id_db(db, mcp_server_id)
    if mcp_server:
        db.delete(mcp_server)
        db.commit()
    return mcp_server