# Maven 自动安装和配置脚本
# 适用于 Windows PowerShell

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "    Maven 自动安装和配置工具" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查是否以管理员权限运行
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "⚠️  警告: 建议以管理员权限运行此脚本" -ForegroundColor Yellow
    Write-Host "右键点击PowerShell -> 以管理员身份运行" -ForegroundColor Yellow
    Write-Host ""
    $continue = Read-Host "是否继续? (y/n)"
    if ($continue -ne "y") {
        exit
    }
}

# 检查Java环境
Write-Host "1. 检查Java环境..." -ForegroundColor Green
try {
    $javaVersion = java -version 2>&1 | Select-String "version"
    Write-Host "✅ Java已安装: $javaVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ 未检测到Java环境" -ForegroundColor Red
    Write-Host "请先安装JDK: https://www.oracle.com/java/technologies/downloads/" -ForegroundColor Yellow
    exit 1
}

# 检查Maven是否已安装
Write-Host ""
Write-Host "2. 检查Maven是否已安装..." -ForegroundColor Green
try {
    $mvnVersion = mvn -version 2>&1
    Write-Host "✅ Maven已安装:" -ForegroundColor Green
    Write-Host $mvnVersion
    Write-Host ""
    $reinstall = Read-Host "是否重新安装? (y/n)"
    if ($reinstall -ne "y") {
        Write-Host "跳过安装，直接配置环境变量..." -ForegroundColor Yellow
        # 跳转到配置部分
        & $MyInvocation.MyCommand.Path -SkipInstall
        exit
    }
} catch {
    Write-Host "Maven未安装，开始下载..." -ForegroundColor Yellow
}

# 设置安装目录
$installDir = "C:\Program Files\Apache\Maven"
$downloadUrl = "https://dlcdn.apache.org/maven/maven-3/3.9.6/binaries/apache-maven-3.9.6-bin.zip"
$zipFile = "$env:TEMP\apache-maven.zip"

Write-Host ""
Write-Host "3. 下载Maven..." -ForegroundColor Green
Write-Host "下载地址: $downloadUrl" -ForegroundColor Gray
Write-Host "保存位置: $zipFile" -ForegroundColor Gray

try {
    # 使用国内镜像加速下载
    $mirrors = @(
        "https://mirrors.aliyun.com/apache/maven/maven-3/3.9.6/binaries/apache-maven-3.9.6-bin.zip",
        "https://mirrors.tuna.tsinghua.edu.cn/apache/maven/maven-3/3.9.6/binaries/apache-maven-3.9.6-bin.zip",
        $downloadUrl
    )
    
    $downloaded = $false
    foreach ($mirror in $mirrors) {
        try {
            Write-Host "尝试从镜像下载: $mirror" -ForegroundColor Gray
            Invoke-WebRequest -Uri $mirror -OutFile $zipFile -TimeoutSec 30
            $downloaded = $true
            Write-Host "✅ 下载成功" -ForegroundColor Green
            break
        } catch {
            Write-Host "❌ 下载失败，尝试下一个镜像..." -ForegroundColor Yellow
        }
    }
    
    if (-not $downloaded) {
        throw "所有镜像下载失败"
    }
} catch {
    Write-Host "❌ 下载失败: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "请手动下载Maven:" -ForegroundColor Yellow
    Write-Host "1. 访问: https://maven.apache.org/download.cgi" -ForegroundColor Yellow
    Write-Host "2. 下载 apache-maven-3.9.6-bin.zip" -ForegroundColor Yellow
    Write-Host "3. 解压到: $installDir" -ForegroundColor Yellow
    Write-Host "4. 重新运行此脚本配置环境变量" -ForegroundColor Yellow
    exit 1
}

# 创建安装目录
Write-Host ""
Write-Host "4. 创建安装目录..." -ForegroundColor Green
if (Test-Path $installDir) {
    Write-Host "目录已存在，清理旧版本..." -ForegroundColor Yellow
    Remove-Item -Path $installDir -Recurse -Force
}
New-Item -ItemType Directory -Path $installDir -Force | Out-Null
Write-Host "✅ 目录创建成功: $installDir" -ForegroundColor Green

