# 上传到 Zhecen-Zhou0309 的独立仓库

## 一次性发布

1. 打开 <https://github.com/new?name=liverpool-squad-audit>。
2. Owner 选 `Zhecen-Zhou0309`，Repository name 填 `liverpool-squad-audit`。公开作品可选 Public；希望先私下开发可选 Private。
3. 保持 README、License 和 `.gitignore` 初始化选项关闭，创建空仓库。
4. 打开当前本地项目目录的终端，检查并推送：

```bash
git status
git log --oneline
git remote -v
git push -u origin main
git push origin v0.1.0
```

当前本地仓库已配置 origin。推送成功后访问：<https://github.com/Zhecen-Zhou0309/liverpool-squad-audit>。检查 Commits、标签和 Actions 测试结果。

不要网页拖拽上传整个 ZIP：那样不能带上本地已有的 Git 提交历史。也不要重新执行 `git init` 并把所有文件重新压成一次初始提交。

## 使用带历史的备份

将 `liverpool-squad-audit-history.bundle` 保存到本地。下面以 Downloads 为例，若文件实际在其他位置需替换路径：

```bash
git clone -b main ~/Downloads/liverpool-squad-audit-history.bundle liverpool-squad-audit
cd liverpool-squad-audit
git remote set-url origin https://github.com/Zhecen-Zhou0309/liverpool-squad-audit.git
git push -u origin main
git push origin v0.1.0
```

Bundle 保留提交、作者、父子关系和标签，但不含忽略的原始数据。普通源码 ZIP 仅用于查看代码；输入数据另有独立备份。

## 不熟悉终端时

先按前面的网页步骤创建空仓库，再在 GitHub Desktop 登录 `Zhecen-Zhou0309`。通过 File → Add Local Repository 选择当前项目，再使用 Push origin 上传 main。这样保留已有 Git 历史；标签可用前面的 `git push origin v0.1.0` 命令推送。

App 内 GitHub 连接不会自动给系统 Git 配置 HTTPS/SSH 登录。如果终端要求认证，使用 GitHub Desktop 或已配置的 SSH/凭据管理器；GitHub 账号密码不能直接用于 Git HTTPS 推送。

## Commit 如何积累

下一步每完成一个有意义且可检查的修改就提交：例如补全一个数据导入器、修复一个分钟统计问题、增加一个边界测试、说明一项方法假设。

同一天创建多条 commit 会保留多条提交记录，但都属于当天。未来持续开发自然产生跨日期历史。Git 历史用于追溯代码，可复现性还需要锁定依赖和保留输入数据。

参考：[GitHub 官方本地项目上传说明](https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github)。
