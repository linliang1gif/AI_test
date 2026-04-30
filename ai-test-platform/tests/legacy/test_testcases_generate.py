#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试 /api/testcases/generate 接口
"""

import requests

def test_testcases_generate():
    """测试测试用例生成接口"""
    
    print("🧪 测试 /api/testcases/generate 接口\n")
    
    # 创建测试文档内容
    test_content = """
电商平台需求文档

1. 用户管理模块
   - 用户注册功能
   - 用户登录功能
   - 密码找回功能
   - 个人信息修改

2. 商品管理模块
   - 商品搜索功能
   - 商品详情查看
   - 商品分类浏览
   - 商品收藏功能

3. 购物车模块
   - 添加商品到购物车
   - 修改购物车商品数量
   - 删除购物车商品
   - 清空购物车

4. 订单管理模块
   - 创建订单
   - 订单支付
   - 订单查询
   - 订单取消

5. 支付模块
   - 支付宝支付
   - 微信支付
   - 银行卡支付
    """
    
    # 准备文件
    files = {
        'file': ('电商平台需求.txt', test_content.encode('utf-8'), 'text/plain')
    }
    
    try:
        print("📤 上传需求文档并生成测试用例...")
        response = requests.post(
            'http://127.0.0.1:8081/api/testcases/generate',
            files=files,
            timeout=30
        )
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ 测试用例生成成功!")
            print(f"生成数量: {result.get('count', 0)}")
            print(f"消息: {result.get('message', '')}")
            
            if 'testCases' in result:
                print(f"\n生成的测试用例:")
                for i, tc in enumerate(result['testCases'][:5], 1):  # 只显示前5个
                    print(f"\n{i}. {tc.get('title', '')}")
                    print(f"   优先级: {tc.get('priority', '')}")
                    print(f"   模块: {tc.get('module', '')}")
                    if len(result['testCases']) > 5:
                        print(f"\n... 还有 {len(result['testCases']) - 5} 个测试用例")
        else:
            print(f"\n❌ 请求失败")
            print(f"响应: {response.text}")
            
    except Exception as e:
        print(f"\n❌ 错误: {e}")


if __name__ == "__main__":
    test_testcases_generate()
