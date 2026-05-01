# 开发进度日志

## 状态摘要

| 项目 | 内容 |
|---|---|
| 当前阶段 | v0.5.0 IRL/BC 开发中 |
| 最后 Tag | `v0.5.0-alpha.1` |
| 当前分支 | feature/multi-algo |
| 最后提交 | — |

### 待解决问题

1. 前端 ECharts 实机数据渲染验证（需浏览器手测）
2. 前端回放页视频加载（依赖 MLflow artifact 路由）
3. RND 内在奖励在实机上的调参数值（β 系数）需要实验校准
4. v0.2 Optuna HPO 端到端训练验证（需实机运行一次完整 sweep）
5. v0.3 新环境（LunarLander/Acrobot）端到端训练验证
6. Docker 方案待 v0.4

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

---

### 2026-05-01 — Phase 2: 后端收尾 + 前端启动 (v0.1.0-alpha.2)

**完成工作**:
- 创建 3 个 ADR 文档：tech stack (001)、v0.1 scope (002)、reward wrapper order (003)
- 前端项目初始化：Vite + React 18 + TypeScript 5，npm 依赖安装
- 前端依赖：react-router-dom、@tanstack/react-query、zustand、echarts、echarts-for-react、openapi-typescript
- API 层：`api/client.ts`（REST 封装 + 全部 TS 类型定义）、`api/stream.ts`（SSE EventSource 封装 + 自动重连）
- 状态管理：`stores/experimentStore.ts`（Zustand，实验列表 + 选中状态 + run 状态更新）
- Hooks：`useRunStream`（SSE 实时订阅）、`useRunMetrics`（历史指标拉取）
- 布局组件：`Navbar.tsx`（导航栏，路由高亮）、`MainLayout.tsx`（Outlet 布局）
- 表单组件：`ExperimentForm/ExperimentForm.tsx`（完整实验创建表单）、`EnvSelector.tsx`、`RewardMultiSelect.tsx`（含 ⚠ 警告样式）、`HyperParamPanel.tsx`
- 监控组件：`LearningCurveChart.tsx`（ECharts 实时曲线，5 色系）、`HealthCard.tsx`（PPO 健康度）、`MonitorPanel.tsx`（整合面板）
- 对比/回放组件：`CompareView.tsx`、`ReplayViewer.tsx`
- 页面：`ExperimentListPage.tsx`（5s 轮询 + 空状态引导）、`NewExperimentPage.tsx`、`ExperimentDetailPage.tsx`（Run 选择器 + MonitorPanel）
- App.tsx：BrowserRouter + QueryClientProvider + 路由配置
- 模板清理：删除 Vite 默认 assets，简化 index.css
- Tailwind CSS CDN（v0.1 原型用，生产换构建版本）
- 前端构建：TypeScript check 零错误，Vite build 成功（719ms）
- package.json：添加 `gen-types` 脚本（openapi-typescript 自动同步）

**遇到的问题**:
- `echarts-for-react` 缺少 `tslib` 传递依赖，通过 `npm install tslib --legacy-peer-deps` 解决
- npm 对等依赖警告较多（React 19 + 部分库），使用 `--legacy-peer-deps` 绕过。v0.1 不影响功能。

**下一步计划**: 提交审查报告，等待批准后进入 Phase 3（前后端联调 + ECharts 实机数据验证）

---

### 2026-05-01 — Phase 3: 前后端联调 + 端到端验证 (v0.1.0-alpha.3)

**完成工作**:
- 前端代理配置：Vite proxy `/api` → `localhost:8000`，移除所有硬编码 URL
- 修复 `run_one.py` 导入错误：`REWARD_REGISTRY` 从 `app.rewards.variants` 导入（正确）而非 `app.rewards.base`（错误）
- 修复 Windows `multiprocessing.Queue` 跨进程问题：改用 `Manager().Queue()`（spawn 模式下可序列化）
- 修复 MLflow tracking URI：由 `file:///` 切换为 `sqlite:///`（MLflow 3.x file store 已废弃）
- 修复 PPO device：显式传 `device='cpu'` 消除 GPU 警告
- 修复确定性算法警告：仅 CPU 可用时启用 `torch.use_deterministic_algorithms`
- 端到端测试通过：创建实验 → 调度 → 子进程训练 → Manager Queue 桥接 → SSE 就绪 → 状态写入 DB
  - 2 轮完整训练：MountainCar-v0 + R1_dense（2000 steps）/ R2_pbrs_potential（5000 steps）
  - 状态流转：pending → running → done ✓
  - MLflow experiment/run 自动记录 ✓
- SSE 端点连接验证：EventSourceResponse 正常响应

