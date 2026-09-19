from sqlalchemy import Column, Integer, String, Boolean
from .database import Base

class MCPServer(Base):
    __tablename__ = "mcp_servers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, index=True, nullable=False)
    desc = Column(String, nullable=True)
    cfg = Column(String, nullable=False) # 建议使用SQLAlchemy的JSON类型
    protocol = Column(String, nullable=False)
    is_enabled = Column(Boolean, default=True, nullable=False)