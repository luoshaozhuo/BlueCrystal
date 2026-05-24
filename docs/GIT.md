# Git Commit 信息前缀规范

Git 提交信息的前缀没有强制规定，但业界存在约定俗成的规范。常见主要有以下几种流派：

---

## 1. Conventional Commits（最流行）

这是目前最广泛使用的规范，被 Angular、Vue、React 等大型项目采用。

### 常用 type 类型

| Type      | 说明                         | 示例                                      |
|-----------|------------------------------|-------------------------------------------|
| feat      | 新功能                       | feat(opcua): 添加 fleet_runtime 仿真器     |
| fix       | Bug 修复                     | fix(parser): 修复 SCL 文件解析错误         |
| docs      | 文档更新                     | docs: 更新 OPC UA 集成指南                 |
| style     | 代码格式（不影响功能）       | style: 格式化代码缩进                     |
| refactor  | 重构（非新功能、非修 bug）   | refactor: 重构 OPC UA 客户端连接逻辑       |
| perf      | 性能优化                     | perf: 优化数据批量处理性能                 |
| test      | 测试相关                     | test: 添加 opcua_sim 单元测试             |
| chore     | 构建/工具/依赖等杂项         | chore: 更新 pyproject.toml 依赖           |
| ci        | CI/CD 配置                   | ci: 配置 GitHub Actions                  |
| build     | 构建系统或外部依赖           | build: 更新 setuptools 配置               |

---

## 2. 简化版（小型项目常用）

适用于无需严格规范的小型项目：

```bash
git commit -m "添加 OPC UA 仿真器运行时"
git commit -m "修复配置文件路径错误"
git commit -m "更新测试文档"
git commit -m "重构 fleet_runtime 模块"
```

## 3. Gitmoji（趣味性）

使用 emoji 作为前缀，直观易读：
✨ feat: 实现仿真器
🐛 fix: 修复连接超时问题
📝 docs: 更新 API 文档
✅ test: 添加单元测试
🔧 chore: 更新配置文件

# Git 常用命令大全

## SSH 密钥配置（首次使用 GitHub 必做）

在新机器上首次使用 GitHub 时，需要生成 SSH 密钥并将公钥添加到 GitHub。

### 1. 生成 SSH 密钥

```bash
ssh-keygen -t ed25519 -C "备注说明" -f ~/.ssh/id_ed25519 -N ""
```

- `-N ""` 表示不设置密码短语，直接回车
- 生成后文件在 `~/.ssh/id_ed25519`（私钥）和 `~/.ssh/id_ed25519.pub`（公钥）

### 2. 将公钥添加到 GitHub

```bash
# 查看公钥内容，复制全部输出
cat ~/.ssh/id_ed25519.pub
```

