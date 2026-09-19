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

    print("\n测试执行完毕！")