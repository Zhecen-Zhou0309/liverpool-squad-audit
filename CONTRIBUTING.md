# 开发与提交

每次提交应解决一个明确问题，使后续分析能够追溯到具体代码变化。提交前运行与变更相关的测试；不要为了增加数量而提交空变更。

## 常规流程

```bash
git switch main
git pull --ff-only
git switch -c feat/appearance-import
```

完成一个功能单元后，查看差异并提交，例如：

```bash
python -m unittest discover -s tests -v
git diff
git add scripts/new_importer.py tests/test_new_importer.py
git commit -m "feat: import verified player appearances"
git push -u origin feat/appearance-import
```

示例中的文件须替换成实际修改过的文件。通过 Pull Request 说明问题、修改后行为和验证结果；如果希望 main 保留功能分支上的逐条提交，合并时使用保留提交历史的方式，而非 squash。

## 推荐的下一批工作

- 可靠来源的利物浦出场记录导入：首发、换人、实际常规时间。
- 比赛阵型与实际位置映射，处理同场换位。
- 独立球员名单与多位置替补覆盖，避免一个替补重复占两个空位。
- 有时间戳和原因分类的伤停/停赛数据。
- 转换防守和机会创造的事件区域或录像标注。
- 基于完整证据的补强角色画像。
- 对阈值做历史赛季回测与敏感性分析。

## Commit 风格

`feat:` 新功能；`fix:` 修复；`test:` 有意义的验证；`docs:` 说明；`build:` 环境；`ci:` 自动检查。

不要将数据文件更新、算法修改和界面调整无解释地混在一个 commit。更改模型或数据快照时保留旧基线并说明原因。
