# Beckhoff ADS Virtual Server 环境搭建说明

## 1. 目标

本文档用于复现 `Beckhoff.TwinCAT.Ads.Server` 虚拟 ADS Server 环境，目标是为后续 `source_lab` 增加 `beckhoff_ads` 协议提供可复现的开发期 ADS Server 测试环境。

本阶段目标：

```text
1. 在 Windows 上安装 TwinCAT XAR / ADS Router。
2. 安装 .NET 8 SDK。
3. 新建空白 .NET Console 工程。
4. 引入 Beckhoff ADS NuGet 包。
5. 编写最小 ADS virtual server。
6. 验证 ADS virtual server 能注册到本机 ADS Router。
7. 不要求 TwinCAT real-time runtime 成功 Start。
8. 不要求真实 Beckhoff PLC。
```

当前能达到的效果：

```text
1. 本机 ADS Router 监听 48898。
2. Beckhoff.TwinCAT.Ads.Server 可被 .NET 工程正常引用。
3. 自定义 AdsServer 可注册为本机虚拟 ADS Server。
4. 程序运行后可获得一个本机 AMS 地址，例如：
   172.27.144.1.1.1:33111
5. 该环境可作为后续 ADS client 读、写、读写、通知等功能测试的基础。
6. 即使 TwinCAT System -> Start 因 RTIME 报错失败，ADS virtual server 方案仍可继续。
```

本文当前只覆盖 **ADS Server 环境搭建和最小注册验证**。后续完成 `source_lab` 的 ADS 协议实践后，再补充 client 读写回环、notification、source_lab runner 和自动化复现脚本。

---

## 2. 环境说明

已验证环境：

```text
操作系统：Windows
TwinCAT：TwinCAT 3.1 XAR 4024.75
.NET SDK：.NET 8
Beckhoff NuGet：
  - Beckhoff.TwinCAT.Ads 7.0.172
  - Beckhoff.TwinCAT.Ads.Server 7.0.172
  - Beckhoff.TwinCAT.Ads.Abstractions 7.0.172
```

注意：

```text
1. XAR 是 Runtime 环境，不是 XAE Engineering IDE。
2. 安装 XAR 后，开始菜单中可能没有完整 TwinCAT IDE。
3. 右下角 TwinCAT 图标可用于查看 Runtime/System 状态。
4. 本文只验证 ADS Router + virtual ADS server，不验证 PLC runtime。
```

---

## 3. 安装 TwinCAT XAR

### 3.1 下载

下载 Beckhoff TwinCAT 3 XAR：

```text
TwinCAT 3 download | eXtended Automation Runtime (XAR)
版本示例：
TwinCAT 3.1
Build 4024.75
```

### 3.2 安装组件

安装过程中至少选择：

```text
TwinCAT 3 ADS (x64)
TwinCAT 3 ADS API
```

可以不安装完整 XAE Engineering。

### 3.3 第三方组件提示

安装过程中可能提示：

```text
Git for Windows Minimal
License: GPL License
Used by TwinCAT Multuser
```

如果不需要 TwinCAT Multiuser，可按实际情况选择；这不影响 ADS Server 最小验证。

---

## 4. 确认 ADS Router 是否运行

安装完成并重启后，打开 PowerShell，执行：

```powershell
netstat -ano | findstr 48898
```

预期看到类似：

```text
TCP    0.0.0.0:48898    0.0.0.0:0    LISTENING    <PID>
```

说明 ADS Router 已监听。

也可以检查 TwinCAT 服务：

```powershell
Get-Service *TwinCAT*
```

可看到类似：

```text
TwinCAT3 System Service
TwinCAT3 AdsGitServer
```

---

## 5. TwinCAT System Start 报错说明

如果右下角 TwinCAT 图标中执行：

```text
System -> Start
```

出现：

```text
RTIME: incompatible software detected
AdsError: 4132
```

这表示 TwinCAT real-time runtime 启动失败，常见原因包括 Hyper-V、WSL2、虚拟化、安全软件、实时内核冲突等。

本文目标不依赖 TwinCAT PLC Runtime 成功 Start。只要 ADS Router 可监听 `48898`，就可以继续验证 `Beckhoff.TwinCAT.Ads.Server`。

---

## 6. 安装 .NET 8 SDK

使用管理员 PowerShell 执行：

```powershell
winget install -e --id Microsoft.DotNet.SDK.8
```

安装完成后关闭 PowerShell，重新打开，执行：

```powershell
dotnet --version
```

预期看到：

```text
8.0.xxx
```

---

## 7. 从空目录创建 ADS Virtual Server 工程

以下脚本可以完整复制执行。

说明：

```text
1. 脚本默认在当前用户目录下创建 ads-work。
2. 可通过修改 $BaseDir 改为任意空白工作目录。
3. 不要把临时子项目放进当前 .NET 项目目录内，否则父项目可能会编译子目录里的 .cs 文件。
```

