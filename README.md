# Liverpool Squad Audit

以利物浦为案例的、可解释的足球阵容诊断小项目。

**第一阶段：2026–27 赛季截至 2026-11-11，先分析英超比赛，再检查位置覆盖，建立补强判断所需的证据。**

本仓库为第一版分析工具，不声称已完成利物浦的真实位置级补强结论。

## 已有功能

- 下载真实的英超比赛 CSV，核验字段、日期和重复比赛，并记录来源、下载时间及 SHA-256。
- 统一主客场视角，计算进失球、积分、xG、xGA、射门和单次射门 xG。
- 同期联赛对照、最近 5/8 场、主客场筛选，以及排除任一方出现红牌的整场比赛。
- 透明的比赛表现规则，每条线索展示指标、比较基准、触发阈值和解释限制。
- 导入真实球员位置分钟，检查多位置重复计算，统计完整比赛的位置使用和轮换集中度。
- 导出 Markdown/JSON 报告，以及用于采集阵容数据的比赛标识。
- 无第三方依赖的命令行分析核心、单元测试，以及 Streamlit 本地界面。

## 快速运行

参考环境为 Python 3.12.6（见 `.python-version`）。macOS/Linux 在项目目录执行：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock
python scripts/fetch_data.py --manifest reproducibility/baseline.json
python -m streamlit run app.py
```

Windows PowerShell 激活命令为 `.venv\Scripts\Activate.ps1`，其他步骤相同。也可直接用虚拟环境里的 Python。

项目不会请求 API 密钥或付费账户。首次下载需要网络；之后可使用本地快照离线分析。

完整复现流程：

```bash
make test
make reproduce
```

`make reproduce` 会验证输入快照与三个输出文件的 SHA-256，并生成独立的运行版本记录。直接执行 `python scripts/fetch_data.py` 会下载源站当前文件；带 `--manifest` 才会要求与本版本的固定输入一致。源站若已修改历史记录，请恢复原始数据备份，不能仅靠网址重建旧版本。

依赖锁记录传递依赖的包版本，未固定操作系统镜像和平台 wheel；详见 [复现说明](docs/REPRODUCIBILITY.md)。

### 不安装界面，只生成报告

```bash
python3 scripts/fetch_data.py
python3 scripts/report.py
python3 scripts/report.py --exclude-red --output reports/no-red
```

输出为 `reports/report.md`、`reports/report.json`、`reports/match_ids.csv`。`--as-of YYYY-MM-DD` 可设为同赛季的更早日期。

下载失败可从[数据源](https://www.football-data.co.uk/mmz4281/2627/E0.csv)手动保存到 `data/local/E0-2627.csv`，或在界面上传相同格式的 CSV。不要把另一个赛季改名当成当前赛季数据。

## 阵容数据怎么补

比赛 CSV 没有球员出场、伤停或战术角色，因此第一版默认将位置级判断标为“证据不足”。

1. 生成报告或在界面下载 `match_ids.csv`。
2. 复制 `data/templates/appearances.csv`。
3. 根据可靠比赛记录，为每位出场球员填入实际位置、常规时间分钟和来源链接。
4. 上传出场文件，或运行：

```bash
python3 scripts/report.py --appearances path/to/appearances.csv
```

字段：

| 字段 | 含义 |
|---|---|
| match_id | 使用程序输出的比赛标识，不自行改写 |
| player_id | 稳定球员 ID；同名球员不要合并 |
| player_name | 姓名 |
| role | GK/CB/LB/RB/DM/CM/AM/LW/RW/ST |
| minutes | 在该位置的常规时间分钟，大于 0 且不超过 90 |
| source_url | 支持这条记录的比赛记录或标注来源 |

如果同一球员先踢边后卫再踢后腰，应拆为两行且分钟之和不超过 90。同一场同一球员同一位置的多段出场先合并。只录入首发名单不等于完整出场数据；不要用报名位置代替实际比赛角色。

双方无红牌、全队分钟总和为 990 的比赛才计入完整比赛。该检查只是分钟完整性的最低要求，无法识别来源中本身的错误。红牌时段尚未重建，不会用于位置集中度判断。

## 如何解读规则

规则只产生**待核查线索**，不是经过训练的预测模型或因果推断：

| 线索 | 当前触发规则 |
|---|---|
| 机会创造 | 场均 xG 低于其他球队同期均值的 90% |
| 机会限制 | 场均 xGA 高于其他球队同期均值的 110% |
| 射门质量 | xG/射门低于其他球队同期值的 90% |
| 位置轮换集中 | 主力占该位置分钟至少 85%；至少 8 场完整记录且覆盖所选无红牌比赛的 80%；该位置也须出现至少 8 场 |

前三条分别要求对应指标至少有 8 场有效比赛。门槛是首版可审查的启发式参数，未做显著性检验或预测验证。

- 缺失值不是 0。xG 差只使用两边 xG 都有效的同场记录。
- 最近 N 场先选取，再排除红牌比赛，避免改变“最近 N 场”的含义。
- 参照为其他球队同期记录的场次加权均值，不是积分榜强队标准；含其对利物浦的记录，未校正赛程强弱。
- 不同比赛或不同数据商的 xG 模型不能随意混合。本项目保持同一数据源口径，源站未给出具体模型版本。
- 主力分钟集中可能源于能力、伤停、教练选择或阵型；未出场的替补不能当作不存在。
- CB/CM 等多人共同承担的角色，主力份额按该角色全部分钟计算，不直接代表替补人数。
- 没触发规则不表示没有缺陷。球队 xGA 高也不能自动归因给中卫或门将。

完整的方法边界和后续路线见 [docs/methodology.md](docs/methodology.md)。

## 项目结构

```text
app.py                    本地交互界面
audit.py                  数据校验、统计、规则和报告核心
scripts/fetch_data.py     公开比赛数据下载与来源记录
scripts/report.py         无依赖报告导出
data/templates/           球员位置分钟模板
data/local/               本地数据，不提交 Git
docs/methodology.md       方法说明与后续计划
tests/test_audit.py        数据正确性和规则边界测试
```

## 验证

```bash
python3 -m unittest discover -s tests -v
```

测试使用明确命名的合成球员和比赛，不用于真实分析。

## 上传到 GitHub

本项目已在本地初始化 Git，并将初始功能导入和可复现性改进分别提交。要保留这些历史，请使用当前本地项目文件夹，或从 Git bundle 克隆；网页上传文件与普通源码 ZIP 不包含这些提交历史。

在 [GitHub 新建仓库](https://github.com/new?name=liverpool-squad-audit)，Owner 选择 `Zhecen-Zhou0309`，名称为 `liverpool-squad-audit`。选择可见性，不初始化 README、License 或 `.gitignore`，然后创建空仓库。

在当前本地项目目录执行：

```bash
git remote -v
git push -u origin main
git push origin v0.1.0
```

当前本地项目的 origin 已设为 `https://github.com/Zhecen-Zhou0309/liverpool-squad-audit.git`；从 bundle 克隆时需先用 `git remote set-url origin` 改成这个地址。若普通源码 ZIP 解压后运行 `git status` 提示不是仓库，说明它不含历史，请改用 bundle。