**遇到的问题**:
- **Windows multiprocessing Queue 跨进程序列化失败** — `RuntimeError: Queue objects should only be shared between processes through inheritance`。根因：Windows 使用 `spawn` 而非 `fork`，`mp.Queue()` 不可序列化。解决：改用 `mp.Manager().Queue()`。这是 `技术栈选型.md` 避坑 #4 的延伸——在 Windows 上子进程通信需要额外的序列化考量。
- **uvicorn 端口占用残留** — 多次测试需手动 `taskkill`。建议后续添加 `lifespan` shutdown hook 清理。

**下一步计划**: 提交审查报告，等待批准后进入 Phase 4（v0.1.0 发布收尾）

---

### 2026-05-01 — Phase 4: v0.1.0 发布收尾

**完成工作**:
- `docs/architecture.md` — 完整架构文档（四层架构图、数据流序列图、模块交互、关键设计决策汇总）
- `README.md` — 全面重写（快速开始指南、奖励变体详情表、项目结构、路线图、文档索引）
- `backend/tests/test_api.py` — 9 个 API 集成测试（health/envs/rewards/experiments CRUD/validation/404）
- 测试矩阵：20/20 全部通过（11 reward unit + 9 API integration）
- `ExperimentCreate.total_steps` 下限由 1000→100（支持快速冒烟测试）

**遇到的问题**: 无

**v0.1.0 发布检查单**:
- [x] 后端 FastAPI 骨架 + 全部路由
- [x] 5 个奖励变体 (R0-R4) + PBRS Wrapper
- [x] 训练 Worker (scheduler + subprocess + MLflow)
- [x] SSE 实时流推送
- [x] 前端 React 项目 + 4 页面 + 12 组件
- [x] 端到端训练链路验证（Windows）
- [x] 架构文档
- [x] 3 个 ADR 决策记录
- [x] 进度日志 + 需求澄清记录
- [x] 20 测试全部通过
- [x] 一键环境搭建脚本
- [ ] 浏览器实机渲染验证（用户手动）
- [ ] 前端 ECharts SSE 实时数据测试（需浏览器）

**下一步**: 用户手动浏览器验证 → v0.2 引入 Optuna HPO


---

### 2026-05-01 — Phase 5: v0.2 Optuna HPO 集成

**完成工作**:
- `backend/app/workers/hpo.py` — Optuna 超参搜索核心：TPESampler(multivariate=True)、RDBStorage、`_objective()` 采样→训练→评估 3 回合、`_sample_params()` 支持 5 种分布（loguniform/uniform/int/categorical/discrete_uniform）、`run_sweep()` 在 thread pool 中同步运行 Optuna
- `backend/app/schemas/api.py` — 新增 `TrialResult`(number/value/params)、`OptimizationResult`(experiment_id/n_trials/best_value/best_params/trials/status)、`ExperimentCreate` 增加 `optimize:bool`/`search_space:dict`/`n_trials:int`
- `backend/app/api/routes/experiments.py` — POST 分支：optimize=True 时不预创建 Run（由 sweep 完成时创建）、`_execute_optimization()` 后台任务、`GET /{id}/optimization` 端点返回 OptimizationResult
- `frontend/src/api/client.ts` — 新增 `TrialResult`/`OptimizationResult` 类型、`getOptimization()` API 函数、`ExperimentCreate` 增加 optimize/search_space/n_trials 字段
- `frontend/src/components/ExperimentForm/SearchSpaceEditor.tsx` — 基于行的搜索空间编辑器：参数下拉选择（7 个 PPO 超参）、分布类型选择（5 种）、根据分布动态显示 low/high/choices/q 输入框
- `frontend/src/components/ExperimentForm/ExperimentForm.tsx` — 新增 "Optuna Hyperparameter Optimization" 开关、SearchSpaceEditor 集成、n_trials 输入、提交时校验搜索空间非空
- `frontend/src/components/MonitorPanel/OptimizationCharts.tsx` — 散点图（Trial vs Reward）+ 并行坐标图（ECharts parallel）+ 试验历史表（按值排序，best 行高亮）+ 最佳结果卡片
- `frontend/src/pages/ExperimentDetailPage.tsx` — 3s 轮询优化结果、渲染 OptimizationCharts
- `backend/tests/test_api.py` — 新增 2 个测试：`test_create_optimize_experiment`（202 响应）、`test_get_optimization_nonexistent`（404）
- 测试矩阵：22/22 全部通过（11 reward + 11 API）
- TypeScript 类型检查零错误，Vite 生产构建通过

**设计决策**:
- optimize 模式仅使用第一个 reward_id（`body.reward_ids[0]`）进行搜索，多奖励同时优化的复杂度留给 v0.3
- `run_sweep` 在独立 DB session 中创建 Run 记录并更新 Experiment 状态，通过 `merge()` 传递实验对象
- Optuna 使用主数据库 URL（剥离 `+aiosqlite` 前缀）作为 RDBStorage，与 App DB 共用 SQLite 文件

