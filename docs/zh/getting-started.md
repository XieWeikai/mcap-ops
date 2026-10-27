# 快速上手

**语言：中文 | [English](../getting-started.md)**

[文档导航](README.md) · [Python API](python.md) · [Rust API](rust.md)

## 运行环境

| 项目 | 要求或验证范围 |
| --- | --- |
| Python | 包声明 Python >=3.10；已验证 CPython 3.12.3 |
| NumPy | 包声明 >=1.24；最近一次最终验证为 2.5.4 |
| Rust | `rust-toolchain.toml` 固定 1.90.0 |
| Python 构建 | maturin >=1.9,<2；常规本机 C/C++ 编译工具 |
| MCAP / 图片 | 通过 Rust 依赖实现；无需安装 ROS |
| 视频 | 另需调用方安装 `ffmpeg` 和 `ffprobe`，可传入绝对路径 |
| 现有 wheel | Linux x86-64，glibc 2.39+，`cp310-abi3`；未验证 macOS/Windows |

目前没有 PyPI/crates.io 发布；不要把 `pip install mcap-ops` 当成本项目已验证的安装方式。
下载源码时保留完整 Git 历史，RSI 的不可变 oracle 依赖旧提交。

维护者：按 [AGENTS.md](../../AGENTS.md) 在本地编辑，所有构建、测试、profiling
在配置的独立 Linux x86-64 执行环境运行。部署位置通过忽略的本地配置或环境变量提供；以下命令均在选定的构建环境
仓库根目录执行，外部使用者可在自己的受控环境构建。

## 从源码使用 Python

确保 `rustc --version` 对应 1.90.0，然后执行：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install "maturin>=1.9,<2" "numpy>=1.24" "pytest>=8"
.venv/bin/maturin develop --release --locked
.venv/bin/python examples/quickstart.py
.venv/bin/python -m pytest -q tests
```

预期示例输出：

```text
linear: [0.0, 0.5, 1.0, 1.5, 2.0]
previous: [0.0, 0.0, 1.0, 1.0, 2.0]
quality: [('above_range', 1)]
history shape: (1, 3, 1)
```

[示例源码](../../examples/quickstart.py) 内置断言，不读用户数据、不启动服务。

## 构建和安装 wheel

```bash
.venv/bin/maturin build --release --locked --out dist
python3 -m venv .tools/consumer
.tools/consumer/bin/python -m pip install dist/*.whl
.tools/consumer/bin/python examples/quickstart.py
```

`dist/` 应仅包含本次目标平台的 wheel。构建产物的具体平台标签取决于构建环境。
原 RSI 已验证 wheel 位于维护者的 `.artifacts/rsi/per-op10/wheel/`，不提交到 Git，
也尚未作为 GitHub Release 附件发布。

## Rust 直接使用

在消费方 `Cargo.toml` 中使用本地 path 依赖；将路径替换为实际 checkout：

```toml
[dependencies]
mcap-ops-core = { path = "../mcap-ops/crates/core" }
mcap-ops-io = { path = "../mcap-ops/crates/io" }
```

只处理数组时仅依赖 core。仓库内的完整示例：

```bash
cargo run --locked --release -p mcap-ops-core --example quality_pipeline
```

该示例通过公共接口串联质检、门控、区间选择与重采样。
参见 [Rust 用法](rust.md)和[示例源码](../../crates/core/examples/quality_pipeline.rs)。

## 常见问题

| 现象 | 原因与处理 |
| --- | --- |
| `No module named mcap_ops._native` | Rust 扩展尚未安装，或执行的 Python 不属于安装环境 |
| dtype 错误 | 时间使用 `np.int64`，数值使用 `np.float64`；不自动转换输入 dtype |
| 时间数组不是连续布局 | 用 `np.ascontiguousarray(times, dtype=np.int64)`；values 可为跨步视图 |
| 输出大多无效 | 检查 ns/ms 单位、时钟来源、`max_age_ns`/`max_gap_ns` 和未来值策略 |
| `source timestamps must be strictly increasing` | 先质检，再由上游决定重复/倒退的处理方式 |
| 未知 CDR/Protobuf 消息 | 通过上游 schema adapter 解码；MCAP 容器检查不等于数值解码 |
| FFmpeg 找不到或退出失败 | 检查可执行文件和解码能力；工具不可用不是数据质量通过 |
| 当前 wheel 无法装在 macOS | 该 wheel 是 Linux 产物；其他平台需要单独构建与验证 |

下一步：[设计多信号管线](guides/pipeline.md)。