```powershell
# ============================================================
# Beckhoff ADS Virtual Server 最小复现工程
# 从空目录开始执行
# ============================================================

# 你可以把这里改成任意空白工作目录
$BaseDir = Join-Path $env:USERPROFILE "ads-work"
$ProjectName = "AdsVirtualServerRun"
$ProjectDir = Join-Path $BaseDir $ProjectName

# 创建独立工作目录
New-Item -ItemType Directory -Path $BaseDir -Force | Out-Null
Set-Location $BaseDir

# 删除旧目录，确保干净
Remove-Item $ProjectDir -Recurse -Force -ErrorAction SilentlyContinue

# 创建 .NET Console 项目
dotnet new console -n $ProjectName

# 进入项目目录
Set-Location $ProjectDir

# 添加 Beckhoff ADS NuGet 包
dotnet add package Beckhoff.TwinCAT.Ads --version 7.0.172
dotnet add package Beckhoff.TwinCAT.Ads.Server --version 7.0.172
dotnet add package Beckhoff.TwinCAT.Ads.Abstractions --version 7.0.172

# 写入最小 ADS virtual server
@'
using System;
using System.Buffers.Binary;
using System.Collections.Concurrent;
using System.Threading;
using System.Threading.Tasks;
using TwinCAT.Ads;
using TwinCAT.Ads.Server;

const string portName = "Whale.SourceLab.BeckhoffAds.VirtualServer";

using var server = new MinimalAdsVirtualServer(portName);

Console.WriteLine("Starting ADS virtual server...");
Console.WriteLine($"PortName: {portName}");

using var cts = new CancellationTokenSource(TimeSpan.FromSeconds(5));
var connectResult = await server.ConnectServerAndWaitAsync(cts.Token);

Console.WriteLine($"Connect result: {connectResult}");
Console.WriteLine($"IsConnected: {server.IsConnected}");
Console.WriteLine($"ServerPort: {server.ServerPort}");
Console.WriteLine($"ServerAddress: {server.ServerAddress}");
Console.WriteLine("Press ENTER to stop.");

Console.ReadLine();

server.Disconnect();

public sealed class MinimalAdsVirtualServer : AdsServer
{
    private readonly ConcurrentDictionary<(uint Group, uint Offset), byte[]> _memory = new();

    public MinimalAdsVirtualServer(string portName)
        : base(portName)
    {
        var bytes = new byte[4];
        BinaryPrimitives.WriteInt32LittleEndian(bytes, 123456);

        // 预置一个 DINT:
        // indexGroup  = 0x4020
        // indexOffset = 0
        // value       = 123456
        _memory[(0x4020, 0)] = bytes;
    }

    protected override Task<ResultReadBytes> OnReadAsync(
        AmsAddress sender,
        uint invokeId,
        uint indexGroup,
        uint indexOffset,
        int readLength,
        CancellationToken cancel)
    {
        if (!_memory.TryGetValue((indexGroup, indexOffset), out var data))
        {
            return Task.FromResult(
                ResultReadBytes.CreateError(AdsErrorCode.DeviceInvalidOffset, invokeId)
            );
        }

        if (readLength < 0 || readLength > data.Length)
        {
            return Task.FromResult(
                ResultReadBytes.CreateError(AdsErrorCode.DeviceInvalidSize, invokeId)
            );
        }

        return Task.FromResult(
            ResultReadBytes.CreateSuccess(data.AsMemory(0, readLength), invokeId)
        );
    }

    protected override Task<ResultWrite> OnWriteAsync(
        AmsAddress target,
        uint invokeId,
        uint indexGroup,
        uint indexOffset,
        ReadOnlyMemory<byte> writeData,
        CancellationToken cancel)
    {
        _memory[(indexGroup, indexOffset)] = writeData.ToArray();

        return Task.FromResult(
            ResultWrite.CreateSuccess(invokeId)
        );
    }

    protected override Task<ResultReadWriteBytes> OnReadWriteAsync(
        AmsAddress sender,
        uint invokeId,
        uint indexGroup,
        uint indexOffset,
        int readLength,
        ReadOnlyMemory<byte> writeData,
        CancellationToken cancel)
    {
        _memory[(indexGroup, indexOffset)] = writeData.ToArray();

        var data = _memory[(indexGroup, indexOffset)];

        if (readLength < 0 || readLength > data.Length)
        {
            return Task.FromResult(
                ResultReadWriteBytes.CreateError(AdsErrorCode.DeviceInvalidSize, invokeId)
            );
        }

        return Task.FromResult(
            ResultReadWriteBytes.CreateSuccess(data.AsMemory(0, readLength), invokeId)
        );
    }

    protected override Task<ResultReadDeviceState> OnReadDeviceStateAsync(
        AmsAddress sender,
        uint invokeId,
        CancellationToken cancel)
    {
        var state = new StateInfo(AdsState.Run, 0);

        return Task.FromResult(
            ResultReadDeviceState.CreateSuccess(state, invokeId)
        );
    }
}
'@ | Set-Content .\Program.cs -Encoding UTF8

# 编译
dotnet build

# 运行
dotnet run
```

