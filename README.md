# MCP ChatBot 项目

> 能够实现 MCP 调用的对话机器人

## 接口梳理

### MCP Server 管理

- [x] **创建 MCP Server**
- [x] **删除 MCP Server**
- [x] **更新 MCP Server**
- [x] **查询 MCP Server 列表**
- [x] **查询 MCP Server 的详情**
- [x] **启用 / 停用 MCP Server**（让大模型更加精准地找到需要调用的函数）

> 整合mcp client 与mcp server
- [x]  **刷新 MCP Server 的在线状态**（相当于重新连接 MCP Server）

```
mcpclient连接 mcp server, 连接之后，在前端展示其连接状态

获取mcp 状态，获取mcp 能够调用的工具，mcp server函数调用功能实现
```

### Tools 管理

- [x]  **查询 MCP Server 的 tools 列表** 不是通过id获取，而是通过配置获取工具列表
- [x]  **调用 MCP Server 的 tool**

将mcp server这里配置的工具，与模型广场中配置的mcp进行打通，完成函数的调用功能

将mcp返回的数据，作为上下文