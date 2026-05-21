#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Create v1.2.5 iteration with requirements in the iteration center."""
import requests
import json

BASE = "http://localhost:8000/api/v2"

def main():
    # 1. Get project
    r = requests.get(f"{BASE}/projects")
    data = r.json()
    projects = data if isinstance(data, list) else data.get("projects", [])
    project_id = projects[0]["id"] if projects else None
    if not project_id:
        r = requests.post(f"{BASE}/projects", json={"name": "recycle-pound", "description": "蓝点新生磅称系统"})
        project_id = r.json()["id"]
    print(f"Project ID: {project_id}")

    # 2. Create iteration v1.2.5
    r = requests.post(f"{BASE}/iterations", json={
        "project_id": project_id,
        "name": "v1.2.5-磅称监控与卸货录像",
        "version": "v1.2.5",
        "description": "磅称管理新增监控实时画面、摄像头位置调整、卸货场视频拍摄、新增仪表品牌顶松",
    })
    it = r.json()
    iter_id = it["id"]
    print(f"Iteration ID: {iter_id}")

    # 3. Requirement 1: 监控实时画面 + 摄像头方向调整
    req1_content = (
        '一、新增[监控]按钮\n'
        '1. 磅称界面 Header 区域新增[监控]按钮(VideoCamera图标), 点击后在右侧展开监控面板\n'
        '1.1 磅称界面和监控弹窗按7:3的比例左右结构展示(main-area vs monitor-sidebar)\n'
        '1.2 当未停留在磅称界面或停留但无操作且监控持续播放5分钟时, 弹出[即将关闭监控]提示\n'
        '   - 提示包含10秒倒计时, 倒计时结束自动关闭监控\n'
        '   - 用户可点击[取消关闭]重新计时5分钟\n'
        '   - 用户可点击[确认关闭]立即关闭监控面板\n\n'
        '二、监控画面自适应\n'
        '2. 根据绑定监控台数(从 /recycle/basic/basicDevice/page 获取设备列表)自动调节每台监控画面尺寸\n'
        '2.1 支持双击放大预览对应摄像头画面(1024x768 或 1280x1024 像素)\n'
        '2.2 播放地址通过 /recycle/basic/basicDevice/getStream 获取FLV流\n'
        '2.3 视频播放器使用 EzuikitFlv 库(ezuikit-flv), 支持自动播放、无音频模式\n\n'
        '三、摄像头PTZ方向控制\n'
        '3. 放大或非放大时, 鼠标移入摄像头画面区域, 展示上下左右调节按钮\n'
        '3.1 PTZ控制使用mousedown/mouseup模式(按下开始移动, 松开停止)\n'
        '3.2 开始移动调用 /recycle/basic/basicDevice/ptz (参数deviceSerial, direction 0上1下2左3右)\n'
        '3.3 停止移动调用 /recycle/basic/basicDevice/ptzout (参数deviceSerial)\n'
        '3.4 摄像头离线时控制按钮禁用\n\n'
        '四、摄像头状态显示\n'
        '4. 每个摄像头画面左上角浮层显示摄像头名称和在线/离线状态指示灯(绿色/红色圆点)\n'
        '4.1 无视频流时显示占位图(VideoCamera图标 + 暂无摄像头文字)'
    )
    r1 = requests.post(f"{BASE}/iterations/{iter_id}/requirements", json={
        "title": "展示企业绑定监控的实时画面及摄像头位置调整",
        "content": req1_content,
        "risk_level": "P0",
    })
    print(f"Req1 [{r1.status_code}]: {r1.json().get('id', 'error')}")

    # 4. Requirement 2: 卸货场视频拍摄
    req2_content = (
        '一、设置-卸货拍摄时长\n'
        '1. 磅称界面设置新增[卸货拍摄时长]字段\n'
        '1.1 支持手动录入正整数5-600, 默认值20\n'
        '1.2 单位默认S, 不可编辑(el-input append插槽显示)\n'
        '1.3 失焦时自动校验范围: <5修正为5, >600修正为600, 非整数向下取整\n'
        '1.4 保存设置时校验: 必须为正整数且在5-600范围内\n\n'
        '二、卸货录像按钮\n'
        '2. 磅称界面底部操作区新增[卸货录像]按钮(需权限bound:video)\n'
        '2.1 点击按钮触发卸货区摄像头的视频拍摄\n'
        '2.2 调用API: POST /recycle/basic/basicDevice/record\n'
        '2.3 拍摄时长根据设置中的recordingTime秒数自动截断\n'
        '2.4 完成拍摄后将视频保存至照片区域及过磅记录的照片/视频记录中\n'
        '2.5 视频同步至ERP对应单据的入库/物流附件中(参照过磅照片处理逻辑)\n\n'
        '三、过磅记录页面更名\n'
        '3. 过磅记录的[过磅照片]列更名为[过磅&卸货影像]\n'
        '3.1 新增[卸货影像]列, 展示mainAttachmentFiles中的视频缩略图\n'
        '3.2 点击视频缩略图在新窗口播放(50%屏幕尺寸, 居中显示)\n'
        '3.3 播放窗口包含关闭按钮, 支持自动播放和循环\n\n'
        '四、过毛重/皮重时自动拍照\n'
        '4. 手动或自动过毛重/过皮重时, 触发磅秤前摄像头和磅秤后摄像头拍照\n'
        '4.1 调用 /recycle/bound/data/capture API获取车牌号和图片\n'
        '4.2 抓拍失败不影响过磅流程, 仅记录日志'
    )
    r2 = requests.post(f"{BASE}/iterations/{iter_id}/requirements", json={
        "title": "新增卸货场视频拍摄功能",
        "content": req2_content,
        "risk_level": "P0",
    })
    print(f"Req2 [{r2.status_code}]: {r2.json().get('id', 'error')}")

    # 5. Requirement 3: 新增仪表品牌顶松
    req3_content = (
        '1. 仪表品牌列表新增[顶松]选项\n'
        '2. 实现顶松品牌协议参数解析\n'
        '3. 串口通信支持顶松协议数据格式\n'
        '4. 重量数据解析遵循顶松协议规范\n'
        '5. WebSocket重量数据推送兼容顶松仪表输出'
    )
    r3 = requests.post(f"{BASE}/iterations/{iter_id}/requirements", json={
        "title": "新增仪表品牌顶松对接",
        "content": req3_content,
        "risk_level": "P1",
    })
    print(f"Req3 [{r3.status_code}]: {r3.json().get('id', 'error')}")

    # 6. Generate test points
    print("\n--- 生成测试点 ---")
    r = requests.post(f"{BASE}/iterations/{iter_id}/test-points/generate")
    tp = r.json()
    print(f"Generated: {tp.get('generated', 0)} test points")

    # 7. Confirm all test points
    print("--- 确认测试点 ---")
    r = requests.get(f"{BASE}/iterations/{iter_id}/test-points")
    tps = r.json().get("test_points", [])
    for t in tps:
        requests.patch(f"{BASE}/iteration-test-points/{t['id']}/confirm", json={"confirmed": True})
    print(f"Confirmed: {len(tps)} test points")

    # 8. Generate test cases
    print("\n--- 生成测试用例 ---")
    r = requests.post(f"{BASE}/iterations/{iter_id}/test-cases/generate")
    tc = r.json()
    print(f"Generated: {tc.get('generated', 0)} test cases")

    # 9. List test cases
    r = requests.get(f"{BASE}/iterations/{iter_id}/test-cases")
    cases = r.json().get("test_cases", [])
    print(f"\n=== 共 {len(cases)} 个测试用例 ===")
    for c in cases:
        print(f"  [{c.get('case_type','?'):10s}] [{c.get('priority','?'):6s}] {c['name']}")

    # 10. Create execution sets
    print("\n--- 创建执行集 ---")
    for t in ["smoke", "iteration", "regression"]:
        r = requests.post(f"{BASE}/iterations/{iter_id}/execution-sets", json={"type": t})
        es = r.json()
        print(f"  {t:12s}: ID={es['id']}, cases={es['case_count']}")

    print(f"\n✅ 迭代 {iter_id} (v1.2.5) 创建完毕，可在前端查看或执行")
    print(f"   前端地址: http://localhost:3000/iterations/{iter_id}")


if __name__ == "__main__":
    main()
