# 运维手册 — RL-Reward-Lab

> 版本：v1.3.0 | 目标读者：值班运维工程师 | 原则：凌晨 3 点照着能恢复服务

## 1. 环境要求

| 项目 | 最低 | 推荐 |
|------|------|------|
| Docker Engine | 24.0+ | 26.0+ |
| Docker Compose | v2 (plugin) | v2.24+ |
| 宿主机 OS | Linux (x86_64) / Windows 11 Pro / macOS 13+ | Linux (Ubuntu 22.04 LTS) |
| CPU | 4 vCPU | 8 vCPU（HPO 场景） |
| RAM | 4 GB | 8 GB（并行 4 Run 训练） |
| 磁盘 | 10 GB 可用 | 50 GB+（长期 HPO 实验累积） |
| 网络 | 主机可访问 Docker Hub (拉取镜像) | — |

> **Windows 注意**：Docker Desktop 默认使用 WSL2 后端。确保 WSL2 已安装且分配了充足内存（`.wslconfig` 中 `memory=8GB`）。

---

## 2. 快速部署（单机 Docker Compose）

### 2.1 首次部署

```bash
# 1. 克隆项目
git clone https://github.com/Sher-ryKarl/RL-Reward-Lab.git
cd RL-Reward-Lab

# 2. 创建并编辑环境变量文件
cp .env.example .env
# 编辑 .env —— 至少修改以下三项：
#   RL_LAB_SECRET_KEY=<随机生成的长字符串>
#   RL_LAB_ADMIN_PASSWORD=<强密码>
#   RL_LAB_CORS_ORIGINS=<你的生产域名,默认 localhost>

# 3. 一键启动
docker compose up -d

# 4. 验证部署
curl http://localhost:8000/health
# 预期输出: {"status":"ok","version":"0.1.0"}

# 5. 检查容器状态
docker compose ps
# 预期: backend 和 frontend 均为 Up 状态
```

### 2.2 停止与重启

```bash
# 停止所有服务（保留数据）
docker compose down

# 重启
docker compose up -d

# 完全销毁（包括数据卷——危险！）
docker compose down -v
```

### 2.3 端口说明

| 服务 | 容器内端口 | 宿主机端口 | 环境变量 |
|------|-----------|-----------|----------|
| 前端 (Nginx) | 80 | `${FRONTEND_PORT:-80}` | `FRONTEND_PORT` |
| 后端 (Uvicorn) | 8000 | `${RL_LAB_PORT:-8000}` | `RL_LAB_PORT` |

修改端口示例：
```bash
# .env 中添加
RL_LAB_PORT=9090
FRONTEND_PORT=443
docker compose up -d  # 重新创建容器
```

### 2.4 Docker 拓扑

```
Browser ──► :80 (Nginx)
                │
                ├── /            → /usr/share/nginx/html (SPA 静态文件)
                ├── /api/        → proxy_pass http://backend:8000
                └── /api/v1/runs/→ proxy_pass + proxy_buffering off + read_timeout 3600s
                                        │
                                        ▼
                                  backend:8000 (Uvicorn)
                                        │
                                   ./data:/app/data (bind mount)
```

依据：`frontend/nginx.conf:1-33`、`docker-compose.yml:1-31`

---

## 3. 全部环境变量表

以下变量在 `.env` 文件中设置，所有以 `RL_LAB_` 为前缀。

### 3.1 核心配置

| 变量 | 默认值 | 作用 | 生产建议 |
|------|--------|------|----------|
| `RL_LAB_PORT` | `8000` | 后端监听端口 | 保持默认（仅容器内使用） |
| `RL_LAB_DEBUG` | `false` | SQLAlchemy echo + FastAPI debug | **必须为 `false`** |
| `RL_LAB_CORS_ORIGINS` | `http://localhost:5173,http://localhost` | 允许的跨域源（逗号分隔） | 改为实际域名，如 `https://rl.example.com` |

### 3.2 安全

| 变量 | 默认值 | 作用 | 生产建议 |
|------|--------|------|----------|
| `RL_LAB_SECRET_KEY` | `rl-lab-dev-secret-change-in-production` | JWT HS256 签名密钥 | **必须修改**：`openssl rand -hex 32` 生成 64 字符随机串 |
| `RL_LAB_ADMIN_PASSWORD` | `admin123` | 默认管理员密码 | **必须修改**：至少 12 位混合字符 |
| `RL_LAB_RATE_LIMIT` | `30/minute` | 写端点每 IP 速率限制 | 根据团队规模调整，`30/minute` 适合 1-5 人团队 |

### 3.3 数据库

