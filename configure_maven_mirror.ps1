# Maven 镜像配置脚本
# 配置阿里云镜像加速Maven依赖下载

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "    Maven 镜像配置工具" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$settingsDir = "$env:USERPROFILE\.m2"
$settingsFile = "$settingsDir\settings.xml"

Write-Host "配置文件位置: $settingsFile" -ForegroundColor Gray
Write-Host ""

# 创建.m2目录
if (-not (Test-Path $settingsDir)) {
    Write-Host "创建配置目录..." -ForegroundColor Green
    New-Item -ItemType Directory -Path $settingsDir -Force | Out-Null
    Write-Host "✅ 目录创建成功" -ForegroundColor Green
}

# 备份现有配置
if (Test-Path $settingsFile) {
    $backupFile = "$settingsFile.backup.$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    Write-Host "备份现有配置..." -ForegroundColor Yellow
    Copy-Item -Path $settingsFile -Destination $backupFile
    Write-Host "✅ 备份保存到: $backupFile" -ForegroundColor Green
    Write-Host ""
}

# 创建settings.xml
Write-Host "生成配置文件..." -ForegroundColor Green

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
        <mirror>
            <id>aliyun-google</id>
            <mirrorOf>google</mirrorOf>
            <name>阿里云Google仓库</name>
            <url>https://maven.aliyun.com/repository/google</url>
        </mirror>
        <mirror>
            <id>aliyun-gradle-plugin</id>
            <mirrorOf>gradle-plugin</mirrorOf>
            <name>阿里云Gradle插件仓库</name>
            <url>https://maven.aliyun.com/repository/gradle-plugin</url>
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
                <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
            </properties>
        </profile>
    </profiles>
</settings>
"@

try {
    Set-Content -Path $settingsFile -Value $settingsContent -Encoding UTF8
    Write-Host "✅ 配置文件创建成功" -ForegroundColor Green
} catch {
    Write-Host "❌ 创建配置文件失败: $_" -ForegroundColor Red
    Read-Host "按Enter键退出"
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "    配置完成！" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "已配置的镜像:" -ForegroundColor Green
Write-Host "  ✅ 阿里云公共仓库" -ForegroundColor White
Write-Host "  ✅ 阿里云Spring仓库" -ForegroundColor White
Write-Host "  ✅ 阿里云Google仓库" -ForegroundColor White
Write-Host "  ✅ 阿里云Gradle插件仓库" -ForegroundColor White
Write-Host ""

Write-Host "本地仓库位置:" -ForegroundColor Green
Write-Host "  $env:USERPROFILE\.m2\repository" -ForegroundColor White
Write-Host ""

Write-Host "现在可以使用Maven下载依赖，速度会大大提升！" -ForegroundColor Green
Write-Host ""

Read-Host "按Enter键退出"
