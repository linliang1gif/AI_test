# Java后端服务配置说明

## 🔍 诊断结果

✅ **已完成诊断**：Java后端服务当前**未运行**在端口8194

这就是为什么API执行失败显示"连接失败，请检查URL是否正确"的原因。

## 服务信息

- **项目名称**: Recycle Server  
- **技术栈**: Spring Boot + Maven
- **服务端口**: 8194
- **Context Path**: /recycle
- **完整基础URL**: `http://localhost:8194/recycle`
- **项目位置**: `D:\360Downloads\蓝点\recycle-server-feature-1.2.2 (1)\recycle-server-feature-1.2.2`

## 🚀 快速启动（3种方式）

### 方式1：使用启动脚本（最简单）⭐

我已经为你创建了启动脚本，双击运行即可：

```
G:\AI项目\ai测试\start_java_backend.bat
```

脚本会自动：
- 检查Java和Maven环境
- 提供3种启动选项（快速/完整/仅启动）
- 显示服务信息和访问地址

### 方式2：使用IDEA（推荐）⭐⭐⭐

1. 用IntelliJ IDEA打开项目：
   ```
   D:\360Downloads\蓝点\recycle-server-feature-1.2.2 (1)\recycle-server-feature-1.2.2
   ```

2. 等待Maven依赖下载完成

3. 找到主启动类（在 `recycle-business` 模块下）：
   - 路径：`recycle/recycle-business/src/main/java/.../Application.java`
   - 或：`RecycleBusinessApplication.java`

4. 右键点击主类 → Run 'Application'

### 方式3：使用命令行

```bash
# 1. 进入项目目录
cd "D:\360Downloads\蓝点\recycle-server-feature-1.2.2 (1)\recycle-server-feature-1.2.2"

# 2. 编译项目（首次或有更新时）
mvn clean install -DskipTests

# 3. 进入业务模块
cd recycle\recycle-business

# 4. 启动服务
mvn spring-boot:run
```

## ✅ 验证服务是否启动成功

### 方法1：运行诊断脚本
```bash
cd "G:\AI项目\ai测试"
py test_java_backend.py
```

如果看到 ✅ 状态码: 200，说明服务已成功启动。

### 方法2：访问Swagger文档
在浏览器中打开：
- http://localhost:8194/recycle/swagger-ui.html
- 或：http://localhost:8194/recycle/doc.html

### 方法3：检查端口
```bash
netstat -ano | findstr :8194
```
看到 `LISTENING` 说明服务在运行。

## 🎯 在AI测试平台中使用

服务启动成功后：

### 1. 修改API执行器的基础URL

在API执行对话框中，将基础URL改为：
```
http://localhost:8194/recycle
```

### 2. API路径说明

从Swagger导入的API路径（如 `/basic/basicCurrency/page`）会自动拼接到基础URL后面：
- 完整URL: `http://localhost:8194/recycle/basic/basicCurrency/page`

### 3. 测试步骤

1. ✅ 启动Java后端服务（端口8194）
2. ✅ 在AI测试平台的API管理页面
3. ✅ 点击任意API的▶️按钮
4. ✅ 修改基础URL为 `http://localhost:8194/recycle`
5. ✅ 取消勾选"Mock模式"
6. ✅ 编辑请求参数
7. ✅ 点击"执行"
8. ✅ 查看真实响应结果
9. ✅ 点击"保存为测试用例"

### 4. 验证服务是否启动

运行诊断脚本：
```bash
cd "G:\AI项目\ai测试"
py test_java_backend.py
```

或访问Swagger文档：
```
http://localhost:8194/recycle/swagger-ui.html
```

## ⚠️ 常见问题

### Q: 连接失败怎么办？
A: 
1. ✅ 确认Java后端服务已启动（运行 `py test_java_backend.py` 检查）
2. ✅ 检查端口8194是否被占用：`netstat -ano | findstr :8194`
3. ✅ 确认基础URL配置正确：`http://localhost:8194/recycle`
4. ✅ 查看Java服务控制台是否有错误日志

### Q: Maven命令找不到？
A: 
- 需要安装Maven并配置环境变量
- 或者使用IDEA（自带Maven）
- 或者双击运行 `start_java_backend.bat` 脚本

### Q: 端口8194被占用？
A: 
1. 查看占用进程：`netstat -ano | findstr :8194`
2. 结束占用的进程
3. 或修改配置文件改用其他端口

### Q: 请求超时怎么办？
A:
1. ✅ 检查数据库（MySQL/MariaDB）是否已启动
2. ✅ 检查Redis是否已启动
3. ✅ 查看Java后端日志
4. ✅ 检查配置文件：`recycle/recycle-business/src/main/resources/application-test.yml`

### Q: 认证失败怎么办？
A: 某些API可能需要登录token：
1. 先调用登录接口获取token
2. 在请求头中添加token
3. 或者使用Mock模式测试

### Q: 暂时无法启动Java服务怎么办？
A: 可以使用Mock模式测试：
1. 在API执行对话框中勾选"🎭 Mock模式"
2. 点击"执行"会返回模拟的成功响应
3. 可以测试"保存为测试用例"等功能
4. 等Java服务准备好后再切换到真实模式

## 📋 相关文件

- `START_JAVA_BACKEND.md` - 详细启动指南
- `start_java_backend.bat` - 一键启动脚本
- `test_java_backend.py` - 服务诊断脚本

## 🎯 下一步

服务启动后，你就可以：
1. ✅ 在AI测试平台中执行真实的API请求
2. ✅ 查看真实的响应数据和状态码
3. ✅ 测试响应时间和性能
4. ✅ 将执行结果保存为测试用例
5. ✅ 进行完整的API测试流程
6. ✅ 生成测试报告
