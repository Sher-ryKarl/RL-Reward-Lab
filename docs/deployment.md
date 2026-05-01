# 部署指南

RL-Reward-Lab 支持 Docker Compose 一键部署和本地开发两种模式。

## Docker Compose（推荐）

**前置条件**: Docker 20.10+, Docker Compose v2

```bash
git clone <repo-url> && cd RL-Reward-Lab
docker compose up -d
```

### 服务端口

| 服务 | 地址 | 说明 |
|---|---|---|
| 前端 (Nginx) | http://localhost | SPA + API 反向代理 |
| 后端 (FastAPI) | http://localhost:8000 | 仅内部暴露（Nginx 代理） |
| 健康检查 | http://localhost:8000/health | 后端可用性 |

### 数据持久化

数据目录通过 volume 挂载到宿主机 `./data/`：

| 路径 | 内容 |
|---|---|
| `./data/rl_lab.db` | SQLite 数据库（实验/运行/Demo） |
| `./data/mlruns/` | MLflow tracking 数据 |
| `./data/videos/` | 训练策略回放 mp4 |
| `./data/demos/` | BC 专家轨迹 .npz |
| `./data/custom_rewards.json` | 自定义奖励函数持久化 |

### 环境变量

复制 `.env.example` 为 `.env` 后修改：

```bash
cp .env.example .env
```

主要变量：

| 变量 | 默认值 | 说明 |
|---|---|---|
| `RL_LAB_DATABASE_URL` | `sqlite+aiosqlite:////app/data/rl_lab.db` | 数据库连接 |
| `RL_LAB_MLFLOW_TRACKING_URI` | `sqlite:////app/data/mlruns.db` | MLflow 追踪 URI |
| `RL_LAB_CORS_ORIGINS` | `http://localhost:5173,http://localhost` | CORS 允许域 |
| `RL_LAB_HOST` | `0.0.0.0` | 后端监听地址 |
| `RL_LAB_PORT` | `8000` | 后端端口 |

### 运行测试

```bash
docker compose exec backend uv run pytest backend/tests/ -q
```

### 查看日志

```bash
docker compose logs -f backend   # 后端日志
docker compose logs -f frontend  # Nginx 日志
```

## 本地开发

**前置条件**: Python ≥3.10, Node ≥18, uv

```bash
# Python 环境
pip install uv
uv pip install --system -e ".[dev]"

# 前端依赖
cd frontend && npm install --legacy-peer-deps && cd ..

# Terminal 1: 后端
uv run uvicorn app.main:app --reload --port 8000

# Terminal 2: 前端
cd frontend && npm run dev
```

打开 http://localhost:5173。

### 开发模式差异

- 前端 Vite dev server 自动代理 `/api` → `localhost:8000`
- 后端 uvicorn `--reload` 监听文件变更自动重启
- CORS 默认允许 `localhost:5173`（Vite 端口）

## Docker 架构

```
client (browser)
    │
    ▼
┌──────────┐   /api/*  proxy   ┌──────────┐
│  Nginx   │ ────────────────► │  FastAPI  │
│  :80     │ ◄──────────────── │  :8000    │
│  (SPA)   │   SSE response    │           │
└──────────┘                   │  ┌─────┐  │
                               │  │Optuna│  │
                               │  │ HPO  │  │
                               │  └─────┘  │
                               │  ┌───────┐│
                               │  │SubProc││
                               │  │Worker ││
                               │  └───────┘│
                               └──────────┘
```

### Nginx 配置要点

- `/` → SPA 静态文件（try_files fallback 到 index.html）
- `/api/` → `backend:8000` 反向代理
- SSE 长连接配置：`proxy_buffering off; proxy_read_timeout 3600s`

### 后端 Dockerfile 要点

- 基础镜像 `python:3.10-slim`
- 预装 OpenGL 库（SB3 视频录制需要 `libgl1`）
- pip install 使用预生成的 `requirements.txt`（避免容器内 uv 兼容性问题）
- 数据库/MLflow 数据写入 `/app/data/`

## 生产部署注意事项

1. **数据库**: 当前使用 SQLite，生产环境建议切换 PostgreSQL（设置 `RL_LAB_DATABASE_URL` 为 PostgreSQL 连接串，需要额外安装 `psycopg2`）
2. **MLflow**: 生产环境建议使用独立的 MLflow Tracking Server
3. **CORS**: 设置 `RL_LAB_CORS_ORIGINS` 为生产域名
4. **认证**: v1.0.0 不含认证层，后续版本将添加 JWT
5. **资源限制**: 训练 Worker 使用 ProcessPoolExecutor，Docker 需要注意内存和 CPU 限制
6. **Swarm 模式**: `data/` 目录应使用 NFS 或 Docker volume（非绑定挂载）以确保多副本间共享
