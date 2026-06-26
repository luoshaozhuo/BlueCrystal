"""starfish 协议级模块集合 —— 编解码器、协议常量和链路层定义。

本包存放协议编解码器（codec）和链路层定义，
与 facade 层互补：facade 负责 server 生命周期和点位映射，
protocols 负责协议帧编解码和协议常量定义。

当前子包：
    - iec101: IEC 60870-5-101 编解码器骨架（ASDU/COT/IOA/CA 编解码）。

架构隔离：
    - 不得 import seahorse / whale.ingest / whale.shared.source。
    - 不得连接生产数据库。
    - 纯协议栈实现，不涉及真实 I/O。
"""