| 变量 | 默认值 | 作用 | 生产建议 |
|------|--------|------|----------|
| `RL_LAB_DATABASE_URL` | `sqlite+aiosqlite:////app/data/rl_lab.db` | 元数据库连接串 | 单机保持默认；多副本切换 PostgreSQL |
| `RL_LAB_MLFLOW_TRACKING_URI` | `sqlite:////app/data/mlflow.db` | MLflow/Optuna 追踪存储 | 单机保持默认；可切换远程 MLflow Server |

### 3.4 训练控制

| 变量 | 默认值 | 作用 | 生产建议 |
|------|--------|------|----------|
| `RL_LAB_DEFAULT_TOTAL_STEPS` | `50000` | 新建实验默认训练步数 | 保持默认 |
| `RL_LAB_MAX_TOTAL_STEPS` | `2000000` | 单 Run 最大步数 (防止误操作) | 按需调整 |
| `RL_LAB_MAX_CONCURRENT_RUNS` | `4` | 同时训练的最大 Run 数 | ≤ CPU 核心数 − 2 |
| `RL_LAB_DEVICE` | `cuda` 或 `cpu`（自动检测） | PyTorch 设备 | GPU 服务器设为 `cuda` |

### 3.5 前端

| 变量 | 默认值 | 作用 |
|------|--------|------|
| `FRONTEND_PORT` | `80` | 前端 Nginx 宿主机端口 |

依据：`backend/app/config.py:9-44`、`.env.example:1-36`

---

## 4. 健康检查与监控

### 4.1 快速健康检查

```bash
# 后端健康检查（应用级别）
curl -s http://localhost:8000/health | jq
# 预期: {"status": "ok", "version": "0.1.0"}

# 前端可访问性
curl -s -o /dev/null -w "%{http_code}" http://localhost/
# 预期: 200

# 数据库文件存在性
docker compose exec backend ls -lh /app/data/rl_lab.db

# 容器运行状态
docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Health}}"
```

### 4.2 查看日志

```bash
# 实时跟踪后端日志
docker compose logs -f backend

# 查看最近 100 行
docker compose logs --tail=100 backend

# 查看特定时间范围的日志
docker compose logs --since=10m backend

# Nginx 访问日志
docker compose logs frontend | grep "GET /api"

# 训练错误日志
docker compose logs backend | grep "\[ERROR\]"
```

### 4.3 判断系统状态

| 症状 | 可能原因 | 检查命令 |
|------|----------|----------|
| `/health` 返回非 200 | 后端未启动或崩溃 | `docker compose ps backend` |
| `/health` 超时 | 后端卡死 (如 GPU 初始化挂起) | `docker compose logs --tail=50 backend` |
| `/health` 正常但前端 502 | Nginx 无法连接 backend | 检查 docker network：`docker compose exec frontend ping backend` |
| 前端加载白屏 | SPA 文件未正确构建 | `docker compose exec frontend ls /usr/share/nginx/html/` |
| 创建实验失败 | 数据库锁表或磁盘已满 | `df -h ./data/`、`docker compose logs backend \| grep sqlite` |

### 4.4 资源监控

```bash
# 容器资源使用
docker stats --no-stream

# 后端进程 CPU/内存
docker compose exec backend top -bn1 | head -20

# 数据目录磁盘使用
du -sh ./data/*
# 关注 mlruns/ 目录，MLflow 日志可能随时间增长
```

---

## 5. 数据备份与恢复

### 5.1 需要备份的内容

```
./data/
├── rl_lab.db             # 实验元数据 (User, Experiment, Run, Demo)
├── mlflow.db             # MLflow tracking + Optuna study
├── demos/                # 专家轨迹 .pkl 文件
├── videos/               # 策略回放 .mp4 文件（可选，可重建）
├── checkpoints/          # 训练模型 .zip 文件（可选，可重建）
├── custom_rewards.json   # 自定义奖励代码
└── tb/                   # TensorBoard 日志（可选）

./.env                    # 环境变量配置
```

### 5.2 备份命令