**遇到的问题**:
- TypeScript `as const` 导致 DIST_TYPES.fields 类型推断为 `never[]`，去掉 `as const` 并显式声明类型解决

**下一步计划**: 端到端验证（实机运行一次完整的 Optuna sweep，观察前端可视化）→ v0.3 多环境扩展


---

### 2026-05-01 — Phase 6: v0.3 多环境扩展

**完成工作**:
- `backend/app/rewards/base.py` — `RewardSpec.wrap()` 增加可选 `env_id` 参数，向后兼容
- `backend/app/rewards/variants.py` — 提取 `_progress_fn(env_id)`/`_phi_fn(env_id)`/`_misleading_fn(env_id)` 三个 env-aware 工厂函数，为每个环境返回专用信号：
  - **MountainCar-v0**: position+1.2 / position+0.5v² / |velocity|
  - **CartPole-v1**: 同上（默认 fallback）
  - **LunarLander-v2**: altitude / altitude+0.3·uprightness / total speed
  - **Acrobot-v1**: tip height (forward kinematics) / tip height / |angular velocity|
- `backend/app/core/registry.py` — 新增 `LunarLander-v2`、`Acrobot-v1` 到 ENV_REGISTRY（4 环境）
- `backend/app/schemas/api.py` — `ExperimentCreate.env_id` 增加 `LunarLander-v2`、`Acrobot-v1`
- `backend/app/workers/run_one.py` — 两处 `spec.wrap()` 传入 `env_id`
- `backend/app/workers/hpo.py` — `spec.wrap()` 传入 `env_id`
- `backend/tests/test_api.py` — env 数量断言更新为 4
- 移除 `variants.py` 中未使用的 `numpy` 导入
- 测试矩阵：22/22 全部通过
- 前端 TypeScript 零错误，Vite build 通过（EnvSelector 动态渲染，无需修改）

**设计决策**:
- `env_id` 参数设为可选（默认 `""`），保持向后兼容；未识别环境回退到 MountainCar 默认值
- 奖励工厂函数分层：泛型 Wrapper（`wrappers.py`，环境无关） → 工厂函数（`variants.py`，环境选择势函数） → RewardSpec 子类（不变）
- Acrobot 的 tip height 通过正向运动学计算：`-cos(θ₁) - cos(θ₁+θ₂) = -obs[0] - obs[0]*obs[2] + obs[1]*obs[3]`

**遇到的问题**: 无

**下一步计划**: 端到端验证（在所有 4 个环境中测试训练链路）→ v0.4 多算法 (DQN/SAC) + GPU


---

### 2026-05-01 — Phase 7: v0.4 多算法 (DQN/SAC) + GPU

**完成工作**:
- `backend/app/config.py` — `device` 改为 `torch.cuda.is_available()` 自动检测（GPU/CPU），本机检测到 CUDA
- `backend/app/core/registry.py` — ALGO_REGISTRY 新增 DQN (discrete-only) 和 SAC (continuous-only)，含完整 `default_hp`
- `backend/app/schemas/api.py` — `algo_id` 扩展为 `Literal["PPO","DQN","SAC"]`；`hyperparams` 从 `PPOHyper` 改为 `dict[str,Any]`（Pydantic 验证 + algo-agnostic）
- `backend/app/api/routes/algos.py` — 新建 `/api/v1/algos` 端点，返回算法元数据 + 默认超参
- `backend/app/api/routes/experiments.py` — POST 增加 `algo_supports_env()` 校验（不兼容算法返回 400）；`_execute_optimization` 传递 `algo_id`
- `backend/app/workers/run_one.py` — 算法 dispatch：PPO/DQN/SAC，用户 hp 与 algo default_hp 合并
- `backend/app/workers/hpo.py` — `_objective` 算法 dispatch；`run_sweep` 接收 `algo_id`
- `backend/app/main.py` — 注册 algos router
- `frontend/src/api/client.ts` — +`AlgoInfo` 类型、`ExperimentCreate.algo_id` 扩展为 union、+`listAlgos()`
- `frontend/src/components/ExperimentForm/HyperParamPanel.tsx` — 重写为通用动态渲染器，根据 algo 自动生成字段
- `frontend/src/components/ExperimentForm/ExperimentForm.tsx` — 新增算法选择器（radio buttons，不兼容环境自动灰选）；algo 切换时 hp 自动重置为 default_hp
- `frontend/src/pages/NewExperimentPage.tsx` — fetch algos 并传入 ExperimentForm
- `backend/tests/test_api.py` — 新增 3 个测试：`test_list_algos`、`test_create_dqn_experiment`、`test_create_sac_rejected_for_discrete_env`
- 测试矩阵：25/25 全部通过
- 前端 TypeScript 零错误，Vite build 通过