命令行登录和 GitHub App 连接分别管理。若 push 要求认证，可先创建空仓库，再通过 GitHub Desktop 登录、添加当前本地仓库并推送；不要用账号密码代替 Git 的 HTTPS 认证。详见 [GitHub 上传指南](docs/GITHUB.md)。

上传前先看 `git status`：本地原始数据、虚拟环境、密钥与生成报告已通过 `.gitignore` 排除。发布的是独立项目仓库；本版无需 GitHub Pages。Python 界面通过本地命令启动。

后续开发流程见 [CONTRIBUTING.md](CONTRIBUTING.md)。每个 commit 对应一个可解释的变化；可复现性由代码版本、环境、数据和运行流程共同保证。

## 来源

- [Football-Data.co.uk 英格兰数据](https://www.football-data.co.uk/englandm.php)
- [2026–27 英超 CSV](https://www.football-data.co.uk/mmz4281/2627/E0.csv)
- [字段说明与上游来源](https://www.football-data.co.uk/notes.txt)
- [利物浦官方赛程](https://www.liverpoolfc.com/matches/mens-team/fixtures)

下载器仅使用比赛结果和统计，忽略源文件里的赔率字段。数据为第三方提供；源码许可不覆盖第三方数据。打包的源码不含原始比赛 CSV。

本项目与利物浦俱乐部无隶属关系。
