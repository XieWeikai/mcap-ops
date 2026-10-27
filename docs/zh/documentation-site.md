# 文档站构建与发布

**语言：中文 | [English](../documentation-site.md)**

公开站点：<https://xieweikai.github.io/mcap-ops/>。
英文为默认语言，中文在 `/zh/` 下；语言切换器保留当前页面。
主要入口是学习用的 **Tutorials**、查询接口的 **Documentation**，
另有完整 **RSI** 工作手册。

## 唯一内容来源

| 来源 | 发布内容 |
| --- | --- |
| `docs/tutorials/` 与已有指南 | 循序渐进的学习路线 |
| `docs/reference/python/` | 14 个 Python 算子各自的接口页 |
| `docs/reference/types.md`、`rust.md` | 类型契约与全部公共 Rust 符号 |
| `docs/zh/` | 对应中文页面 |
| `RSI/`、`RSI/zh/` | 工作流、剖析、正确性、证据和模板 |
| Rust 源码 / `cargo doc` | 精确签名、字段、方法、trait 和源码链接 |
| `docs/performance/` | 链接到同版本 GitHub 源码的共享原始证据 |

构建时将维护中的 Markdown 暂存到 `.artifacts/docs/source/{en,zh}`，
用主题切换器替代 GitHub 文档里的语言链接行，
把源码/证据链接指向同一 Git 版本，并复制共享资源。
不增加第二份手工维护的指南或 RSI。原始实验日志不进入站点与搜索索引。

```mermaid
flowchart LR
    A["本地编写 / 审阅 / 提交"] --> B["同步 Linux 执行目录"]
    B --> C["示例 + 严格 MkDocs + cargo doc"]
    C --> D["链接 / 浏览器 / 隐私检查"]
    D --> E["取回静态产物"]
    E --> F["非强制推送 gh-pages"]
    F --> G["GitHub Pages 托管静态文件"]
```

## 构建与验证

所有构建/测试命令在配置的 Linux 执行环境的仓库根目录运行。
执行配置见[贡献指南](contributing.md)，部署坐标只保存在本地。

```bash
python3 -m venv .tools/docs
.tools/docs/bin/python -m pip install -r requirements-docs.txt
export CARGO_HOME="$PWD/.tools/cargo"
export RUSTUP_HOME="$PWD/.tools/rustup"
export PATH="$CARGO_HOME/bin:$PATH"
.venv/bin/python -m pytest -q tests
.tools/docs/bin/python scripts/build_docs.py
.tools/docs/bin/python scripts/check_docs_site.py
```

`build_docs.py` 严格检查 MkDocs，并将 rustdoc 警告视为错误；
在 `build.json` 记录源版本与 dirty 状态，最后扫描并拒绝包含执行目录
或 home 目录路径的产物。新增依赖只用于文档构建，不改变包的运行时依赖。

浏览器预览时，在执行环境中托管 `.artifacts/docs/site`，使用授权的本地隧道。
检查桌面/手机导航、内部页面语言切换、中英文搜索、代码复制、Mermaid 渲染、
Rust 符号链接。浏览器检查使用 Playwright 和项目内 Chromium，
它们是可选开发工具，不是站点构建依赖。
运行方法见 [check_docs_browser.py](../../scripts/check_docs_browser.py)。

## 发布

1. 本地提交已审阅源码，通过 `scripts/publish_remote.py` 同步并推送 `main`；
   本地、执行目录、GitHub 的源版本必须一致。
2. 在干净的执行目录重新构建，检查站点链接和浏览器，
   只将 `.artifacts/docs/site/` 复制回本地同名产物路径。
3. 本地使用已登录的 `gh` 运行 `python3 scripts/publish_docs.py`。
   脚本检查干净的源版本、完整产物和 GitHub main，然后在临时克隆里提交静态文件，
   非强制推送 `gh-pages`。本地不构建。
4. 一次性在仓库 **Settings > Pages** 选择 **Deploy from a branch**，
   `gh-pages`、`/ (root)`。`.nojekyll` 保留已构建文件；
   GitHub 原生 Pages 部署负责发布静态分支，无需 CI runner 访问执行环境。
5. 等待 Pages 部署成功，核对在线 `build.json`，验证实际 `/mcap-ops/` 路径。

源提交变化后必须重新从干净版本构建，dirty/过期产物会被拒绝。
如果 `gh-pages` 被并发更新，非快进推送会失败，不会覆盖它，应先检查变更。

## 编辑约定

- 中英文页面成对增加，并在 `mkdocs.yml` 中配置导航。
- 每个 Python 接口页必须有真实公共签名和生成数据的可运行示例；
  测试会对照安装包检查签名/默认值，执行两种语言的例子。
- 保留 Markdown 相对链接，保证文档在 GitHub 也可用。
- rustdoc 自动生成，不手工翻译或编辑；双语概念页解释同样的类型，
  链接到共享的精确参考。
- 不把历史包、源数据、私有产物或执行坐标放进静态分支；
  README 顶图仍使用原有共享矢量资源。
