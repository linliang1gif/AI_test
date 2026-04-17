# Maven 环境变量配置脚本
# 用于手动下载Maven后配置环境变量

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "    Maven 环境变量配置工具" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查Maven目录是否存在
$mavenHome = "C:\Program Files\Apache\Maven"
$mavenBin = "$mavenHome\bin"
$mvnCmd = "$mavenBin\mvn.cmd"

Write-Host "检查Maven安装目录..." -ForegroundColor Green
if (-not (Test-Path $mavenHome)) {
    Write-Host "❌ Maven目录不存在: $mavenHome" -ForegroundColor Red
    Write-Host ""
    Write-Host "请先完成以下步骤:" -ForegroundColor Yellow
    Write-Host "1. 下载 apache-maven-3.9.6-bin.zip" -ForegroundColor Yellow
    Write-Host "2. 解压到: $mavenHome" -ForegroundColor Yellow
    Write-Host "3. 重新运行此脚本" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "详细说明请查看: install_maven_manual.md" -ForegroundColor Yellow
    Read-Host "按Enter键退出"
    exit 1
}

if (-not (Test-Path $mvnCmd)) {
    Write-Host "❌ Maven命令文件不存在: $mvnCmd" -ForegroundColor Red
    Write-Host ""
    Write-Host "请确认Maven已正确解压到: $mavenHome" -ForegroundColor Yellow
    Write-Host "目录结构应该是:" -ForegroundColor Yellow
    Write-Host "  $mavenHome\" -ForegroundColor Yellow
    Write-Host "    ├── bin\" -ForegroundColor Yellow
    Write-Host "    ├── boot\" -ForegroundColor Yellow
    Write-Host "    ├── conf\" -ForegroundColor Yellow
    Write-Host "    └── lib\" -ForegroundColor Yellow
    Read-Host "按Enter键退出"
    exit 1
}

Write-Host "✅ Maven目录存在: $mavenHome" -ForegroundColor Green
Write-Host ""

# 检查是否有管理员权限
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if ($isAdmin) {
    Write-Host "✅ 以管理员权限运行，将配置系统环境变量" -ForegroundColor Green
    $scope = "Machine"
} else {
    Write-Host "⚠️  非管理员权限，将配置用户环境变量" -ForegroundColor Yellow
    $scope = "User"
}

Write-Host ""
Write-Host "配置环境变量..." -ForegroundColor Green

# 设置MAVEN_HOME
try {
    [Environment]::SetEnvironmentVariable("MAVEN_HOME", $mavenHome, $scope)
    Write-Host "✅ MAVEN_HOME = $mavenHome" -ForegroundColor Green
} catch {
    Write-Host "❌ 设置MAVEN_HOME失败: $_" -ForegroundColor Red
}

# 添加到PATH
try {
    $currentPath = [Environment]::GetEnvironmentVariable("Path", $scope)
    
    if ($currentPath -notlike "*$mavenBin*") {
        $newPath = "$currentPath;$mavenBin"
        [Environment]::SetEnvironmentVariable("Path", $newPath, $scope)
        Write-Host "✅ 已添加到PATH: $mavenBin" -ForegroundColor Green
    } else {
        Write-Host "✅ PATH中已存在Maven" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ 设置PATH失败: $_" -ForegroundColor Red
}

# 刷新当前会话的环境变量
$env:MAVEN_HOME = $mavenHome
$env:Path = "$env:Path;$mavenBin"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "    配置完成！" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "请执行以下步骤验证:" -ForegroundColor Yellow
Write-Host "1. 关闭当前PowerShell窗口" -ForegroundColor White
Write-Host "2. 重新打开PowerShell" -ForegroundColor White
Write-Host "3. 运行: mvn -version" -ForegroundColor White
Write-Host ""
Write-Host "如果显示Maven版本信息，说明配置成功！" -ForegroundColor Green
Write-Host ""

Read-Host "按Enter键退出"
