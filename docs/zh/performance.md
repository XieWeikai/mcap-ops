# 性能环境与证据

**语言：中文 | [English](../performance.md)**

[文档导航](README.md) · [RSI 协议](../../RSI/zh/README.md)

## 描述环境，不依赖部署地址

| 维度 | 已记录的测试条件 |
| --- | --- |
| 架构 / 系统 | Linux x86-64，kernel 6.11，glibc 2.39 |
| CPU | Intel Core i9-14900K，32 个逻辑线程 |
| 亲和性 | 固定一个性能核对应的逻辑 CPU；历史记录使用 CPU index 12 |
| Rust | 1.90.0，release、thin LTO、一个 codegen unit，锁文件和 flags 不变 |
| Python / NumPy | CPython 3.12.3 / NumPy 2.5.4 |
| Native profile | 两侧 release 产物都保留 debug line tables |
| 最终 Python 计时 | 两侧 release wheel 都关闭 debug 信息 |
| Profiling | Callgrind / cProfile；插桩时间不作为性能收益 |
| 数据 | 生成 fixture；重复文件读取不等于冷盘吞吐 |
| 调度 | 试验串行，不让多个 benchmark 争抢同一固定 CPU |

CPU 编号不具备跨平台含义，迁移前应核对实际拓扑。未使用 GPU 加速。
参考环境限制硬件计数器，因此采用用户态工具，没有修改全局权限。

## 如何读结果

| 阶段 | 决策数 | 接受 / 拒绝 | 详细记录 |
| --- | ---: | ---: | --- |
| 初始 | 60 | 27 / 33 | [结果](../performance/RESULTS.md) |
| 后续 | 20 | 7 / 13 | [结果](../performance/extension/RESULTS.md) |
| 每算子十轮 | 300 | 23 / 277 | [结果](../performance/per-op10/RESULTS.md) |

百分比是配对耗时下降，不是吞吐增长。每轮对比最近接受状态；整版对比使用相同的最终
harness 重建起始实现。不能把各轮百分比相加，也不能混合不同基线。

接受至少需要四组交替 AB/BA、每侧七个校准样本、每块几何平均耗时下降不少于 8%，
任一代表用例中位数退化不超过 3%，并通过正确性、资源和复杂度审查。PNG 编码候选
还要求解码像素一致，测得的最大文件增长不超过 1.25 倍。

## 反例也是结果

后续阶段曾因短核和缺口退化撤销 FIR 转置；再后阶段发现 reader cache 的单 topic 开销，
再用小范围修正重新验收。初始观察、独立复测、拒绝补丁与最终结论全部保留。
请结合[双语证据索引](../../RSI/zh/evidence.md)，不要只读正收益摘要。

最新整版覆盖 78 个 native 和 21 个 Python 工作负载；最差 native 下降为 -2.91%，
最差 Python 约 -0.84%。这些是测量变化，不是加速。最终 wheel 当时通过五项 API smoke
和 291 项接口对比；后续新增工作流测试不改变那次历史计数。

## 共享证据与限制

原始 JSON、patch、日志和生成报告共享一份，不制造两套中英文测量。两种语言的解释均
引用同一组数字和哈希；保留历史基线和实验标识，不因翻译声称额外运行。

大型 profile 和 wheel 保留在产物存储中，不随 Git 克隆。已验证 wheel 面向 Linux x86-64 /
glibc 2.39+，CPython abi3 3.10+，实际运行验证为 Python 3.12。未证明真实录制、上游整条
管线、GPU、多 worker 或其他平台的性能；Python 绑定仍持有 GIL。