```bash
# 创建带时间戳的备份
BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# 方法 1：直接文件拷贝（服务必须停止）
docker compose down
cp -r ./data "$BACKUP_DIR/data"
cp ./.env "$BACKUP_DIR/.env"
docker compose up -d

# 方法 2：在线备份（SQLite 使用 .backup 命令，安全不锁表）
mkdir -p "$BACKUP_DIR"
docker compose exec -T backend sqlite3 /app/data/rl_lab.db ".backup '/tmp/rl_lab_backup.db'"
docker compose cp backend:/tmp/rl_lab_backup.db "$BACKUP_DIR/rl_lab.db"
docker compose exec backend sqlite3 /app/data/mlflow.db ".backup '/tmp/mlflow_backup.db'"
docker compose cp backend:/tmp/mlflow_backup.db "$BACKUP_DIR/mlflow.db"
cp -r ./data/demos "$BACKUP_DIR/demos" 2>/dev/null || true
cp -r ./data/videos "$BACKUP_DIR/videos" 2>/dev/null || true
cp ./data/custom_rewards.json "$BACKUP_DIR/" 2>/dev/null || true
cp ./.env "$BACKUP_DIR/.env"

# 创建压缩归档
tar -czf "$BACKUP_DIR.tar.gz" -C "$(dirname "$BACKUP_DIR")" "$(basename "$BACKUP_DIR")"
rm -rf "$BACKUP_DIR"
echo "Backup: $BACKUP_DIR.tar.gz ($(du -h "$BACKUP_DIR.tar.gz" | cut -f1))"
```

### 5.3 恢复命令

```bash
# 1. 停止服务
docker compose down

# 2. 解压备份
tar -xzf ./backups/20260502_030000.tar.gz -C /tmp/restore/
# 或者从目录恢复：
# RESTORE_DIR="./backups/20260502_030000"

# 3. 恢复数据文件
rm -rf ./data  # 危险！确保备份已解压成功
cp -r /tmp/restore/20260502_030000/data ./data
cp /tmp/restore/20260502_030000/.env ./.env

# 4. 重启服务
docker compose up -d

# 5. 验证
curl http://localhost:8000/health
```

### 5.4 自动化备份建议

```bash
# 添加到 crontab (每天凌晨 3:00 执行)
# crontab -e
0 3 * * * /opt/rl-reward-lab/scripts/backup.sh >> /var/log/rl-backup.log 2>&1

# scripts/backup.sh 内容：
# #!/bin/bash
# cd /opt/rl-reward-lab
# BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
# mkdir -p "$BACKUP_DIR"
# docker compose exec -T backend sqlite3 /app/data/rl_lab.db ".backup '/tmp/rl_lab_backup.db'"
# docker compose cp backend:/tmp/rl_lab_backup.db "$BACKUP_DIR/rl_lab.db"
# docker compose exec backend sqlite3 /app/data/mlflow.db ".backup '/tmp/mlflow_backup.db'"
# docker compose cp backend:/tmp/mlflow_backup.db "$BACKUP_DIR/mlflow.db"
# cp ./data/custom_rewards.json "$BACKUP_DIR/" 2>/dev/null || true
# cp ./.env "$BACKUP_DIR/"
# tar -czf "$BACKUP_DIR.tar.gz" -C ./backups "$(basename "$BACKUP_DIR")"
# rm -rf "$BACKUP_DIR"
# # 保留最近 30 天
# find ./backups -name "*.tar.gz" -mtime +30 -delete
# echo "[$(date)] Backup complete: $BACKUP_DIR.tar.gz"
```

### 5.5 备份策略建议

| 策略 | 频率 | 保留 |
|------|------|------|
| 全量备份 | 每日 | 最近 30 天 |
| 周备份 | 每周日 | 最近 12 周 |
| 发布前备份 | 每次部署前 | 永久 |

---

## 6. 升级与回滚

### 6.1 常规升级

```bash
# 1. 备份数据（必须！）
# 按 5.2 节执行在线备份

# 2. 拉取最新代码
git pull origin main

# 3. 检查 .env.example 是否有新增变量
diff .env.example .env
# 如有新增变量，手动添加到 .env

# 4. 重新构建并启动
docker compose down
docker compose build --no-cache
docker compose up -d

# 5. 验证
curl http://localhost:8000/health
docker compose logs --tail=20 backend | grep -E "ERROR|WARNING"
```

### 6.2 回滚到指定版本

```bash
# 1. 停止服务
docker compose down

# 2. 检出目标版本
git checkout v1.3.0          # 或者 git checkout <commit-hash>

# 3. 重建
docker compose build --no-cache
docker compose up -d

# 4. 验证
curl http://localhost:8000/health

# 5. 如需恢复数据，按 5.3 节执行
```

### 6.3 数据库迁移

本项目使用**自动幂等迁移**（无需手动跑迁移脚本）。`init_db()` 在每次后端启动时执行：

1. `CREATE TABLE IF NOT EXISTS`（通过 SQLAlchemy `Base.metadata.create_all`）
2. 对新增列执行 `ALTER TABLE ADD COLUMN`（try/except 跳过已存在的列）
3. 种子 admin 用户（如果不存在）
4. 将旧数据（无 `user_id`）归属到 admin

