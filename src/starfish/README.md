# Starfish

Starfish 是 IEC104 simulator 的运行时管理模块。当前实现采用 Hexagonal
Architecture，并在 core 内使用 Supervisor/Worker 模式管理多个 server。
依赖装配集中在 `starfish.composition`，不再保留单独的 API facade 层。

## CLI

数据库连接由 `WHALE_DB_URL` 提供：

```bash
python -m starfish run -id 1001
python -m starfish run -a
```

`-id` 按 `connection_id` 启动一个 simulator，`-a` 选择 DB view 中全部
connection，两者必须且只能选择一个。Starfish 会先读取每个 connection 的
protocol，再调用对应协议 loader；当前只注册 IEC104，其他协议会明确报错。

## 数据来源

Starfish 从以下 Whale 执行视图构建 server：

- `vw_connection_object_full`
- `vw_task_full`
- connection/task 中登记的协议 point item view

Starfish 只读取初始化信息并管理 server 生命周期。server 数据更新由 Seahorse
负责，Starfish 不提供 read/write API。

详细边界见 [ARCHITECTURE.md](ARCHITECTURE.md)。
