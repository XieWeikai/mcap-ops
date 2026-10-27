# 已有探索与证据索引

**语言：中文 | [English](../evidence.md)**

[导航](README.md) · [操作手册](workflow.md)

## 三轮历史，不覆盖重用

| Series | 基线 | 决策 | 最终接受 / 拒绝 | 报告 |
| --- | --- | ---: | ---: | --- |
| initial | `66248dac` | 60 | 27 / 33 | [两轮结果](../../docs/performance/RESULTS.md) |
| extension | `bc58f81b` | 20 | 7 / 13 | [二十轮结果](../../docs/performance/extension/RESULTS.md) |
| per-op10 | `9de19ead` | 300 | 23 / 277 | [每算子十轮结果](../../docs/performance/per-op10/RESULTS.md) |

30 个计数单元包含 IntervalSet 的多个操作、IO 和 Python bridge，不等于 30 个 Python 函数。
总计 380 个完成决策；中断、编译修复、同候选的确认和集成修正不是新增优化轮。
结果百分比相对于该次最近接受状态，不能直接加和。

## 下一轮应先学到什么

| 经验 | 对应证据 / 反例 |
| --- | --- |
| 减少重复计算比改语法更有机会 | Hampel 利用有序窗口和偏差；[per-op10 经验](../../docs/performance/per-op10/LESSONS.md) |
| 有序数据先定位有效前缀 | 稀疏时间匹配获益，但要同时测密集路径 |
| 缓存要覆盖小输入成本 | 多 topic reader 缓存导致单 topic 退化；[重新验收](../../docs/performance/per-op10/final/raw-reader-requalification.json) |
| 不能只看平均收益 | clock drift 快而纯 offset 慢，候选拒绝；[extension 12](../../docs/performance/extension/results/extension-12-map-clock.json) |
| 准备成本也是调用成本 | FIR 转置长核较快，短核/缺口退化后撤销；[extension 历史](../../docs/performance/extension/history) |
| “无分支/迭代器/原地”不保证快 | [extension 经验](../../docs/performance/extension/LESSONS.md)及 rejected 补丁 |
| bridge 应利用既有所有权 | 减少输出复制、处理跨步数组；保持快照和逻辑次序 |
| 成熟媒体库外围调参常未达标 | image/video 候选保留失败记录；不靠更大文件换取未说明的速度 |
| 最终包必须复测 | [整版 native](../../docs/performance/per-op10/final/native.json)、[release Python](../../docs/performance/per-op10/final/python.json) |

单 topic 反例先在集成和独立复测观察到，随后只改一条谓词：空/单 topic 走直接比较，
多 topic 继续缓存。原退化结果留在 final/integration-*，修正提交 `f2813d9` 不隐去失败证据。
这比只保留成功汇总更能指导下一次探索。

## 证据存在哪里

```text
docs/performance/<series>/
  PLAN.md              冻结范围、环境与门槛
  RESULTS.md           决策与最终整版比较
  LESSONS.md           成功、失败、撤销及适用边界
  results/<label>.json 决策、热点、复杂度、base_commit、哈希
  data/<label>.json    每块/每侧/每用例的原始样本与配对统计
  rejected/*.patch    未保留的实现尝试
  history/             独立确认、撤销前的决定与反证
  evidence/            验证日志、profile 摘要、原始 profile 哈希与路径
  final/               全套集成比较、wheel/扩展/源码身份、限制

.artifacts/rsi/trials/<label>/    本地/远端工作产物，不进 Git
  before/                       候选拥有路径的基线快照
  candidate.patch               验证过的候选 diff
  before.callgrind / *.prof      原始 profile，可能很大
  measurement.json / audit.json  计时与机器 gate
  validation.log                完整验证输出
  attempts/                     失败或中断重试记录
  commit-message.txt            接受时生成的提交说明
```

initial 的 results/data 在 `docs/performance/` 根层，保留历史布局；后续 series 用子目录。
Git 中的 profile 哈希不是原始文件本身；新使用者能检查证据身份和摘要，但若要重新查看
完整 profile，需要访问归档主机或重新生成，不能声称克隆就包含所有大产物。

## 脚本职责与限制

| 工具 | 运行位置 | 职责 / 限制 |
| --- | --- | --- |
| `sync_sources.py` | 本地 | 相对路径清单同步；不发布 Git、不删除；先检查远端工作树 |
| `rsi_trial.py` | 本地，执行在配置的 Linux 执行环境 | 保存快照、正确性、profile、配对计时、audit；支持新 series |
| `rsi_decide.py` | 本地 | 保存决策；接受生成 commit 文本，拒绝恢复已验证 owned paths |
| `rsi_measure.py` | 配置的 Linux 执行环境 | 采样与配对，保存二进制身份；低层工具不替代全部接受审阅 |
| `prepare_reference.py` | 配置的 Linux 执行环境 | 从固定历史 commit 建不可变 oracle workspace |
| `check_python_equivalence.py` | 配置的 Linux 执行环境 | 两个真实包快照的公共接口对比 |
| `archive_extension_evidence.py` | 本地 | 新 series 也可归档日志/profile 身份；initial 布局另处理 |
| `rsi_batch.py`, `rsi_extension.py`, `rsi_per_operator.py` | 本地 | 历史候选调度器；不是新的通用 campaign 定义 |
| `report_rsi.py`, `report_extension.py`, `report_per_operator.py` | Linux 执行环境审核 | 固定历史范围的审计和报告生成，会写对应文件 |
| `verify_extension.sh`, `verify_per_operator.sh` | 配置的 Linux 执行环境 | 固定历史 campaign 收尾；新轮次不要覆盖其输出 |
| `publish_remote.py` | 本地 | 检查干净提交、哈希和 fast-forward，发布 Git bundle |

历史 300 轮的候选定义在 [benchmarks/ten_rounds](../../benchmarks/ten_rounds)，30 个单元的
覆盖和详细决策在 [coverage.json](../../docs/performance/per-op10/coverage.json)。
新 series 可直接复用 trial/decide/archive；若需要新的批量调度器或报告审计器，先按
新计划明确数量与 baseline，再实现，不篡改历史脚本中的目标来制造已完成统计。

## 接受提交该写什么

```text
perf(operator): concrete change [RSI series round N]

Profile: measured hotspot and source profile
Change: what redundant work was removed
Complexity: branches, memory, dependencies and maintenance cost
Environment: host / CPU / Rust / profile / immutable fixture set
Paired blocks: count, samples per side, order
Aggregate reduction: median and worst block
case: before ns/op -> after ns/op; paired reduction
Correctness: exact commands and results, tolerances
Resources: measured or bounded costs, PNG size ratio if applicable
Decision: why it clears every gate
Evidence: results/<label>.json and data/<label>.json
```

每轮提交绑定该轮证据；报告另补最终 commit hash。文档/测试脚手架提交与性能提交分开。
新的正确性修复或集成再验收不能偷换为第 N+1 次候选。