依据：`backend/app/db/database.py:30-88`

> **注意**：迁移是追加式（additive-only）。不会执行 DROP COLUMN 或类型修改。如需破坏性迁移，需手动操作 SQLite。

---

## 7. 生产环境检查清单

上生产前逐项确认：

### 安全

- [ ] `RL_LAB_SECRET_KEY` 已修改（`openssl rand -hex 32` 生成）
- [ ] `RL_LAB_ADMIN_PASSWORD` 已修改（≥12 位，混合大小写+数字+符号）
- [ ] `RL_LAB_DEBUG=false`（禁止在生产开启 debug 日志）
- [ ] `RL_LAB_CORS_ORIGINS` 限定为实际域名（非通配符 `*`）
- [ ] `RL_LAB_RATE_LIMIT` 已按团队规模设置
- [ ] 如暴露在公网：已在 Nginx 前加 HTTPS 反代（如 Nginx Proxy Manager / Traefik / Caddy）

### 数据

- [ ] 备份脚本已部署并通过测试（手动跑一次 `scripts/backup.sh` 验证）
- [ ] `./data/` 目录有足够的磁盘空间（`df -h`）
- [ ] 如使用 PostgreSQL：连接串、密码、连接池大小已配置

### 运维

- [ ] 健康检查端点可从监控系统访问（Prometheus Blackbox / Uptime Kuma / Nagios）
- [ ] Docker daemon 已配置 `restart: unless-stopped`（docker-compose.yml 中已默认设置）
- [ ] 日志轮转已配置（`/etc/docker/daemon.json` 中 `log-opts.max-size`）
- [ ] 宿主机防火墙仅开放必要端口（80/443，后端 8000 仅本地或内网访问）

### 性能

- [ ] `RL_LAB_MAX_CONCURRENT_RUNS` ≤ CPU 核心数 − 2
- [ ] GPU 环境：`RL_LAB_DEVICE=cuda` + nvidia-docker 已安装
- [ ] 首次 HPO 实验前：估算磁盘空间（每个 Trial 约产生 10-50MB MLflow 日志）

---

## 8. 故障排除

### 8.1 启动问题

**问题：`docker compose up -d` 后前端返回 502 Bad Gateway**

```bash
# 原因：后端尚未完成初始化
# 解决：等待 30-60 秒后重试（init_db 需要建表 + 种子数据）
docker compose logs backend | tail -5
# 看到 "Application startup complete" 即表示就绪
```

**问题：首次启动时 MLflow 报错 `unable to open database file`**

```bash
# 原因：./data 目录权限不足
# 解决：
chmod 755 ./data
docker compose down && docker compose up -d
```

**问题：Windows Docker Desktop 路径挂载失败**

```bash
# 原因：Windows 路径格式不兼容或 WSL2 未运行
# 解决：
# 1. 确保在 WSL2 终端中执行（非 PowerShell/cmd）
# 2. 确保项目在 WSL2 文件系统中（如 /home/user/projects/），而非 /mnt/c/
# 3. Docker Desktop Settings → Resources → File Sharing 中添加项目路径
```

### 8.2 运行时问题

**问题：训练失败，日志显示 `sqlite3.OperationalError: database is locked`**

```bash
# 原因：并发写入 SQLite（如多个 Run 同时结束写入 final_metrics）
# SQLite 只支持单写者，高并发下偶发锁冲突
# 解决：
# 1. 降低 RL_LAB_MAX_CONCURRENT_RUNS
# 2. 或切换到 PostgreSQL（设置 RL_LAB_DATABASE_URL）
docker compose down
# 编辑 .env: RL_LAB_MAX_CONCURRENT_RUNS=2
docker compose up -d
```

**问题：后端 OOM（内存溢出）被 Docker 杀死**

```bash
docker compose logs backend | grep "Killed"
# 原因：并行训练 + 大模型占用超限
# 解决：增加 Docker 内存限制或降低并发
# docker-compose.yml 中添加：
#   backend:
#     deploy:
#       resources:
#         limits:
#           memory: 8G
```

**问题：端口冲突（`bind: address already in use`）**

```bash
# 检查占用端口的进程
netstat -tlnp | grep -E ":(80|8000)\s"
# 或: lsof -i :80 -i :8000

# 解决：修改 .env 中端口或停止冲突进程
echo "RL_LAB_PORT=9090" >> .env
echo "FRONTEND_PORT=8080" >> .env
docker compose down && docker compose up -d
```

### 8.3 数据问题

**问题：`custom_rewards.json` 损坏导致后端启动失败**

