# Maven 安装和配置指南

## 🚀 快速安装（推荐）

### 方式1：使用自动安装脚本 ⭐⭐⭐

我已经为你创建了自动安装脚本，一键完成所有配置！

1. 右键点击 PowerShell，选择"以管理员身份运行"

2. 运行安装脚本：
```powershell
cd "G:\AI项目\ai测试"
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\install_maven.ps1
```

脚本会自动：
- ✅ 检查Java环境
- ✅ 下载Maven（使用国内镜像加速）
- ✅ 解压到 `C:\Program Files\Apache\Maven`
- ✅ 配置环境变量（MAVEN_HOME 和 PATH）
- ✅ 配置阿里云镜像加速
- ✅ 创建 settings.xml 配置文件

3. 安装完成后，关闭并重新打开PowerShell

4. 验证安装：
```powershell
mvn -version
```

看到Maven版本信息就说明安装成功了！

## 📋 手动安装步骤

如果自动脚本失败，可以手动安装：

### 步骤1：下载Maven

访问以下任一地址下载：
- 官方：https://maven.apache.org/download.cgi
- 阿里云镜像：https://mirrors.aliyun.com/apache/maven/maven-3/3.9.6/binaries/
- 清华镜像：https://mirrors.tuna.tsinghua.edu.cn/apache/maven/maven-3/3.9.6/binaries/

下载文件：`apache-maven-3.9.6-bin.zip`

### 步骤2：解压Maven

将下载的zip文件解压到：
```
C:\Program Files\Apache\Maven
```

解压后目录结构应该是：
```
C:\Program Files\Apache\Maven\
  ├── bin\
  ├── boot\
  ├── conf\
  ├── lib\
  └── ...
```

### 步骤3：配置环境变量

1. 右键"此电脑" → "属性" → "高级系统设置" → "环境变量"

2. 在"系统变量"中，点击"新建"：
   - 变量名：`MAVEN_HOME`
   - 变量值：`C:\Program Files\Apache\Maven`

3. 编辑"系统变量"中的 `Path`，添加：
   ```
   %MAVEN_HOME%\bin
   ```

4. 点击"确定"保存所有更改

### 步骤4：配置Maven镜像（加速下载）

1. 打开文件：`C:\Users\你的用户名\.m2\settings.xml`
   - 如果文件不存在，创建这个文件

2. 复制以下内容到文件中：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<settings xmlns="http://maven.apache.org/SETTINGS/1.0.0"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
          xsi:schemaLocation="http://maven.apache.org/SETTINGS/1.0.0 
          http://maven.apache.org/xsd/settings-1.0.0.xsd">
    
    <!-- 本地仓库路径 -->
    <localRepository>C:\Users\你的用户名\.m2\repository</localRepository>
    
    <!-- 镜像配置 - 使用阿里云加速 -->
    <mirrors>
        <mirror>
            <id>aliyun-maven</id>
            <mirrorOf>central</mirrorOf>
            <name>阿里云公共仓库</name>
            <url>https://maven.aliyun.com/repository/public</url>
        </mirror>
        <mirror>
            <id>aliyun-spring</id>
            <mirrorOf>spring</mirrorOf>
            <name>阿里云Spring仓库</name>
            <url>https://maven.aliyun.com/repository/spring</url>
        </mirror>
    </mirrors>
    
    <!-- 配置文件 -->
    <profiles>
        <profile>
            <id>jdk-1.8</id>
            <activation>
                <activeByDefault>true</activeByDefault>
                <jdk>1.8</jdk>
            </activation>
            <properties>
                <maven.compiler.source>1.8</maven.compiler.source>
                <maven.compiler.target>1.8</maven.compiler.target>
                <maven.compiler.compilerVersion>1.8</maven.compiler.compilerVersion>
            </properties>
        </profile>
    </profiles>
</settings>
```

3. 保存文件

### 步骤5：验证安装

1. 打开新的PowerShell窗口（必须是新窗口）

2. 运行：
```powershell
mvn -version
```

3. 应该看到类似输出：
```
Apache Maven 3.9.6
Maven home: C:\Program Files\Apache\Maven
Java version: 1.8.0_xxx
```

## ✅ 验证脚本

我创建了一个验证脚本，运行它来检查Maven是否正确安装：

```powershell
cd "G:\AI项目\ai测试"
py verify_maven_installation.py
```

## 🎯 安装成功后的下一步

Maven安装成功后，就可以启动Java后端服务了：

```powershell
# 1. 进入项目目录
cd "D:\360Downloads\蓝点\recycle-server-feature-1.2.2 (1)\recycle-server-feature-1.2.2"

# 2. 编译项目
mvn clean install -DskipTests

# 3. 启动服务
cd recycle\recycle-business
mvn spring-boot:run
```

或者直接运行启动脚本：
```powershell
cd "G:\AI项目\ai测试"
.\start_java_backend.bat
```

## ⚠️ 常见问题

### Q: PowerShell提示"无法加载文件，因为在此系统上禁止运行脚本"？

A: 运行以下命令允许脚本执行：
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Q: 下载速度很慢？

A: 
1. 使用自动安装脚本（已配置国内镜像）
2. 或手动从阿里云/清华镜像下载

### Q: mvn命令找不到？

A: 
1. 确认环境变量配置正确
2. 关闭并重新打开PowerShell窗口
3. 运行 `$env:Path` 检查PATH中是否包含Maven

### Q: 编译项目时下载依赖很慢？

A: 确保已配置阿里云镜像（settings.xml文件）

### Q: 没有管理员权限怎么办？

A: 
1. 可以安装到用户目录：`C:\Users\你的用户名\Maven`
2. 配置"用户变量"而不是"系统变量"

## 📚 相关文件

- `install_maven.ps1` - 自动安装脚本
- `verify_maven_installation.py` - 验证脚本
- `start_java_backend.bat` - Java服务启动脚本
- `JAVA_BACKEND_CONFIG.md` - Java后端配置说明

## 💡 提示

如果Maven安装遇到困难，也可以：
1. 使用IDEA（自带Maven，不需要单独安装）
2. 或者先用Mock模式测试AI测试平台的功能
