# RL-Reward-Lab

**强化学习奖励函数设计与自动化调参可视化平台**

面向 RL 研究的实验平台，专注于奖励函数设计、自动化超参搜索与多维可视化分析。

## 当前状态

- **版本**: v0.3.0-dev（开发中）
- **当前范围**: 4 环境 × 1 算法 × 5 奖励变体 × Optuna HPO × 实时监控看板
- **下一阶段**: v0.4 — 多算法 (DQN/SAC) + GPU

## 技术栈

| 层 | v0.1 选型 | 版本约束 |
|---|---|---|
| 前端框架 | React 18 + TypeScript 5 + Vite | React ≥18.3, TS ≥5.4 |
| 状态管理 | TanStack Query + Zustand | TanStack 5.x, Zustand 5.x |
| 可视化 | Apache ECharts 5 (echarts-for-react) | 5.5+ |
| 后端框架 | FastAPI + Uvicorn + Pydantic v2 | FastAPI ≥0.135 |
| RL 训练 | Stable-Baselines3 + sb3-contrib + imitation | SB3 ≥2.3 |
| 实验追踪 | MLflow (SQLite backend, 自托管) | ≥3.7 |
| 数据库 | SQLite → PostgreSQL v0.4+ | — |
| 实时推送 | SSE (FastAPI EventSourceResponse) | — |
| 任务调度 | asyncio.Semaphore + ProcessPoolExecutor | — |
| 超参优化 | Optuna 4.x (v0.2 起) | — |

## 快速开始

### 环境要求

- Python ≥3.10 + pip
- Node.js ≥18 + npm
- (可选) conda

### 一键搭建

```bash
# 1. 克隆项目
git clone <repo-url> && cd RL-Reward-Lab

# 2. Python 环境
bash scripts/setup.sh
# 或手动: pip install uv && uv pip install --system -e ".[dev]"

# 3. 前端依赖
cd frontend && npm install --legacy-peer-deps && cd ..

# 4. 生成 OpenAPI 类型（后端启动后）
cd frontend && npm run gen-types && cd ..
```

### 启动开发环境

```bash
# Terminal 1: 启动后端
cd backend && uvicorn app.main:app --reload --port 8000

# Terminal 2: 启动前端
cd frontend && npm run dev
```

打开 http://localhost:5173，创建实验即可开始。

### 运行测试

```bash
# 后端测试
pytest backend/tests/ -v

# 前端类型检查
cd frontend && npx tsc --noEmit
```

## 当前功能

| 功能 | 说明 |
|---|---|
| 环境 | MountainCar-v0, CartPole-v1, LunarLander-v2, Acrobot-v1 |
| 算法 | PPO (MlpPolicy) |
| 奖励变体 | R0_sparse / R1_dense / R2_pbrs_potential / R3_curiosity_rnd / R4_misleading |
| 实验创建 | 多选奖励 × 多种子 → 并行训练 |
| 超参搜索 | Optuna TPESampler，5 种分布，散点图 + 并行坐标可视化 |
| 实时监控 | SSE 推送学习曲线 + PPO 健康度卡片 |
| 实验对比 | 列表页 3s 轮询状态，对比页多选 |
| 策略回放 | 训练完成后 mp4 视频 |

## 奖励变体详情

| ID | 名称 | 原理 | 教学价值 |
|---|---|---|---|
| R0_sparse | Sparse | 仅终局成功 +1 | 演示不加 shaphing 学不会 |
| R1_dense | Dense | 位置进度信号 | 手工奖励 vs 稀疏对比 |
| R2_pbrs_potential | PBRS | Φ(s)=pos+0.5v² (Ng & Russell 1999) | 策略不变性塑形 |
| R3_curiosity_rnd | Curiosity | RND 内在动机 (Burda et al. 2019) | 探索驱动 vs 奖励塑形 |
| R4_misleading | ⚠ Misleading | 奖励\|速度\|而非到达终点 | reward hacking 反例 |

## 项目结构

```
RL-Reward-Lab/
├── backend/          # FastAPI 后端
│   ├── app/
│   │   ├── api/      # REST + SSE 路由
│   │   ├── db/       # SQLAlchemy 模型
│   │   ├── schemas/  # Pydantic v2 验证
│   │   ├── rewards/  # 5 个奖励变体
│   │   ├── workers/  # 训练调度执行
│   │   └── core/     # 注册表
│   └── tests/        # 11 tests
├── frontend/         # React + Vite + ECharts
│   └── src/
│       ├── api/      # REST client + SSE
│       ├── components/ # 12 组件
│       ├── pages/    # 4 页面
│       ├── hooks/    # SSE hook
│       └── stores/   # Zustand
├── docs/             # 架构/ADRs/日志/需求
├── scripts/          # setup/dev 脚本
└── docker/           # (v0.4 启用)
```

## 文档索引

- [系统架构](docs/architecture.md) — 四层架构、数据流、关键设计决策
- [开发日志](docs/progress_log.md) — 状态摘要 + 逐阶段日志
- [需求澄清记录](docs/requirements_clarification.md)
- [技术决策 (ADR)](docs/decisions/) — ADR-001~003
- [工程规范](CLAUDE.md)

## 路线图

| 版本 | 主题 | Tag |
|---|---|---|
| v0.1 | 单环境 + PPO + 5 Reward | `v0.1.0` ✅ |
| v0.2 | Optuna HPO | — ✅
| v0.3 | 多环境 (LunarLander/Acrobot) | — ✅
| v0.4 | 多算法 (DQN/SAC) + GPU | — |
| v0.5 | IRL/RLHF (imitation 集成) | — |
| v1.0 | 文档站 + Docker Compose + 发布 | — |

## 许可证

MIT
