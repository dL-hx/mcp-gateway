import httpx
import uuid

host = "http://localhost:8000"

def test_create_mcp_server():
    # 写死的配置
    json_data = {
        "name": "test_mcp_server",
        "desc": "test_mcp_server description",
        "cfg": '{"key": "value"}',
        "protocol": "sse",
        "is_enabled": True
    }

    response = httpx.post(f"{host}/api/mcp_server", json=json_data)
    print(f"状态码: {response.status_code}")
    
    # 如果出现 500，把后端的错误详情打印出来
    if response.status_code == 500:
        print(f"❌ 后端崩溃了，详情: {response.text}")
        
    assert response.status_code in [200, 400]
    print("创建接口测试完毕")

def test_get_mcp_server():
    # 写死的 URL 路径
    response = httpx.get(f"{host}/api/mcp_server/1")
    print(response.status_code)
    assert response.status_code == 200
    assert response.json()["id"] == 1
    print("详情查询测试完毕")


def test_get_mcp_server_list():
    # 写死的 URL 路径
    response = httpx.get(f"{host}/api/mcp_server")
    print(response.status_code)
    assert response.status_code == 200
    
    list_data = response.json()
    assert len(list_data) > 0
    assert list_data[0]["name"] == "test_mcp_server"
    print("列表查询测试完毕")


def test_update_mcp_server():
    # 完全按照截图的硬编码风格
    json_data = {"desc": "test_mcp_server_update", "cfg": "{}", "protocol": "stdio"}
    
    # URL 直接写死 1
    response = httpx.put(f"{host}/api/mcp_server/1", json=json_data)
    
    print(response.status_code)
    assert response.status_code == 200
    assert response.json()["desc"] == "test_mcp_server_update"
    print("更新接口测试完毕")

def test_delete_mcp_server():
    # 先临时创建一个用来删
    unique_name = f"test_mcp_server_{uuid.uuid4().hex[:6]}"
    json_data = {
        "name": unique_name, 
        "desc": "test delete", 
        "cfg": "{}", 
        "protocol": "sse"
    }
    
    # 创建拿到 ID
    create_res = httpx.post(f"{host}/api/mcp_server", json=json_data)
    assert create_res.status_code == 200
    temp_id = create_res.json()["id"]

    # 执行删除
    response = httpx.delete(f"{host}/api/mcp_server/{temp_id}")
    print(f"删除状态码: {response.status_code}")
    assert response.status_code == 200

    # 再次查询，验证是否已消失（应该返回 404）
    get_res = httpx.get(f"{host}/api/mcp_server/{temp_id}")
    assert get_res.status_code == 404
    print("删除接口测试完毕")
def test_toggle_mcp_server():
    # 1. 创建/获取测试数据
    json_data = {
        "name": "test_mcp_server_toggle",
        "desc": "test_mcp_server",
        "cfg": "{}",
        "protocol": "stdio"
    }
    create_res = httpx.post(f"{host}/api/mcp_server", json=json_data)
    print(f"创建状态码: {create_res.status_code}")
    assert create_res.status_code in [200, 400]

    # 2. 拿到它的真实 ID (如果创建成功直接用返回值，如果已存在就去列表里找)
    if create_res.status_code == 200:
        target_id = create_res.json()["id"]
    else:
        # 如果已存在，通过列表找到它的 ID
        list_res = httpx.get(f"{host}/api/mcp_server")
        target_id = next(item["id"] for item in list_res.json() if item["name"] == "test_mcp_server_toggle")
    
    print(f"准备切换的 ID: {target_id}")

    # 3. 获取切换前的状态
    get_res = httpx.get(f"{host}/api/mcp_server/{target_id}")
    assert get_res.status_code == 200
    before_state = get_res.json()["is_enabled"]
    print(f"切换前状态: {before_state}")

    # 4. 执行切换操作（使用动态的 target_id）
    response = httpx.put(f"{host}/api/mcp_server/{target_id}/toggle")
    print(f"切换状态码: {response.status_code}")
    assert response.status_code == 200

    # 5. 根据切换前的状态进行动态断言
    after_state = response.json()["is_enabled"]
    print(f"切换后状态: {after_state}")

    if before_state is True:
        assert after_state is False
    else:
        assert after_state is True
        
    print("切换状态测试完毕")


def test_list_tools():
    # 1. 准备临时配置（直接传 URL，不依赖数据库里的 ID）
    json_data = {
        "cfg": "{\"url\": \"http://localhost:8002/mcp\"}",
        "protocol": "streamable http"
    }
    
    # 2. 发起请求
    response = httpx.post(f"{host}/api/mcp_server/list_tools", json=json_data)
    print(f"获取工具列表状态码: {response.status_code}")
    
    # 3. 断言
    assert response.status_code == 200, f"期望 200，实际 {response.status_code}, 详情: {response.text}"
    res_json = response.json()
    assert "tools" in res_json
    tools = res_json["tools"]
    assert isinstance(tools, list)
    
    # 4. 验证是否成功拿到本地的加减乘除工具
    tool_names = [t["name"] for t in tools]
    print(f"获取到的工具: {tool_names}")
    assert "add" in tool_names
    assert "subtract" in tool_names
    assert "multiply" in tool_names
    assert "divide" in tool_names
    print("获取工具列表测试完毕")

