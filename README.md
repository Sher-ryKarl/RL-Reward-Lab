# RL-Reward-Lab

**强化学习奖励函数设计与自动化调参可视化平台**

面向 RL 研究的实验平台，专注于奖励函数设计、自定义奖励编辑器、多奖励并行超参搜索与多维度可视化分析。

## 当前状态

- **版本**: v1.3.0
- **测试**: 53/53 全部通过
- **认证**: JWT Bearer Token + 多用户系统（注册/登录/数据隔离）
- **安全**: Token-bucket 速率限制（写端点 30req/min）+ bcrypt 密码哈希
- **环境**: 5 环境 × 4 算法 × 5 奖励变体 × 自定义奖励

## 技术栈

| 层 | 选型 | 版本 |
|---|---|---|
| 前端框架 | React 19 + TypeScript + Vite 8 | React ≥18.3 |
| 状态管理 | TanStack Query 5 + Zustand 5 | — |
| 可视化 | Apache ECharts 6 (echarts-for-react) | 6.0+ |
| 后端框架 | FastAPI + Uvicorn + Pydantic v2 | ≥0.135 |
| RL 训练 | Stable-Baselines3 + sb3-contrib + imitation | SB3 ≥2.3 |
| 实验追踪 | MLflow (SQLite / 远程) | ≥3.7 |
| 数据库 | SQLite → PostgreSQL 可切换 | — |
| 实时推送 | SSE (EventSourceResponse) | — |
| 超参优化 | Optuna TPESampler (多奖励并行) | ≥3.6 |
| 部署 | Docker Compose | — |

## 快速开始

### Docker（推荐，一键启动）

```bash
git clone https://github.com/Sher-ryKarl/RL-Reward-Lab.git && cd RL-Reward-Lab

# 启动全部服务
docker compose up -d

# 打开浏览器
# → http://localhost （前端）
# → http://localhost:8000/health （后端健康检查）

# 运行测试
docker compose exec backend pytest backend/tests/ -q
```

### 本地开发

```bash
# Python 环境（需要 Python ≥3.10）
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

### 运行测试

```bash
# 后端测试
pytest backend/tests/ -q

# 前端类型检查
cd frontend && npx tsc --noEmit
```

## 功能矩阵

| 功能 | 说明 |
|---|---|
| **5 环境** | MountainCar, CartPole, LunarLander, Acrobot, Pendulum |
| **4 算法** | PPO, DQN (discrete), SAC (continuous), BC (Behavioral Cloning) |
| **5 内置奖励** | R0_sparse / R1_dense / R2_pbrs / R3_curiosity_rnd / R4_misleading |
| **自定义奖励** | Monaco 编辑器 + AST 安全校验 + 磁盘持久化 |
| **多奖励 HPO** | Optuna TPE 自动探索"奖励函数 × 超参"最佳组合 |
| **实验筛选** | 分页、状态/env/algo/名称四维筛选、批量对比 |
| **Demo 管理** | 专家轨迹收集、一键 BC 克隆实验 |
| **多目标 HPO** | NSGA-II 三目标（奖励+速度+收敛），Pareto 前沿可视化 |
| **Pareto 决策助手** | 交互式权重滑块 + 约束过滤 + 自动推荐最优 Trial |
| **实时监控** | SSE 学习曲线 + 多跑对比叠加图（降采样+节流优化） |
| **策略回放** | 训练完成自动录制 mp4 视频 |
| **多用户支持** | 注册/登录/数据隔离，每用户独立实验空间 |
| **速率限制** | Token-bucket 写保护（可配置），GET 豁免 |

## 奖励变体详情

| ID | 名称 | 原理 | 教学价值 |
|---|---|---|---|
| R0_sparse | Sparse | 仅终局成功 +1 | 演示不加 shaping 学不会 |
| R1_dense | Dense | 位置/角度进度信号 | 手工奖励 vs 稀疏对比 |
| R2_pbrs_potential | PBRS | Φ(s) 策略不变塑形 (Ng & Russell 1999) | 理论保证不改变最优策略 |
| R3_curiosity_rnd | Curiosity | RND 内在动机 (Burda et al. 2019) | 探索驱动 vs 奖励塑形 |
| R4_misleading | ⚠ Misleading | 奖励速度/角速度而非任务目标 | reward hacking 反例 |
| Custom | 自定义 | Python reward_fn 函数 | 自由实验任意奖励设计 |

## 项目结构

```
RL-Reward-Lab/
├── backend/              # FastAPI 后端
│   ├── app/
│   │   ├── api/routes/   # REST + SSE 端点
│   │   ├── core/         # 注册表 + AST 奖励校验
│   │   ├── db/           # SQLAlchemy 模型
│   │   ├── rewards/      # 5 内置 + 自定义奖励
│   │   ├── schemas/      # Pydantic v2 验证
│   │   └── workers/      # 训练调度 + HPO
│   └── Dockerfile
├── frontend/             # React + Vite + ECharts
│   ├── src/
│   │   ├── api/          # REST client + SSE
│   │   ├── components/   # 18 组件
│   │   ├── pages/        # 6 页面
│   │   └── hooks/        # SSE hook
│   ├── nginx.conf
│   └── Dockerfile
├── docs/                 # 架构/ADR/日志/需求/部署
├── docker-compose.yml    # 一键编排
└── .github/workflows/    # CI
```

## 文档索引

- [系统架构](docs/architecture.md)
- [部署指南](docs/deployment.md)
- [开发日志](docs/progress_log.md)
- [需求澄清](docs/requirements_clarification.md)
- [技术决策 (ADR)](docs/decisions/)
- [工程规范](CLAUDE.md)

## 路线图

| 版本 | 主题 | Tag |
|---|---|---|
| v0.1 – v0.5 | 训练链路 + 多算法 + BC | `v0.5.0-alpha.1` |
| v0.6 | 自定义奖励编辑器 | `v0.6.0-alpha.1` |
| v0.7 | UX 补完（筛选/分页/批量对比） | `v0.7.0-alpha.1` |
| v0.8 | 连续动作环境 Pendulum + SAC | `v0.8.0-alpha.1` |
| v0.9 | 多奖励 Optuna HPO | `v0.9.0-alpha.1` |
| v1.0 | Docker 部署 + CI + JWT 认证 | `v1.0.0` |
| v1.1 | NSGA-II 多目标优化 + Pareto 前沿可视化 | `v1.1.0-alpha.1` |
| v1.2 | 交互式 Pareto 权重 + 约束推荐 | `v1.2.0-alpha.1` |
| v1.3 | 速率限制 + 前端性能优化 + 多用户支持 | `v1.3.0` |

## 许可证

MIT
