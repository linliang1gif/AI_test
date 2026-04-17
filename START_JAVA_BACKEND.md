# 启动Java后端服务指南

## 问题诊断结果

✅ 诊断完成！Java后端服务当前**未运行**在端口8194。

## 启动步骤

### 方式1：使用命令行（推荐）

1. 打开命令行窗口
2. 进入项目目录：
```bash
cd "D:\360Downloads\蓝点\recycle-server-feature-1.2.2 (1)\recycle-server-feature-1.2.2"
```

3. 编译项目（首次运行或代码有更新时）：
```bash
mvn clean install -DskipTests
```

4. 进入业务模块目录：
```bash
cd recycle\recycle-business
```

5. 启动服务：
```bash
mvn spring-boot:run
```

### 方式2：使用IDEA（最简单）

1. 用IntelliJ IDEA打开项目目录：
   ```
   D:\360Downloads\蓝点\recycle-server-feature-1.2.2 (1)\recycle-server-feature-1.2.2
   ```

2. 等待Maven依赖下载完成

3. 找到主启动类（通常在 `recycle-business` 模块下）：
   - 路径类似：`recycle/recycle-business/src/main/java/.../Application.java`
   - 或者：`RecycleBusinessApplication.java`

4. 右键点击主类 → Run 'Application'

### 方式3：使用启动脚本

我已经为你创建了一个启动脚本 `start_java_backend.bat`，双击运行即可。

## 验证服务是否启动成功

### 方法1：检查端口
打开新的命令行窗口，运行：
```bash
netstat -ano | findstr :8194
```
如果看到 `LISTENING`，说明服务已启动。

### 方法2：访问Swagger文档
在浏览器中打开：
- http://localhost:8194/recycle/swagger-ui.html
- 或：http://localhost:8194/recycle/doc.html

如果能看到API文档页面，说明服务正常运行。

### 方法3：运行诊断脚本
```bash
cd "G:\AI项目\ai测试"
py test_java_backend.py
```

## 启动成功后的配置

服务启动成功后，在AI测试平台中：

1. 打开 API管理 页面
2. 点击任意API的 ▶️ 执行按钮
3. 在弹出的对话框中：
   - 基础URL改为：`http://localhost:8194/recycle`
   - 取消勾选 "🎭 Mock模式"
   - 编辑请求参数
   - 点击"执行"

## 常见问题

### Q: Maven命令找不到？
A: 需要安装Maven并配置环境变量。或者使用IDEA，它自带Maven。

### Q: 端口8194被占用？
A: 
1. 查看是哪个程序占用：`netstat -ano | findstr :8194`
2. 结束占用的进程，或修改配置文件改用其他端口

### Q: 启动报错缺少数据库连接？
A: 
1. 检查MySQL/MariaDB是否已启动
2. 检查Redis是否已启动
3. 查看配置文件：`recycle/recycle-business/src/main/resources/application-test.yml`

### Q: 暂时无法启动Java服务怎么办？
A: 可以使用Mock模式测试：
1. 在API执行对话框中勾选 "🎭 Mock模式"
2. 点击"执行"会返回模拟数据
3. 可以测试"保存为测试用例"等功能

## 下一步

服务启动后，你就可以：
1. ✅ 在AI测试平台中执行真实的API请求
2. ✅ 查看真实的响应数据
3. ✅ 将执行结果保存为测试用例
4. ✅ 进行完整的API测试流程