def test_list_tools_connection_refused():
    """测试连接失败的情况，确保返回标准 JSON 格式的错误"""
    json_data = {
        "cfg": "{\"url\": \"http://localhost:9999/mcp\"}",
        "protocol": "streamable http"
    }
    response = httpx.post(f"{host}/api/mcp_server/list_tools", json=json_data)
    print(f"错误连接状态码: {response.status_code}")
    print(f"错误响应内容: {response.text[:200]}")
    
    assert response.status_code == 500
    
    # 现在应该稳定返回 JSON
    res_json = response.json()
    assert "detail" in res_json
    assert "Failed to list tools" in res_json["detail"]
    print("✅ 错误响应为标准 JSON 格式")
    print("错误连接测试完毕")

def test_call_tool_add():
    """测试调用 MCP 工具的 add 方法：10 + 20 = 30"""

    # ============ 步骤 1: 确保数据库里有 local-math-server 记录 ============
    server_payload = {
        "name": "local-math-server",
        "desc": "本地计算服务",
        "cfg": "{\"url\": \"http://localhost:8002/mcp\"}",
        "protocol": "streamable http",
        "is_enabled": True
    }
    create_res = httpx.post(f"{host}/api/mcp_server", json=server_payload)
    print(f"创建 MCP Server 状态码: {create_res.status_code}")
    # 200 = 新建成功, 400 = 已存在, 都算通过

    # ============ 步骤 2: 通过列表接口找到它的真实 ID ============
    list_res = httpx.get(f"{host}/api/mcp_server")
    assert list_res.status_code == 200
    servers = list_res.json()
    target = next((s for s in servers if s["name"] == "local-math-server"), None)
    assert target is not None, "❌ 未找到 local-math-server"
    server_id = target["id"]
    print(f"local-math-server 的 ID: {server_id}")

    # ============ 步骤 3: 刷新状态，触发连接缓存 ============
    refresh_res = httpx.put(f"{host}/api/mcp_server/{server_id}/refresh")
    assert refresh_res.status_code == 200
    assert refresh_res.json()["is_online"] is True, "❌ MCP Server 未上线，请检查 8002 端口是否在运行"
    print(f"✅ MCP Server 已上线")

    # ============ 步骤 4: 调用 add 工具 ============
    call_payload = {
        "name": "local-math-server/add",
        "arguments": "{\"a\": 10, \"b\": 20}"
    }
    response = httpx.post(f"{host}/api/mcp_server/call_tool", json=call_payload)
    print(f"调用 add 状态码: {response.status_code}")
    print(f"响应: {response.text}")

    assert response.status_code == 200, f"期望 200, 实际 {response.status_code}, 详情: {response.text}"
    res_json = response.json()
    assert "content" in res_json
    assert len(res_json["content"]) > 0
    # 结果中应包含 30
    text_content = res_json["content"][0]["text"]
    assert "30" in text_content, f"期望 30, 实际: {text_content}"
    print("✅ add 工具调用测试通过")

    # ============ 步骤 5: 测试 divide 工具（带参数校验） ============
    divide_payload = {
        "name": "local-math-server/divide",
        "arguments": "{\"a\": 100, \"b\": 4}"
    }
    response = httpx.post(f"{host}/api/mcp_server/call_tool", json=divide_payload)
    print(f"调用 divide 状态码: {response.status_code}")
    assert response.status_code == 200
    res_json = response.json()
    assert "25" in res_json["content"][0]["text"], f"期望 25, 实际: {res_json['content'][0]['text']}"
    print("✅ divide 工具调用测试通过")


def test_call_tool_server_not_found():
    """测试调用不存在的 MCP Server"""
    call_payload = {
        "name": "non-existent-server/add",
        "arguments": "{\"a\": 1, \"b\": 2}"
    }
    response = httpx.post(f"{host}/api/mcp_server/call_tool", json=call_payload)
    print(f"不存在的 Server 状态码: {response.status_code}")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]
    print("✅ 不存在的 Server 测试通过")


def test_call_tool_invalid_name():
    """测试非法工具名格式"""
    call_payload = {
        "name": "invalid-format-without-slash",
        "arguments": "{}"
    }
    response = httpx.post(f"{host}/api/mcp_server/call_tool", json=call_payload)
    print(f"非法工具名状态码: {response.status_code}")
    assert response.status_code == 400
    assert "Invalid tool name" in response.json()["detail"]
    print("✅ 非法工具名测试通过")



if __name__ == "__main__":
    print("--- 测试创建接口 ---")
    test_create_mcp_server()
    
    print("\n--- 测试查询详情接口 ---")
    test_get_mcp_server()
    
    print("\n--- 测试查询列表接口 ---")
    test_get_mcp_server_list()
    
    print("\n--- 测试更新接口 ---")
    test_update_mcp_server()

    print("\n--- 5. 测试删除接口 ---")
    test_delete_mcp_server()

    print("\n--- 6. 测试切换接口 ---")
    test_toggle_mcp_server()

    # 新增的测试调用
    print("\n--- 7. 测试获取工具列表 ---")
    test_list_tools()
    
    print("\n--- 8. 测试获取工具列表（连接失败） ---")
    test_list_tools_connection_refused()

    print("\n--- 9. 测试调用工具（add + divide） ---")
    test_call_tool_add()

    print("\n--- 10. 测试调用工具（Server 不存在） ---")
    test_call_tool_server_not_found()

    print("\n--- 11. 测试调用工具（非法名称） ---")
    test_call_tool_invalid_name()

    
    print("\n测试执行完毕！")