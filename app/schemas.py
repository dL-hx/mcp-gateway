from pydantic import BaseModel
from typing import Optional

class CallToolRequest(BaseModel):
    name: str # 工具名称 格式: "server_name/tool_name"
    arguments: str # 工具参数 JSON 字符串，如 '{"a": 1, "b": 2}'


# 基础字段
class MCPServerBase(BaseModel):
    name: str
    desc: Optional[str] = None
    cfg: str
    protocol: str
    is_enabled: bool = True

class MCPServerUpdate(BaseModel):
    desc: Optional[str] = None
    cfg: Optional[str] = None
    protocol: Optional[str] = None


class MCPServerCreate(BaseModel):
    name: str
    desc: str
    cfg: str
    protocol: str
    is_enabled: bool = True 

class MCPServerToggleResponse(MCPServerCreate):
    is_enabled: bool
    id: int


class ConnectionCfg(BaseModel):
    cfg: str
    protocol: str


# 返回给前端的字段（包含id）
class MCPServerResponse(MCPServerBase):
    id: int
    class Config:
        from_attributes = True # Pydantic v2 (如果是v1请用 orm_mode = True)


class MCPServerWithStatusResponse(MCPServerBase):
    id: int
    is_online: bool = False
    tools:list[dict] = []
    class Config:
        from_attributes = True # Pydantic v2 (如果是v1请用 orm_mode = True)