# 文档导航

[项目首页](../README.md) · [RSI 手册](../RSI/README.md)

## 我想使用

| 文档 | 解决的问题 |
| --- | --- |
| [快速上手](getting-started.md) | 怎么安装、运行示例、在 Rust 中依赖本仓库 |
| [多路信号管线](guides/pipeline.md) | 怎么质检、同步、保留历史窗口、组织训练输入 |
| [MCAP 与媒体](guides/media.md) | 怎么读 JSON、接 CDR/Protobuf、处理图片、检查视频 |
| [Python API](python.md) | 14 个公共处理函数的签名、返回类型、默认值与错误 |
| [Rust API](rust.md) | 类型、模块、筛选接口、Decoder 扩展点 |
| [算子清单](operators.md) | 哪些已经实现，哪些能从 Python 调用 |

## 我想理解或扩展

| 文档 | 解决的问题 |
| --- | --- |
| [设计与架构](architecture.md) | 模块边界、依赖方向、设计取舍、上游职责 |
| [抽象与数据契约](concepts.md) | Signal、时间、质量事件、掩码、来源与因果性 |
| [贡献与验证](contributing.md) | 本地编辑、reference-linux 测试、Git 同步、文档示例验证 |
| [RSI 工作流](../RSI/workflow.md) | 如何从瓶颈探索走到可审计的优化提交 |

## 我想核对性能

| 阶段 | 已完成决策 | 接受 / 拒绝 | 入口 |
| --- | ---: | ---: | --- |
| 初始两轮 | 60 | 27 / 33 | [报告](performance/RESULTS.md) |
| 后续二十轮 | 20 | 7 / 13 | [报告](performance/extension/RESULTS.md)、[经验](performance/extension/LESSONS.md) |
| 每算子追加十轮 | 300 | 23 / 277 | [报告](performance/per-op10/RESULTS.md)、[经验](performance/per-op10/LESSONS.md) |

合计 380 个已记录决策。接受数按最终记录统计；撤销、复测和集成修正须结合
`history/` 与 `final/` 阅读，不能仅累计单轮百分比推算总加速。

文档描述 `0.1.0` 的实际接口。性能报告是历史证据，新增功能或实验应增加新记录，
不应覆盖旧测量。原始 profile 大文件在 reference-linux 的 `.artifacts/` 中，Git 中保存日志、
摘要、哈希与来源路径，详见[证据索引](../RSI/evidence.md)。