**设计决策**:
- `hyperparams` 从强类型 `PPOHyper` 改为 `dict[str,Any]`：随算法增多，单一 Hyper 模型无法维护。后端合并 default_hp + 用户 hp，SB3 自行校验参数合法性
- SAC 当前无可用环境（4 个 env 均为 discrete），通过 `algo_supports_env` 在 POST 时拒绝，前端 UI 同时灰选。为后续 v0.5+ 连续环境预留
- GPU 自动检测：`torch.cuda.is_available()` → `"cuda"` else `"cpu"`。PPO + GPU 会产生 SB3 已知 warning，不影响训练

**遇到的问题**:
- `hpo.py` 首次端到端验证时缺少 `select` 导入（已于上一阶段修复）
- `device="cuda"` 下 PPO 产生 SB3 GPU warning（已知问题，训练正常进行）

**下一步计划**: 端到端验证 DQN 训练链路 → v0.5 IRL/RLHF (imitation 集成)


---

### 2026-05-01 — Phase 8: v0.5 Behavioral Cloning (BC) + Demo Collection

**完成工作**:
- `backend/app/core/registry.py` — ALGO_REGISTRY 新增 BC（Behavioral Cloning），discrete=True, continuous=True, default_hp: batch_size/l2_weight/optimizer_kwargs
- `backend/app/workers/collect_demo.py` — 新建：从已完成 PPO Run 的 checkpoint 收集专家轨迹，使用 `imitation.data.rollout.rollout()` + `serialize.save()` 输出 .npz 文件
- `backend/app/api/routes/demos.py` — 新建：Demo CRUD API（GET list, POST create from source_run_id, GET detail, DELETE）
- `backend/app/workers/run_one.py` — 新增 BC dispatch：加载 demo .npz → `bc.BC` 训练 → `BCPolicyWrapper` 包装（适配 `predict(obs, deterministic) → (actions, None)` 接口）；`_record_replay` 类型泛化
- `backend/app/api/routes/experiments.py` — BC 实验创建校验：必须有 demo_id、demo 存在、demo env 匹配；`hyperparams` 增加 `demo_path` 透传
- `backend/app/main.py` — 注册 demos router
- `backend/app/schemas/api.py` — `algo_id` 扩展为 `Literal["PPO","DQN","SAC","BC"]`（前期已做）；DemoCreate/DemoSummary 已添加
- `backend/app/db/models.py` — Demo ORM 模型已添加（前期已做）
- `backend/tests/test_api.py` — 新增 5 个测试：test_create_bc_experiment_requires_demo / test_list_demos / test_create_demo_missing_source / test_get_demo_nonexistent / test_delete_demo_nonexistent
- 测试矩阵：30/30 全部通过（11 reward + 19 API）
- 前端 TypeScript 零错误，Vite build 通过
- 前端 `client.ts` — 新增 DemoInfo 类型、listDemos/createDemo API、ExperimentCreate.algo_id 扩展 + demo_id 字段
- 前端 `ExperimentForm.tsx` — BC 算法选项；BC 选中时显示 Demo 选择器（按 env_id 过滤）；优化面板 BC 时隐藏；total_steps 标签适配

**设计决策**:
- BC 不通过 `model.learn()` 训练，而是在 algo dispatch 块中直接 `bc_trainer.train(n_batches=total_steps)`
- `BCPolicyWrapper` 调用底层 policy 的 `_predict()` 方法（imitation 内部 API），确保与 SB3 `predict()` 签名一致
- `demo_id` 仅在 ExperimentCreate API schema 中存在，不存储到 Experiment DB 模型；demo_path 存入 Run.hyperparams（JSON）
- Demo collection 必须在 source run 状态为 "done" 时进行，验证 checkpoint 文件存在

**遇到的问题**: 无

**遇到的问题**:
- `imitation.data.rollout.rollout()` 默认 `unwrap=True` 需要 imitation 特定的 info wrapper，使用 `unwrap=False` 解决
- `bc.BC.__init__()` 需要 `rng` 参数（imitation 1.0.0）
- `artifact_path` 未持久化到 DB 的预存在 bug：`schedule_run` 中 bridge task 被 cancel 导致最终消息丢失，改为 await 完成
- `gym.vector.make` 与 imitation rollout 不兼容，改用 `DummyVecEnv`

**端到端验证结果**: `scripts/validate_bc.py` 全部通过 — PPO 训练 (9s) → Demo 收集 (5 eps, 1005 steps) → BC 训练 (1s, 100 batches) → BC 无 demo 正确拒绝

**下一步计划**: v0.6 候选方向（按优先级）：Docker 部署 / 前端 Demo 管理页面 / 连续动作环境 (Pendulum) / 前端回放页视频加载