```bash
# 解决：备份后重置
docker compose exec backend cp /app/data/custom_rewards.json /app/data/custom_rewards.json.bak
docker compose exec backend sh -c 'echo "{}" > /app/data/custom_rewards.json'
docker compose restart backend
# 注意：所有用户的自定义奖励将丢失，需重新创建
```

**问题：MLflow DB 过大（超过 1GB）**

```bash
# 查看大小
ls -lh ./data/mlflow.db

# 解决：清理已完成的 HPO study（保留实验元数据）
docker compose exec backend sqlite3 /app/data/mlflow.db \
  "SELECT study_name, COUNT(*) FROM trials GROUP BY study_name;"
# 手动删除不需要的 study（谨慎！）
# 或直接删除 mlflow.db 并重启（会丢失 Optuna study 历史，但不影响 Run 记录）
```

### 8.4 已知限制

| 限制 | 影响 | 绕过方案 |
|------|------|----------|
| SQLite 单写者锁 | 高并发 (>4 Run) 时可能 `database is locked` | 降低并发数或切换 PostgreSQL |
| 无 GPU 自动检测 (Docker) | 默认 fallback 到 CPU | 设置 `RL_LAB_DEVICE=cuda` + nvidia-docker |
| Windows spawn 子进程 | 每个子进程重新 import 所有模块，启动慢 3-5 秒 | 正常现象，非故障 |
| 无 HTTPS 终止 | 默认 Nginx 仅监听 HTTP | 前置 Nginx Proxy Manager / Caddy / Traefik |
| 无多副本支持 | `./data` bind mount 不支持多容器共享 | 切换到 PostgreSQL + NFS/Docker Volume |
| BC 训练依赖 `demo_path` | 超参中必须有 `demo_path` 字段，否则报错 | 通过 UI 创建 BC 实验自动注入 |

---

## 9. PostgreSQL 迁移指南

### 9.1 迁移步骤

```bash
# 1. 停止服务
docker compose down

# 2. 编辑 .env
# RL_LAB_DATABASE_URL=postgresql+asyncpg://user:password@host:5432/rl_lab
# (需要提前在 PostgreSQL 中创建数据库 rl_lab)

# 3. 启动（init_db 会自动建表）
docker compose up -d

# 4. 验证
docker compose logs backend | grep -i "postgresql\|migration"
```

### 9.2 数据迁移 (SQLite → PostgreSQL)

```bash
# 使用 pgloader 或手动导出/导入
# 1. 导出 SQLite 数据
docker compose exec backend sqlite3 /app/data/rl_lab.db .dump > ./rl_lab_dump.sql

# 2. 根据 PostgreSQL 语法调整 dump 文件
# (修改引号、AUTOINCREMENT、datetime 函数等)

# 3. 导入到 PostgreSQL
# psql -h host -U user -d rl_lab -f ./rl_lab_dump.sql
```

---

## 10. HTTPS 配置示例（Nginx Proxy Manager）

如使用 [Nginx Proxy Manager](https://nginxproxymanager.com/)：

```
# Docker Compose 中添加：
#   backend:
#     expose:
#       - "8000"  # 只暴露给内部网络，不映射宿主机端口
#   frontend:
#     expose:
#       - "80"

# Nginx Proxy Manager 中：
# - Domain: rl.yourdomain.com
# - Forward Host: frontend
# - Forward Port: 80
# - SSL: Request a new SSL Certificate (Let's Encrypt)
# - Force SSL: ON
```

---

## 11. 附录：关键文件路径

| 文件 | 路径 | 用途 |
|------|------|------|
| 环境变量 | `./.env` | 所有可配置参数 |
| Docker Compose | `./docker-compose.yml` | 服务编排 |
| 后端 Dockerfile | `./backend/Dockerfile` | 后端镜像构建 |
| 前端 Dockerfile | `./frontend/Dockerfile` | 前端多阶段构建 |
| Nginx 配置 | `./frontend/nginx.conf` | 反向代理 + SPA fallback + SSE |
| 数据库 | `./data/rl_lab.db` | SQLite 元数据 |
| MLflow 数据库 | `./data/mlflow.db` | Optuna study + MLflow 日志 |
| 自定义奖励 | `./data/custom_rewards.json` | 用户自定义奖励代码 |
| 训练模型 | `./data/checkpoints/` | 训练完成的模型 .zip |
| 回放视频 | `./data/videos/` | 策略回放 .mp4 |
| 专家轨迹 | `./data/demos/` | BC 训练所用的轨迹 .pkl |
| 后端日志 | Docker stdout (`docker compose logs backend`) | 应用日志 |