打开 [https://github.com/settings/ssh/new](https://github.com/settings/ssh/new)，粘贴公钥内容，点击 **Add SSH key**。

### 3. 验证连接

```bash
ssh -T git@github.com
# 成功输出：Hi <username>! You've successfully authenticated...
```

### 4. 确认远程仓库使用 SSH 地址

```bash
git remote -v
# 应显示 git@github.com:... 开头，而不是 https://
```

若为 HTTPS 地址，切换为 SSH：

```bash
git remote set-url origin git@github.com:<username>/<repo>.git
```

### HTTPS 方式（备选）

若不想配置 SSH，也可用 HTTPS + Personal Access Token（PAT）：

```bash
# 切换远程地址为 HTTPS
git remote set-url origin https://github.com/<username>/<repo>.git

# push 时输入用户名，密码处填写 PAT（不是账号密码）
# PAT 在 GitHub → Settings → Developer settings → Personal access tokens 生成
```

---

## 基础配置

```bash
# 设置用户名和邮箱
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# 查看配置信息
git config --list

# 设置默认编辑器
git config --global core.editor "code --wait"

# 设置别名（简化命令）
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.st status
git config --global alias.lg "log --oneline --graph --all"
```

## 仓库管理

```bash
# 初始化新仓库
git init

# 克隆远程仓库
git clone <repository-url>
git clone <repository-url> <directory-name>  # 克隆到指定目录
git clone --depth 1 <repository-url>  # 浅克隆（只下载最新提交）

#添加远程仓库
git remote add origin <repository-url>
git remote add upstream <repository-url>  # 添加上游仓库

# 查看远程仓库
git remote -v
git remote show origin
```

## 基本操作

```bash
# 查看状态
git status
git status -s  # 简洁模式

# 添加文件到暂存区
git add <file>           # 添加单个文件
git add .                # 添加所有文件
git add *.py             # 添加所有 Python 文件
git add -A               # 添加所有变更（包括删除）
git add -p               # 交互式添加（按块选择）

# 提交
git commit -m "message"           # 提交并写消息
git commit -am "message"          # 跳过暂存区直接提交（仅已跟踪文件）
git commit --amend                # 修改最后一次提交
git commit --amend --no-edit      # 修改提交但不改消息

# 删除文件
git rm <file>            # 删除文件并暂存删除操作
git rm --cached <file>   # 停止追踪文件但保留在本地

# 移动/重命名文件
git mv <old-name> <new-name>
```

## 查看历史

``` bash
# 查看提交历史
git log
git log --oneline               # 一行显示
git log --graph                 # 图形化显示
git log --oneline --graph --all # 完整图形化历史
git log -n 5                    # 只看最近5次提交
git log --author="name"         # 按作者筛选
git log --grep="keyword"        # 按关键词搜索

# 查看每次提交的修改
git log -p

# 查看某个文件的修改历史
git log -p <file>

# 查看谁改了什么（逐行标注）
git blame <file>

# 查看当前状态（简洁版）
git status -sb
```

## 分支管理

```bash
# 查看分支
git branch                 # 本地分支
git branch -r              # 远程分支
git branch -a              # 所有分支（本地+远程）
git branch -v              # 查看分支及最后提交

# 创建分支
git branch <branch-name>           # 创建分支
git checkout -b <branch-name>      # 创建并切换
git switch -c <branch-name>        # 新版Git推荐方式

# 切换分支
git checkout <branch-name>         # 传统方式
git switch <branch-name>           # 新版方式

# 合并分支
git merge <branch-name>            # 合并到当前分支
git merge --no-ff <branch-name>    # 不使用快进合并
git merge --abort                  # 取消合并

# 删除分支
git branch -d <branch-name>        # 删除已合并的分支
git branch -D <branch-name>        # 强制删除
git push origin --delete <branch-name>  # 删除远程分支

# 重命名分支
git branch -m <old-name> <new-name>
```

## 远程操作

```bash
# 拉取远程更新
git fetch                    # 拉取但不合并
git fetch origin             # 拉取指定远程仓库
git fetch --all              # 拉取所有远程仓库

# 拉取并合并
git pull                     # 拉取并合并（fetch + merge）
git pull --rebase            # 拉取并变基（fetch + rebase）
git pull origin main

# 推送
git push                     # 推送到默认远程
git push origin <branch>     # 推送到指定分支
git push -u origin <branch>  # 推送并设置上游分支
git push --force             # 强制推送（慎用）
git push --force-with-lease  # 更安全的强制推送

# 删除远程分支
git push origin --delete <branch>
```

## 撤销与恢复

```bash
# 撤销工作区的修改（未暂存）
git checkout -- <file>       # 传统方式
git restore <file>           # 新版方式

# 撤销暂存区的修改（已 add 未 commit）
git reset HEAD <file>        # 传统方式
git restore --staged <file>  # 新版方式

# 撤销提交（保留修改）
git reset --soft HEAD~1      # 撤销最后一次提交，修改回到暂存区
git reset --soft HEAD~3      # 撤销最近3次提交

# 撤销提交（丢弃修改）
git reset --hard HEAD~1      # 撤销最后一次提交，丢弃所有修改（危险）

# 撤销提交但保留工作区修改
git reset --mixed HEAD~1     # 默认行为，修改回到工作区

# 恢复被删除的提交
git reflog                   # 查看所有历史操作
git reset --hard <commit-id> # 恢复到指定提交

# 撤销合并
git reset --hard ORIG_HEAD   # 撤销最近一次合并
```

## 暂存（Stash）

```bash
# 保存当前工作进度
git stash                    # 默认保存
git stash save "message"     # 带消息保存
git stash push -m "message"  # 新版方式

# 查看暂存列表
git stash list

# 恢复暂存
git stash pop                # 恢复并删除暂存
git stash apply              # 恢复但不删除暂存
git stash apply stash@{1}    # 恢复指定的暂存

# 删除暂存
git stash drop               # 删除最新暂存
git stash drop stash@{1}     # 删除指定暂存
git stash clear              # 清空所有暂存

# 从暂存创建分支
git stash branch <branch-name>
```

## 变基（Rebase）

```bash
# 变基操作
git rebase <branch>                    # 将当前分支变基到目标分支
git rebase -i HEAD~3                   # 交互式变基最近3次提交
git rebase --continue                  # 解决冲突后继续
git rebase --abort                     # 取消变基
git rebase --skip                      # 跳过当前提交

# 常用交互式变基操作（在编辑器中使用）
# pick   - 使用提交
# reword - 使用提交但修改消息
# edit   - 使用提交但停止修改
# squash - 使用提交但合并到前一个提交
# fixup  - 同 squash 但丢弃消息
# drop   - 删除提交
```

## 差异对比 

```bash
# 查看工作区与暂存区的差异
git diff

# 查看暂存区与上次提交的差异
git diff --staged
git diff --cached

# 查看工作区与上次提交的差异
git diff HEAD

# 查看两次提交的差异
git diff <commit1> <commit2>

# 查看两个分支的差异
git diff <branch1> <branch2>

# 查看某个文件的差异
git diff -- <file>

# 统计差异信息
git diff --stat
```

## 调试与诊断

```bash
# 二分查找定位问题提交
git bisect start
git bisect bad                 # 标记当前提交有问题
git bisect good <commit>       # 标记正常提交
git bisect reset               # 结束二分查找

# 查找特定代码是谁改的
git blame <file>

# 搜索包含特定字符串的提交
git grep "search-text"
git grep -n "search-text"      # 显示行号

# 查看提交的详细信息
git show <commit-id>
git show <branch-name>
```

## 常用工作流程示例
```bash
# 标准开发流程
git checkout -b feature/new-feature
# ... 编写代码 ...
git add .
git commit -m "feat: add new feature"
git push -u origin feature/new-feature

# 同步主分支最新代码
git checkout main
git pull origin main
git checkout feature/new-feature
git rebase main
# 解决冲突后
git add .
git rebase --continue
git push --force-with-lease

# 合并到主分支
git checkout main
git merge --no-ff feature/new-feature
git push origin main

# 紧急修复流程
git checkout main
git pull origin main
git checkout -b hotfix/critical-bug
# ... 修复代码 ...
git add .
git commit -m "fix: critical bug fix"
git push -u origin hotfix/critical-bug
# 合并到 main 后
git checkout main
git merge --no-ff hotfix/critical-bug
git push origin main
```