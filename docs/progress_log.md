# 开发进度日志

## 状态摘要

| 项目 | 内容 |
|---|---|
| 当前阶段 | Phase 1 (v0.1.0-alpha.1) 已完成：后端核心搭建 |
| 最后 Tag | `v0.1.0-alpha.1` |
| 当前分支 | develop |
| 最后提交 | `c4ae3ac` → 即将提交 Phase 1 |

### 待解决问题

1. 前端项目骨架待搭建（Phase 2）
2. MLflow 集成端到端验证（Phase 2）
3. Docker 方案待 v0.4

### 恢复上下文需读取的文件

1. `rl-reward-research.md` — 奖励函数架构研究（唯一需求来源）
2. `技术栈选型.md` — 技术栈选型与渐进式路线
3. `CLAUDE.md` — 工程规范
4. `docs/progress_log.md` — 本文件
5. `docs/requirements_clarification.md` — 需求澄清记录
6. `README.md` — 项目总览

---

## 日志

### 2026-05-01 — Phase 1: 后端核心搭建 (v0.1.0-alpha.1)

**完成工作**:
- `pyproject.toml` + `environment.yml` — 依赖声明（uv + conda 双通道）
- `backend/app/main.py` — FastAPI 应用入口（CORS、lifespan、路由挂载）
- `backend/app/config.py` — Pydantic Settings 配置管理
- `backend/app/db/database.py` + `models.py` — SQLAlchemy 异步引擎 + Experiment/Run ORM
- `backend/app/schemas/api.py` + `domain.py` — Pydantic v2 全部 Schema（PPOHyper、ExperimentCreate/RunSummary、MetricEvent）/ 四种元对象（EnvSpec、RewardSpecMeta、AlgoSpec）
- `backend/app/rewards/base.py` + `wrappers.py` + `variants.py` — RewardSpec ABC + REWARD_REGISTRY / PBRSWrapper、SparseWrapper、DenseProgressWrapper、MisleadingRewardWrapper / 5 个奖励变体 R0-R4
- `backend/app/rewards/rnd.py` — 最小 RND 实现（替代 rlexplore，理由：PyPI 无此包，GitHub 不可达）
- `backend/app/workers/scheduler.py` + `run_one.py` + `callbacks.py` — asyncio.Semaphore + ProcessPoolExecutor 调度 / 训练入口（含 RND 适配） / SSE 流式回调
- `backend/app/api/routes/envs.py` + `rewards.py` + `experiments.py` + `runs.py` + `stream.py` — 全部 v0.1 REST + SSE 端点
- `backend/app/core/registry.py` — Env/Algo 统一注册与兼容性矩阵
- `backend/tests/test_rewards.py` — 11 项单元测试（全部通过）
- `scripts/setup.sh` + `dev.sh` — 一键搭建/启动脚本
- 需求澄清 5 项全部闭环（`docs/requirements_clarification.md`）
- CLAUDE.md 工程规范文件

**依赖处理决策**:
- `gymnasium` 版本由 `>=1.0` 调整为 `>=0.29,<1.0`：`imitation>=1.0.0` 要求 gymnasium<1.0
- `rlexplore` 移除依赖，自实现 RNDCallback（`backend/app/rewards/rnd.py`）：PyPI 无此包，GitHub 不可达
- `mlflow>=3.7.0` 确认 PyPI 可用（实际最新 3.11.1）

**遇到的问题**:
- uv 要求 venv 或 `--system` flag，使用 `--system` 安装到 conda 环境
- hatchling 无法自动发现包（项目名 rl-reward-lab ≠ 实际包 app），通过 `[tool.hatch.build.targets.wheel] packages = ["backend/app"]` 解决
- Windows 终端 GBK 编码问题，通过 `PYTHONIOENCODING=utf-8` 解决

**下一步计划**: 提交审查报告，等待批准后进入 Phase 2（MLflow 集成验证 + 前端项目骨架）