---

## 8. 预期输出

运行成功时，预期看到类似：

```text
Starting ADS virtual server...
PortName: Whale.SourceLab.BeckhoffAds.VirtualServer
Connect result: Succeeded
IsConnected: False
ServerPort: 0
ServerAddress: 172.27.144.1.1.1:33111
Press ENTER to stop.
```

说明：

```text
Connect result: Succeeded
```

表示 ADS virtual server 已成功注册到 ADS Router。

```text
ServerAddress: 172.27.144.1.1.1:33111
```

表示当前虚拟 ADS Server 的 AMS 地址。端口 `33111` 是动态注册端口。不同机器和不同运行时，实际地址与端口可能不同。

```text
ServerPort: 0
```

这是因为代码使用了动态端口构造函数：

```csharp
base(portName)
```

真实端口以 `ServerAddress` 为准。

```text
IsConnected: False
```

当前阶段可暂不作为失败判断。实际可用性应以后续 AdsClient read/write 回环测试为准。

---

## 9. 常见问题

### 9.1 dotnet 无法识别

现象：

```text
dotnet : 无法将“dotnet”项识别为 cmdlet、函数、脚本文件或可运行程序的名称
```

处理：

```powershell
winget install -e --id Microsoft.DotNet.SDK.8
```

安装后关闭并重新打开 PowerShell。

---

### 9.2 空目录里 dotnet add package 报找不到项目

错误原因：

```text
dotnet add package 必须在 .csproj 项目目录内执行
```

正确顺序：

```powershell
dotnet new console -n AdsVirtualServerRun
cd .\AdsVirtualServerRun
dotnet add package Beckhoff.TwinCAT.Ads --version 7.0.172
```

---

### 9.3 父项目编译了子目录里的 Program.cs

现象：

```text
类型 Program 的声明上缺少 partial 修饰符
只有一个编译单元可具有顶级语句
```

原因：

```text
.NET SDK 默认会把项目目录下子目录中的 *.cs 也编进当前项目。
```

处理：

```text
不要把临时子项目放在当前 .NET 项目目录下面。
临时工程应放在兄弟目录或单独目录。
```

推荐目录：

```text
<workspace>\AdsVirtualServerRun
<workspace>\ApiDumpTmp
```

不要：

```text
<workspace>\AdsVirtualServerRun\ApiDumpTmp
```

---

### 9.4 TwinCAT System Start 报 RTIME 4132

现象：

```text
RTIME: incompatible software detected
AdsError: 4132
```

说明：

```text
这是 TwinCAT real-time runtime 启动失败。
本文 ADS virtual server 最小验证不依赖 TwinCAT real-time runtime 成功启动。
```

只要以下命令确认 ADS Router 监听即可继续：

```powershell
netstat -ano | findstr 48898
```

---

### 9.5 Connect result 是 ClientPortNotOpen

可能原因：

```text
1. ADS Router 没有正常运行。
2. 当前 PowerShell 权限不足。
3. 固定端口注册失败。
```

处理：

```powershell
netstat -ano | findstr 48898
Get-Service *TwinCAT*
```

如果 ADS Router 已运行，尝试用管理员 PowerShell：

```powershell
Set-Location "$env:USERPROFILE\ads-work\AdsVirtualServerRun"
dotnet run
```

当前推荐使用动态端口构造：

```csharp
public MinimalAdsVirtualServer(string portName)
    : base(portName)
{
}
```

不要优先使用固定端口：

```csharp
base(35000, portName)
```

---

## 10. 当前阶段结论

本阶段已证明：

```text
1. Beckhoff.TwinCAT.Ads.Server 可用于搭建 ADS virtual server。
2. Windows + TwinCAT XAR / ADS Router + .NET 8 SDK 环境可运行。
3. 不需要先解决 TwinCAT real-time runtime 4132 问题。
4. 可作为 source_lab beckhoff_ads 协议开发期测试环境基础。
```

---

## 11. 后续待补充内容

等 `source_lab` 实践完成后，需要继续补充：

```text
1. AdsClient read/write/readwrite 回环测试。
2. ADS notification 测试。
3. symbol handle 测试。
4. source_lab beckhoff_ads runner 接入方式。
5. C++ AdsLib native runner 构建方式。
6. 在无 XAR/ADS Router 环境下如何跳过相关测试。
7. Windows 本机验证脚本。
8. Linux runner 与 Windows ADS virtual server 的联调方式。
9. 与 shared_source production ADS backend 的边界说明。
```

建议后续文档状态：

```text
当前版本：
ADS virtual server environment smoke

后续版本：
source_lab beckhoff_ads protocol development and validation guide
```
