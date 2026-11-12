# 可复现性

Commit 使代码变化可以追踪；要复现一份足球分析，还需要固定输入、分析参数和运行环境。

## 本版本保存了什么

| 层面 | 记录 |
|---|---|
| 代码 | 功能划分的 Git 提交、`v0.1.0` 标签 |
| 环境 | `.python-version`、全部已解析包版本 `requirements.lock`、参考系统信息 |
| 数据 | `reproducibility/baseline.json` 中的源站、下载时间、原始 CSV SHA-256 |
| 参数 | 利物浦、英超、2026–27、截止 2026-11-11、完整赛季至今、不排除红牌 |
| 结果 | Markdown、JSON 和比赛 ID 文件的 SHA-256 |
| 单次运行 | `run_metadata.json` 保存代码 commit、工作区状态、实际 Python/系统、依赖锁及输入输出哈希 |

所有初始导入提交均在本次准备过程中创建，反映功能分组，不代表过去不同日期的开发活动。后续环境锁定、数据验证、CI 和文档是实际新增改进。

## 重建基线

1. 在包含 Git 历史的项目中，定位到标签：

```bash
git switch --detach v0.1.0
```

2. 使用 Python 3.12.6；安装界面依赖时执行：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock
```

只运行分析核心和复现验证无需第三方包。

3. 恢复固定数据，或者尝试从源站下载并校验：

```bash
python scripts/fetch_data.py --manifest reproducibility/baseline.json
```

4. 测试并重建报告：

```bash
python -m unittest discover -s tests -v
python scripts/reproduce.py
```

成功时输出“复现通过”，报告位于 `reports/reproduced/`。执行过程不自动修改基线。

## 数据保留是必要条件

源站 CSV 会随赛季进展或历史修正而改变。SHA-256 可以识别同一文件，但不能把缺失的文件恢复出来。本仓库不提交原始第三方 CSV，所以仅克隆源码不能保证将来仍能从源站取到旧字节。

请长期保存本地 `data/local/E0-2627.csv` 和 `provenance.json`。本次交付还提供独立的 `liverpool-analysis-input-2026-11-11.zip` 输入备份；可将其恢复到项目根目录，里面已经包含 `data/local/` 路径。该备份与公开源码分开，不自动推送 GitHub。

要允许其他研究者复现真实比赛结果，应为同一输入提供持久、可访问且符合数据源使用条件的归档。暂时只有代码和合成测试可以完全从 Git 仓库重建。

## 更新数据或模型时

- 使用新的 commit 和新的分析日期，保留旧标签与原始输入。
- 先核查源文件变化，再生成新报告；不要为了让验证变绿而直接改旧哈希。
- 新基线同时记录新输入和新输出，并在 changelog 解释变化。
- 不要把当前数据用于过去时间点的可用性判断，避免信息泄漏。

## 边界

依赖锁固定包版本，未保存 wheel 哈希、全部 wheel 文件、系统库或容器镜像，不能声称操作系统级或二进制级完全一致。Python patch 版本已记录；跨平台情况应通过 CI 或其他机器运行后再确认。本地已经验证输入及输出文件一致，GitHub CI 需要首次上传后才会实际执行。
