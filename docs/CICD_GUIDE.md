# GitHub Actions CI/CD 部署指南

## 目标

```
git push main → GitHub Actions 自动构建镜像 → 推送 GHCR → SSH 服务器 helm upgrade
```

不再需要你手动 build / push / SSH 部署。

---

## 一、准备工作

### 1.1 生成服务器的 SSH 专用密钥（本地电脑）

```powershell
ssh-keygen -t ed25519 -f C:\Users\morni\.ssh\github-actions-worktime -N '""' -C "github-actions-worktime"
```

这会生成两个文件：
- `C:\Users\morni\.ssh\github-actions-worktime`（私钥）
- `C:\Users\morni\.ssh\github-actions-worktime.pub`（公钥）

### 1.2 把公钥放到服务器上

```powershell
type C:\Users\morni\.ssh\github-actions-worktime.pub | ssh root@43.155.140.124 "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
```

验证免密登录：

```powershell
ssh -i C:\Users\morni\.ssh\github-actions-worktime root@43.155.140.124 "echo ok"
```

输出 `ok` 即成功。

### 1.3 生成 GitHub Personal Access Token

1. 打开 `https://github.com/settings/tokens`
2. 点击 "Generate new token (classic)"
3. Note 填 `worktime-ci`
4. 勾选 `write:packages` 和 `delete:packages`
5. 生成后**复制保存**，只显示一次

---

## 二、配置 GitHub Secrets

打开 `https://github.com/morningsunzzz/worktime-app/settings/secrets/actions`

点击 "New repository secret"，依次添加 4 个：

| Secret 名称 | 值 |
|-------------|-----|
| `GHCR_TOKEN` | 上一节生成的 GitHub Personal Access Token |
| `SSH_HOST` | `43.155.140.124` |
| `SSH_USER` | `root` |
| `SSH_PRIVATE_KEY` | 私钥文件**完整内容**（包括 `-----BEGIN-----` 到 `-----END-----`） |

获取私钥内容：

```powershell
Get-Content C:\Users\morni\.ssh\github-actions-worktime -Raw
```

---

## 三、创建 GitHub Actions Workflow

在项目根目录创建 `.github/workflows/deploy.yml`，内容如下：

```yaml
name: Build and Deploy

on:
  push:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_BACKEND: ghcr.io/morningsunzzz/worktime-backend
  IMAGE_FRONTEND: ghcr.io/morningsunzzz/worktime-frontend

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GHCR_TOKEN }}

      - name: Generate image tag
        id: tag
        run: echo "TAG=$(date +%Y%m%d-%H%M)" >> $GITHUB_OUTPUT

      - name: Build and push backend
        uses: docker/build-push-action@v5
        with:
          context: ./backend
          push: true
          tags: |
            ${{ env.IMAGE_BACKEND }}:${{ steps.tag.outputs.TAG }}
            ${{ env.IMAGE_BACKEND }}:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Build and push frontend
        uses: docker/build-push-action@v5
        with:
          context: ./frontend
          push: true
          tags: |
            ${{ env.IMAGE_FRONTEND }}:${{ steps.tag.outputs.TAG }}
            ${{ env.IMAGE_FRONTEND }}:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Deploy to server
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.SSH_HOST }}
          username: ${{ secrets.SSH_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /opt/worktime-app
            git pull
            helm upgrade worktime ./helm/worktime -n worktime \
              --reuse-values \
              --set backend.image=${{ env.IMAGE_BACKEND }}:latest \
              --set frontend.image=${{ env.IMAGE_FRONTEND }}:latest
            kubectl rollout status deploy/worktime-backend -n worktime --timeout=60s
            kubectl rollout status deploy/worktime-frontend -n worktime --timeout=60s
```

---

## 四、提交并测试

```bash
git add .github/workflows/deploy.yml
git commit -m "ci: add GitHub Actions deploy workflow"
git push
```

推送后：

1. 打开 `https://github.com/morningsunzzz/worktime-app/actions`
2. 看到名称为 "Build and Deploy" 的 workflow 正在运行
3. 点进去看实时日志
4. 全部绿色 ✓ 即成功

---

## 五、验证

```bash
curl -s http://43.155.140.124:30080/api/health
# → {"status":"ok"}

curl -s -o /dev/null -w "%{http_code}" http://43.155.140.124:30080/
# → 200
```

---

## 六、日常使用

之后改完代码只需：

```bash
git add .
git commit -m "feat: xxx"
git push
```

剩下的全自动：构建镜像 → 推送 GHCR → 部署到服务器。在 GitHub Actions 页面可以看到每次部署的状态和日志。

如果想回滚，在 Actions 历史里找到上一次成功的 run，手动重新执行就行。
