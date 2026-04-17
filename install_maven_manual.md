# Maven 手动安装指南（网络下载失败时使用）

## 问题说明

自动下载Maven失败，可能原因：
- 网络连接问题
- 防火墙/代理设置
- 镜像站点暂时不可用

## 解决方案：手动下载安装

### 步骤1：下载Maven

请访问以下任一网址下载Maven：

**选项1：百度网盘（推荐，速度快）**
- 搜索：apache-maven-3.9.6-bin.zip
- 或使用其他网盘分享

**选项2：官方网站**
- https://maven.apache.org/download.cgi
- 找到 `apache-maven-3.9.6-bin.zip` 点击下载

**选项3：国内镜像**
- 阿里云：https://mirrors.aliyun.com/apache/maven/maven-3/3.9.6/binaries/apache-maven-3.9.6-bin.zip
- 清华：https://mirrors.tuna.tsinghua.edu.cn/apache/maven/maven-3/3.9.6/binaries/apache-maven-3.9.6-bin.zip
- 华为云：https://mirrors.huaweicloud.com/apache/maven/maven-3/3.9.6/binaries/apache-maven-3.9.6-bin.zip

**选项4：使用下载工具**
- 使用迅雷、IDM等下载工具
- 复制上面的链接进行下载

### 步骤2：解压Maven

1. 将下载的 `apache-maven-3.9.6-bin.zip` 解压

2. 将解压后的文件夹移动到：
   ```
   C:\Program Files\Apache\Maven
   ```

3. 确保目录结构是：
   ```
   C:\Program Files\Apache\Maven\
     ├── bin\
     │   └── mvn.cmd
     ├── boot\
     ├── conf\
     ├── lib\
     └── ...
   ```

### 步骤3：配置环境变量

我已经为你准备了配置脚本，运行它即可：

```powershell
cd "G:\AI项目\ai测试"
.\configure_maven_env.ps1
```

或者手动配置：

1. 右键"此电脑" → "属性" → "高级系统设置" → "环境变量"

2. 在"系统变量"中，点击"新建"：
   - 变量名：`MAVEN_HOME`
   - 变量值：`C:\Program Files\Apache\Maven`

3. 编辑"系统变量"中的 `Path`，添加：
   ```
   %MAVEN_HOME%\bin
   ```

4. 点击"确定"保存

### 步骤4：验证安装

1. 关闭所有PowerShell窗口

2. 重新打开PowerShell

3. 运行：
   ```powershell
   mvn -version
   ```

4. 如果看到Maven版本信息，说明安装成功！

### 步骤5：配置阿里云镜像（加速）

运行配置脚本：
```powershell
cd "G:\AI项目\ai测试"
.\configure_maven_mirror.ps1
```

## 快速验证

安装完成后运行：
```powershell
cd "G:\AI项目\ai测试"
py verify_maven_installation.py
```

## 下一步

Maven安装成功后，启动Java后端：
```powershell
cd "G:\AI项目\ai测试"
.\start_java_backend.bat
```

## 需要帮助？

如果遇到问题：
1. 查看 MAVEN_INSTALL_GUIDE.md 详细说明
2. 或者使用IDEA（自带Maven，不需要单独安装）
3. 或者先用Mock模式测试AI测试平台功能
