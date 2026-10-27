# 贡献、验证与发布

**语言：中文 | [English](../contributing.md)**

[文档导航](README.md) · [仓库规则](../../AGENTS.md) · [RSI](../../RSI/zh/README.md)

## 分离编写端与执行端

```mermaid
flowchart LR
    A["本地编辑与审阅"] --> B["按相对路径同步源码"]
    B --> C["Linux 执行环境<br/>构建与测试"]
    C --> D["本地 commit"]
    D --> E["Git bundle + 全文件哈希"]
    E --> F["执行端验证后 fast-forward"]
    F --> G["推送已审阅历史"]
```

使用隔离的 Linux x86-64 执行 checkout 和项目本地 Rust/Python 工具。历史参考环境为
32 个逻辑 CPU、固定性能核亲和性、Rust 1.90.0、release 构建；完整条件见
[性能环境](performance.md)。其他环境必须自行验证，不能直接宣称相同性能。

不在公开文档中写部署别名、账号名、绝对工作路径或启动标识。通过环境变量或 Git 忽略的
`.mcap-ops.local.json` 提供执行位置：

```json
{
  "host": "your-ssh-alias",
  "destination": "/absolute/path/to/mcap-ops"
}
```

这些是占位值，不是可直接使用的部署地址。也可以设置 MCAP_OPS_TEST_HOST 和
MCAP_OPS_TEST_ROOT。同步 CLI 的显式参数优先，其次环境变量，最后本地配置。
项目路径必须是绝对路径、无空格和父目录跳转。不在配置中放凭据，认证使用正常 SSH。

同步前分别核对两端 HEAD 和工作树；不能覆盖其他任务修改或分叉历史。仅 HEAD 相同
不代表文件一致。

## 同步源码

```bash
git status --short
python3 scripts/sync_sources.py
```

同步 tracked 和非忽略新文件，保留相对目录；不复制 .git、不删除、不推进历史、不运行
测试。它会更新同名文件，因此先审阅执行端工作树。第三方展示、工具、虚拟环境、
本地配置和二进制产物都不应加入 Git。

## 项目本地工具

在执行 checkout 根目录：

```bash
export CARGO_HOME="$PWD/.tools/cargo"
export RUSTUP_HOME="$PWD/.tools/rustup"
export PATH="$CARGO_HOME/bin:$PATH"
export VIRTUAL_ENV="$PWD/.venv"
rustc --version
.venv/bin/python --version
```

前提是工具已安装到这些目录。新环境按[快速上手](getting-started.md)准备，不借用其他
训练或机器人控制项目的环境。

```bash
cargo fmt --all --check
cargo clippy --workspace --all-targets --locked -- -D warnings
cargo test --workspace --locked -j 12
cargo run --locked --release -p mcap-ops-core --example quality_pipeline
.venv/bin/maturin develop --release --locked
.venv/bin/python -m pytest -q tests
.venv/bin/python examples/quickstart.py
```

差分、profiling 和 benchmark 按 [RSI](../../RSI/zh/workflow.md)。普通文档修改不需要
重跑几百个历史候选。共享 CI 不作为性能接受环境。当前工作流是操作手册 + CLI，
不代表已经部署 GitHub Actions、自托管 runner 或 SSH secrets。

## 改动覆盖面

- 算子：公共类型、错误边界、生成 fixture、单位、shape 和因果性。
- Python：绑定、wrapper、__all__、返回类型、公共测试和 API 文档。
- Decoder：schema、时钟、字段、未知编码失败、限额和原始顺序。
- 优化：单一假设、可比较产物、独立接受 commit、拒绝证据。
- 文档：内容对应的中英页面、链接与图示、可执行代码片段。

工作流测试用临时 Git 仓库验证新 series、决策防覆盖、过期候选拒绝恢复、仅恢复拥有路径、
接受不自动 commit、非法命名和最低配对块数等保护。

## 提交和发布执行端历史

只暂存相关文件，检查 diff；性能提交与文档、脚手架、正确性修复分开。

```bash
git diff --check
git diff --cached
# 提交已审阅内容后，工作树应干净。
python3 scripts/publish_remote.py
```

发布工具传输 Git bundle，核对 tracked 文件哈希与 tree、未知 untracked 文件，并要求
fast-forward。已经提交的删除只有在远端文件仍与旧提交一致时，才移入本地产物备份。
任何意外修改都会拒绝发布。执行目标保存在本地回执中，不公开。

不能用 force/reset 绕过分叉历史。验证后正常推送授权 remote：

```bash
git push origin main
```

## 文档与分发

README 图示使用仓库内 SVG，说明使用 Mermaid，不增加文档站构建依赖。中英页面成对
维护；原始测量共享一份证据。不上传凭据、真实录制或第三方包。注册表和 Release 附件
是独立交付，Git push 不等于已经发布安装包。