# 解压Maven
Write-Host ""
Write-Host "5. 解压Maven..." -ForegroundColor Green
try {
    Expand-Archive -Path $zipFile -DestinationPath $installDir -Force
    
    # 移动文件到正确位置（解压后会有一个子目录）
    $extractedDir = Get-ChildItem -Path $installDir -Directory | Select-Object -First 1
    if ($extractedDir) {
        $items = Get-ChildItem -Path $extractedDir.FullName
        foreach ($item in $items) {
            Move-Item -Path $item.FullName -Destination $installDir -Force
        }
        Remove-Item -Path $extractedDir.FullName -Force
    }
    
    Write-Host "✅ 解压成功" -ForegroundColor Green
} catch {
    Write-Host "❌ 解压失败: $_" -ForegroundColor Red
    exit 1
}

# 配置环境变量
Write-Host ""
Write-Host "6. 配置环境变量..." -ForegroundColor Green

$mavenHome = $installDir
$mavenBin = "$installDir\bin"

# 设置MAVEN_HOME
[Environment]::SetEnvironmentVariable("MAVEN_HOME", $mavenHome, "Machine")
Write-Host "✅ MAVEN_HOME = $mavenHome" -ForegroundColor Green

# 添加到PATH
$currentPath = [Environment]::GetEnvironmentVariable("Path", "Machine")
if ($currentPath -notlike "*$mavenBin*") {
    $newPath = "$currentPath;$mavenBin"
    [Environment]::SetEnvironmentVariable("Path", $newPath, "Machine")
    Write-Host "✅ 已添加到PATH: $mavenBin" -ForegroundColor Green
} else {
    Write-Host "✅ PATH中已存在Maven" -ForegroundColor Green
}

# 刷新当前会话的环境变量
$env:MAVEN_HOME = $mavenHome
$env:Path = "$env:Path;$mavenBin"

# 配置Maven settings.xml（使用阿里云镜像）
Write-Host ""
Write-Host "7. 配置Maven镜像..." -ForegroundColor Green

$settingsDir = "$env:USERPROFILE\.m2"
$settingsFile = "$settingsDir\settings.xml"

if (-not (Test-Path $settingsDir)) {
    New-Item -ItemType Directory -Path $settingsDir -Force | Out-Null
}

$settingsContent = @"
<?xml version="1.0" encoding="UTF-8"?>
<settings xmlns="http://maven.apache.org/SETTINGS/1.0.0"
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
          xsi:schemaLocation="http://maven.apache.org/SETTINGS/1.0.0 
          http://maven.apache.org/xsd/settings-1.0.0.xsd">
    
    <!-- 本地仓库路径 -->
    <localRepository>$env:USERPROFILE\.m2\repository</localRepository>
    
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
"@

Set-Content -Path $settingsFile -Value $settingsContent -Encoding UTF8
Write-Host "✅ Maven配置文件已创建: $settingsFile" -ForegroundColor Green
Write-Host "   已配置阿里云镜像加速" -ForegroundColor Gray

# 清理临时文件
Write-Host ""
Write-Host "8. 清理临时文件..." -ForegroundColor Green
Remove-Item -Path $zipFile -Force -ErrorAction SilentlyContinue
Write-Host "✅ 清理完成" -ForegroundColor Green

# 验证安装
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "    安装完成！正在验证..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "请关闭当前PowerShell窗口，重新打开后运行以下命令验证:" -ForegroundColor Yellow
Write-Host ""
Write-Host "mvn -version" -ForegroundColor White
Write-Host ""
Write-Host "如果显示Maven版本信息，说明安装成功！" -ForegroundColor Green
Write-Host ""
Write-Host "下一步: 启动Java后端服务" -ForegroundColor Cyan
Write-Host "cd `"D:\360Downloads\蓝点\recycle-server-feature-1.2.2 (1)\recycle-server-feature-1.2.2`"" -ForegroundColor White
Write-Host "mvn clean install -DskipTests" -ForegroundColor White
Write-Host "cd recycle\recycle-business" -ForegroundColor White
Write-Host "mvn spring-boot:run" -ForegroundColor White
Write-Host ""

Read-Host "按Enter键退出"
