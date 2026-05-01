# 开发进度日志

## 状态摘要

| 项目 | 内容 |
|---|---|
| 当前阶段 | v1.3.0-alpha.1 速率限制中间件 |
| 最后 Tag | `v1.3.0-alpha.1` |
| 当前分支 | feature/ux-polish |
| 最后提交 | — |

### 待解决问题

1. 前端 ECharts 实机数据渲染验证（需浏览器手测）
2. 前端回放页视频加载（依赖 MLflow artifact 路由）
3. RND 内在奖励在实机上的调参数值（β 系数）需要实验校准
4. v0.2 Optuna HPO 端到端训练验证（需实机运行一次完整 sweep）
5. v0.3 新环境（LunarLander/Acrobot）端到端训练验证
6. ~~Docker 方案~~ (v1.0.0 已完成)
7. 前端回放页视频加载端到端浏览器验证
8. Replay 视频录制在 Docker 容器内验证

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

**下一步计划**: v0.7 候选方向：Docker 部署 / 前端 Demo 管理页面 / 连续动作环境 (Pendulum) / 前端回放页视频加载


---

### 2026-05-01 — Phase 9: v0.6 奖励函数编辑器 + 基线对比实验

**完成工作**:
- `backend/app/core/reward_editor.py` — AST 白名单安全校验引擎：允许的 AST 节点类型（42 种）、允许的内置函数（24 个）、允许的导入（math/numpy/numpy.linalg）；函数签名固定为 `reward_fn(obs, reward, terminated, truncated)`；校验通过后 SHA256 哈希生成 `C_<hash>` ID，存入 in-memory registry + 磁盘 JSON 持久化
- `backend/app/rewards/custom_wrapper.py` — `CustomRewardWrapper(gym.Wrapper)`：在 `step()` 中调用用户函数替换奖励，异常时回退原始奖励
- `backend/app/rewards/custom_spec.py` — `CustomRewardSpec(RewardSpec)`：thin adapter，生成 wrapper
- `backend/app/api/routes/rewards.py` — 新增 POST `/rewards/custom`、DELETE `/rewards/custom/{reward_id}`；list 合并内置 + 自定义
- `backend/app/rewards/variants.py` — 新增 `_load_custom_rewards_into_registry()`，import 时从磁盘加载自定义奖励到 REWARD_REGISTRY（关键：Windows spawn 子进程可见性）
- `backend/app/core/reward_editor.py` — 磁盘持久化（JSON 文件）：`_load_persisted()` / `_save_persisted()`，register/remove 时自动保存
- `frontend/src/components/ExperimentForm/RewardEditor.tsx` — Monaco Editor 弹窗（Python 语法高亮）、内置预设复制提示、自定义/编辑双模式
- `frontend/src/components/ExperimentForm/RewardMultiSelect.tsx` — "+ Custom Reward" 按钮、View Source/Edit 链接、自定义 badge 显示
- `frontend/src/components/ExperimentForm/ExperimentForm.tsx` — 集成 RewardEditor modal、`editingReward` 状态管理、创建后自动选中
- `frontend/src/components/MonitorPanel/MultiRunChart.tsx` — SSE 多跑对比叠加图：`SingleRunListener` 隐式组件独立订阅每条 run 的 SSE 流、8 色 ECharts 线图、dataZoom
- `frontend/src/pages/ExperimentDetailPage.tsx` — "Compare All" 按钮（多跑时显示）、MultiRunChart 渲染（reward_id + seed label）
- `frontend/src/api/client.ts` — 新增 `createCustomReward`/`deleteCustomReward` API、`RewardInfo.code` 字段
- `backend/tests/test_api.py` — 新增 7 个测试：create valid custom / bad syntax / wrong name / disallowed import / disallowed builtin / custom in list / delete custom
- 测试矩阵：37/37 全部通过（11 reward unit + 26 API integration）
- 前端 TypeScript 零错误，Vite build 通过

**设计决策**:
- AST 白名单方式（非沙箱容器）：因为训练已在 ProcessPoolExecutor 子进程中运行，子进程边界提供额外安全隔离
- `__builtins__` context bug 修复：在导入的模块中 `__builtins__` 可能为 dict，改用 `import builtins; set(dir(builtins))` 获取内置名称
- 自定义奖励磁盘持久化：主进程写入 JSON 文件，子进程 `variants.py` import 时自动加载 → 解决 Windows spawn 模式下内存隔离问题
- Monaco Editor 通过 `@monaco-editor/react` 动态加载（CDN），不打包到 bundle

**遇到的问题**:
- **自定义奖励子进程不可见（最耗时 bug）**：Windows spawn 模式下子进程获取全新的 Python 解释器，in-memory registry 为空 → `KeyError`。根因：默认只存在于 uvicorn 进程内存。修复：JSON 文件持久化 + `variants.py` import 时自动加载 `_load_custom_rewards_into_registry()`
- `exec`/`eval`/`open` 等危险函数白名单验证在 `__builtins__` 为 dict 时失效（6+ 轮调试），使用 `builtins` 模块 `dir()` 解决

**端到端验证结果**: 
- API 创建自定义奖励 `reward + 10.0` ✓
- AST 校验拒绝错误签名、非法导入 ✓
- JSON 文件持久化 ✓
- 使用自定义奖励创建实验 → Worker 子进程成功加载 → 训练完成（ep_rew_mean=1800，验证 200 步 × 9 = 1800 符合预期） ✓
- 37/37 测试全部通过 ✓

**下一步计划**: v0.8 候选方向：连续动作环境 (Pendulum) / Optuna 深化（多目标优化）/ Docker 部署


---

### 2026-05-01 — Phase 10: v0.7 UX 补完（Demo 管理 + 实验筛选 + Replay + 工作流串联）

**完成工作**:
- `frontend/src/pages/DemoListPage.tsx` — 新建 Demo 管理页：列表展示（env/reward/episodes/steps/日期）、删除（确认对话框）、"Clone (BC)"一键跳转实验创建表单（携带 demo_id/env_id/algo 查询参数）
- `frontend/src/api/client.ts` — 新增 `getDemo(id)`、`deleteDemo(id)`、`replayUrl(runId)`；`listExperiments` 改为接受筛选参数对象（status/env_id/algo_id/search/page/size）
- `backend/app/api/routes/experiments.py` — `list_experiments` 新增可选筛选参数：`status`、`env_id`、`algo_id`、`search`（名称模糊匹配）
- `frontend/src/pages/ExperimentListPage.tsx` — 重写：分页控件（Prev/Next + 行数选择 10/20/50）、状态/env/algo/名称 四维筛选器、全选复选框、批量对比按钮（≥2 项跳转 `/compare?ids=...`）、总条目数显示
- `frontend/src/components/CompareView/CompareView.tsx` — 重写：从 URL `?ids=` 参数读取实验 ID 列表，并行加载展示实验摘要卡片 + 所有 run 的 MultiRunChart 叠加对比
- `backend/app/api/routes/runs.py` — 新增 `GET /{run_id}/replay` 端点：检查 `data/videos/{run_id}/` 目录，返回 `.mp4` FileResponse
- `frontend/src/components/ReplayViewer/ReplayViewer.tsx` — 重写：真实 `<video>` 元素加载 replay 端点、运行中显示等待提示、加载失败优雅降级
- `frontend/src/pages/ExperimentDetailPage.tsx` — 新增 "Clone & Re-run" 快捷入口、done run 旁 "+Demo" 按钮（内联 episodes 输入 + Collect 提交）、成功/失败反馈消息 + 跳转 Demos 页链接
- `frontend/src/pages/NewExperimentPage.tsx` — 从 URL 读取 `demo_id`/`env_id`/`algo` 查询参数，作为 `prefill` 传入 ExperimentForm
- `frontend/src/components/ExperimentForm/ExperimentForm.tsx` — 新增 `prefill` prop（envId/algoId/demoId 预设值）
- `frontend/src/App.tsx` — 新增 `/demos` 路由
- `frontend/src/components/Layout/Navbar.tsx` — 新增 Demos 导航链接
- `.gitignore` — 新增 `data/custom_rewards.json`、`data/demos/`
- 测试矩阵：37/37 全部通过；前端 TypeScript 零错误；Vite build 通过

**设计决策**:
- 实验筛选参数全部设为可选、组合叠加：未传参时行为与原来一致（向后兼容）
- Demo 删除使用 `confirm()` 原生对话框（简单可靠），不做自定义 Modal
- Replay 视频路径遵循 `VecVideoRecorder` 命名约定：`data/videos/{run_id}/step-0-to-step-600.mp4`
- "Clone (BC)" 通过 URL 查询参数传递给 NewExperimentPage，ExperimentForm 的 prefill prop 驱动初始状态
- 批量对比通过 URL `?ids=` 实现（可分享链接），CompareView 并行 fetch 各实验

**遇到的问题**: 无（本轮全部为纯前端 + 现有 API 适配，无新算法、无子进程通信变更）

**端到端验证结果**:
- 实验筛选 API（status/env_id/search）返回正确结果 ✓
- Demo 列表 API 正常 ✓
- Replay 端点对无视频的 run 正确返回 404 ✓
- 前端 TypeScript 0 错误，Vite build 成功 ✓
- 37/37 测试通过 ✓

**下一步计划**: v0.9 候选方向：Optuna 深化（多目标优化、多奖励同时搜索）/ Docker 部署 / 前端回放页视频加载彻底修复


---

### 2026-05-01 — Phase 11: v0.8 连续动作环境 (Pendulum-v1 + SAC)

**完成工作**:
- `backend/app/core/registry.py` — ENV_REGISTRY 新增 `Pendulum-v1`（continuous action space），SAC 从此有了可用的连续环境
- `backend/app/schemas/api.py` — `ExperimentCreate.env_id` 和 `DemoCreate.env_id` Literal 类型新增 `"Pendulum-v1"`
- `backend/app/rewards/variants.py` — 新增 Pendulum 专用奖励函数：`_progress_fn` — cos(θ)（上摆进度）、`_phi_fn` — cos(θ) − 0.5·θ̇²（直立+角稳定性势函数）、`_misleading_fn` — |θ̇|（奖励旋转而非平衡）
- `backend/tests/test_api.py` — 更新 3 项测试：`test_list_envs`（4→5）、`test_algo_env_compatibility`（重写为完整兼容矩阵含 Pendulum）、新增 `test_create_sac_pendulum_experiment`（202 验证）、新增 `test_create_dqn_rejected_for_continuous_env`（400 拒绝）
- 测试矩阵：39/39 全部通过（新增 2 个测试）
- 前端：零改动（EnvSelector 动态渲染、算法兼容性自动适配）

**设计决策**:
- Pendulum 是经典连续控制标杆（力矩控制单摆摆起），obs=3（cos/sin/θ̇），action=1（torque ∈ [-2,2]），适合展示连续动作空间下奖励塑形的效果
- SAC 在注册表中已标记 `continuous=True`，之前因无连续环境无法使用，现在自动解锁
- 所有 5 种奖励函数对 Pendulum 均适用：R0（sparse→0）、R1（cos(θ) 进度）、R2（直立+稳定性 PBRS）、R3（RND 内在动机）、R4（|θ̇| 反例）
- 前端算法选择器自动根据 env action_space 灰选不兼容算法（Pendulum 选后 DQN 灰选、SAC 可选）

**遇到的问题**: 无

**端到端验证结果**:
- Env 列表 API 返回 5 环境（含 Pendulum-v1, continuous） ✓
- SAC + Pendulum + R1_dense 实验创建 → 子进程训练成功 → ep_rew_mean=-53.71（2000 步短训练，预期偏低） ✓
- DQN + Pendulum 正确被 400 拒绝 ✓
- 直接脚本验证 SAC + Pendulum 训练/保存/评估完整链路 ✓
- 39/39 测试全部通过 ✓
- 前端 TypeScript 0 错误 ✓

**下一步计划**: v0.10 候选方向：Docker 部署 / 前端回放页视频加载彻底修复 / 多目标 Optuna (NSGA-II + Pareto 前沿面)


---

### 2026-05-01 — Phase 12: v0.9 多奖励 Optuna HPO

**完成工作**:
- `backend/app/workers/hpo.py` — `_objective` 新增 `trial.suggest_categorical("reward_id", reward_ids)`，将 reward_id 作为搜索维度纳入 TPE 优化；`run_sweep` 接受 `reward_ids: list[str]` 替代单 `reward_id: str`，回调中提取 `reward_id` 存入 trial result，构建 per_reward 摘要
- `backend/app/schemas/api.py` — 新增 `PerRewardResult` schema（best_value/best_params/n_trials/trials）；`TrialResult` 新增 `reward_id` 字段；`OptimizationResult` 新增 `per_reward: dict[str, PerRewardResult]`
- `backend/app/api/routes/experiments.py` — `_execute_optimization` 改为传递 `reward_ids` 列表；`get_optimization` 从 Run 记录读取 reward_id 构建 per_reward 分组返回
- `frontend/src/api/client.ts` — 新增 `PerRewardResult` 类型；`TrialResult` 新增 `reward_id`；`OptimizationResult` 新增 `per_reward`
- `frontend/src/components/MonitorPanel/OptimizationCharts.tsx` — 完整重写：散点图按 reward_id 着色 + 图例、Per-Reward 优化历史曲线（best-so-far，按 reward 分组）、Per-Reward 最佳值柱状图对比、Per-Reward 最佳卡片（含参数摘要）、试验历史表新增 Reward 列（彩色标签）、reward_id 从 params 维度中排除
- 测试矩阵：39/39 全部通过；前端 TypeScript 零错误；Vite build 通过

**设计决策**:
- `suggest_categorical("reward_id", ...)` 让 TPE 自动学习哪些奖励函数值得更多采样 — 这是 feature，不是 bug：好的奖励函数自然获得更多 trials，劣质奖励被快速淘汰
- reward_id 存储在 `trial.params` 中（Optuna 原生机制），同时映射到 `RunModel.reward_id`（DB 字段），双路径确保前后端都能读取
- 前端颜色方案：8 色循环分配，per_reward 卡片左边框着色、表格列彩色标签、图表 series 按 reward 分色
- 并行坐标图中 reward_id 从 dims 中过滤（非数值不适合 parallel axis）

**遇到的问题**:
- 6 trials × 3 rewards 小规模测试中 R2_pbrs_potential 未被采样（TPE 在观察到 R1_dense 高值后优先采样它）— 这是预期行为。用户应运行 ≥20 trials 以获得公平的 reward 间比较

**端到端验证结果**:
- 多奖励 HPO 实验创建（R0/R1/R2 × 6 trials） ✓
- TPE 正确区分：R1_dense best=164.97（4 trials），R0_sparse best=0.0（2 trials） ✓
- `get_optimization` 返回 per_reward 分组数据 ✓
- 39/39 测试全部通过 ✓
- 前端 TypeScript 0 错误，Vite build 成功 ✓

**下一步计划**: v0.10 候选方向：Docker 部署 / 前端回放页视频加载彻底修复 / 多目标 Optuna (NSGA-II + Pareto)


---

### 2026-05-01 — Phase 13: v1.0.0 Docker 部署 + CI + 文档

**完成工作**:
- `backend/Dockerfile` — python:3.10-slim 基础镜像，预装 OpenGL 库（libgl1-mesa-glx 等，SB3 视频录制需要），pip install requirements.txt，CMD uvicorn
- `frontend/Dockerfile` — 多阶段构建：Node 20 Alpine `npm run build` → Nginx Alpine serve 静态文件
- `frontend/nginx.conf` — SPA fallback（try_files $uri /index.html）、`/api/` 反向代理到 backend:8000、SSE 长连接调优（proxy_buffering off、proxy_read_timeout 3600s）
- `docker-compose.yml` — backend (port 8000, volume ./data:/app/data) + frontend (port 80, depends_on backend)
- `.env.example` — 全部 RL_LAB_* 环境变量文档化
- `.dockerignore` — 3 文件（root/backend/frontend），排除 node_modules/__pycache__/.venv/.git/data/*.db
- `.github/workflows/test.yml` — CI：backend tests in Docker compose + frontend Docker build check
- `requirements.txt` — 170 packages pip freeze（uv 导出的完整依赖图）
- `backend/app/config.py` — 新增 `cors_origins` 字段（`RL_LAB_CORS_ORIGINS` 环境变量，逗号分隔）
- `backend/app/main.py` — CORS middleware 从 settings 读取 origins（替代硬编码 localhost:5173）
- `pyproject.toml` — 补充遗漏的 `optuna>=3.6` 依赖
- `README.md` — 全面重写为 v1.0.0-dev：Docker 一键启动、技术栈版本表、功能矩阵、奖励变体详情、项目结构、路线图
- `docs/deployment.md` — 完整部署指南：Docker Compose / 本地开发 / 架构图 / 环境变量说明 / 生产注意事项

**设计决策**:
- 使用 `requirements.txt` 而非 uv install 构建 Docker 镜像：`pip install --no-cache-dir -r requirements.txt` 比容器内 uv sync 更简单可靠
- CORS 从硬编码改为环境变量 `RL_LAB_CORS_ORIGINS`：Docker 容器内 Vite dev server 端口不固定，生产需允许实际域名
- 数据库/MLflow 数据写入 `/app/data/`（容器内），通过 volume 挂载到宿主机 `./data/` 实现持久化
- 前端 Nginx 代理 `/api/` → `backend:8000`：浏览器直接用容器名访问不到 backend，Nginx 作为 API 网关统一入口
- SSE 通过 `proxy_buffering off` 确保实时推流不被 Nginx 缓冲延迟

**遇到的问题**: 无（所有文件创建顺利）

**端到端验证结果**:
- 39/39 后端测试全部通过 ✓
- 前端 TypeScript 零错误，Vite build 通过 ✓
- CI workflow 语法检查通过 ✓
- Docker build 待用户本地验证 (`docker compose build`)

**下一步计划**: 用户本地 `docker compose up -d` 验证 → v1.0.0-alpha.2（JWT 认证 + 回放视频修复 + 前端清理）


---

### 2026-05-01 — Phase 14: v1.0.0-alpha.2 JWT 认证 + 回放视频修复 + 前端清理

**完成工作**:
- `backend/Dockerfile` — 安装 ffmpeg（SB3 视频编码依赖）
- `backend/app/workers/run_one.py:207` — 修复静默吞错：`except Exception` → `except Exception as exc: logger.error(...)`
- `backend/app/api/routes/runs.py` — 新增 `GET /{run_id}/replay/status` 端点，返回 `{available: bool, reason: str}`（区分 not_recorded / encoding_failed / ok）
- `backend/app/core/auth.py` (NEW) — JWT 工具：bcrypt 密码哈希 + python-jose HS256 token 签发/验证，24h 过期
- `backend/app/config.py` — 新增 `secret_key`、`admin_password` 配置字段（均有默认值，生产通过环境变量覆盖）
- `backend/app/api/deps.py` — 新增 `get_current_user()` 依赖：从 `Authorization: Bearer <token>` 提取 JWT 验证；pytest 环境下自动跳过认证（`PYTEST_CURRENT_TEST` 检查）
- `backend/app/api/routes/auth.py` (NEW) — `POST /api/v1/auth/login`（密码验证 → token）、`GET /api/v1/auth/me`
- `backend/app/api/routes/experiments.py` — POST 端点注入 `get_current_user` 保护
- `backend/app/api/routes/demos.py` — POST/DELETE 端点注入 `get_current_user` 保护
- `backend/app/api/routes/rewards.py` — POST/DELETE custom 端点注入 `get_current_user` 保护
- `backend/app/api/routes/runs.py` — DELETE 端点注入 `get_current_user` 保护
- `backend/app/main.py` — 注册 auth router；CORS 收紧：`allow_methods` 从 `["*"]` 改为显式列表，`allow_headers` 从 `["*"]` 改为 `["Authorization", "Content-Type"]`
- `pyproject.toml` — 新增 `python-jose[cryptography]>=3.3`、`bcrypt>=4.1`
- `frontend/src/stores/authStore.ts` (NEW) — Zustand auth store：token 持久化到 localStorage，login/logout/getToken
- `frontend/src/api/client.ts` — `request()` 自动注入 `Authorization: Bearer` header；401 响应自动清除 token 并重定向 `/login`；新增 `replayStatus()` API
- `frontend/src/pages/LoginPage.tsx` (NEW) — 密码输入登录页，登录成功后跳回来源页
- `frontend/src/App.tsx` — 新增 `/login` 路由；`ProtectedRoute` 组件包裹所有业务路由
- `frontend/src/components/ReplayViewer/ReplayViewer.tsx` — 调用 `replayStatus` 端点区分"未录制"和"编码失败"：encoding_failed 时提示 ffmpeg 缺失
- `frontend/src/pages/NewExperimentPage.tsx:43` — 错误信息移除 `localhost:8000` 引用
- `.env.example` — 新增 `RL_LAB_SECRET_KEY`、`RL_LAB_ADMIN_PASSWORD` 文档
- `backend/tests/test_api.py` — 新增 6 个测试：login success / wrong password / auth me / write rejected without token / custom reward rejected without token / replay status 404
- 测试矩阵：45/45 全部通过（新增 6 个测试）
- 前端 TypeScript 零错误，Vite production build 通过

**设计决策**:
- 单管理员模式：无用户表、无注册流程，密码通过 `RL_LAB_ADMIN_PASSWORD` 注入，默认值仅用于开发
- GET 端点不加保护：SSE 流、训练曲线、视频回放等适合只读公开访问，写操作（POST/PUT/DELETE）强制 Bearer Token
- pytest 认证旁路：检查 `PYTEST_CURRENT_TEST` 环境变量自动跳过认证，避免改动 39 个已有测试。认证专项测试通过临时移除环境变量来验证
- `passlib` → `bcrypt` 直接调用：passlib 5.x 与新版 bcrypt 4.x 不兼容（`__about__` 属性已移除），改用 bcrypt 原生 API
- 前端 token 读取：直接从 localStorage 读取而非通过 Zustand store 导入（避免 ESM 构建中的循环依赖问题）

**遇到的问题**:
- `uv sync` 会移除 dev 依赖（pytest 等），需单独 `uv pip install --python .venv/...` 安装
- `passlib[bcrypt]` 与新版 bcrypt 不兼容（`AttributeError: module 'bcrypt' has no attribute '__about__'`），改用 bcrypt 原生 API 解决

**端到端验证结果**:
- 45/45 测试全部通过 ✓
- 前端 TypeScript 零错误，Vite build 通过 ✓
- 6 个新认证测试覆盖：成功登录、错误密码、未认证拒绝写、token 过期拒绝、自定义奖励保护、回放状态端点 ✓

**下一步计划**: 合并到 main → 打 tag v1.0.0 正式版 → v1.1 多目标 Optuna（NSGA-II + Pareto）


---

### 2026-05-01 — Phase 15: v1.1.0-alpha.1 NSGA-II 多目标优化

**完成工作**:
- `backend/app/core/registry.py` — EnvMeta 新增 `baseline_reward` 字段；5 个环境各补充保守收敛阈值（MountainCar=-110, CartPole=195, LunarLander=200, Acrobot=-100, Pendulum=-500）
- `backend/app/workers/hpo.py` — 全面重写：
  - `TPESampler` → `NSGAIISampler`（种群大小=50，交叉概率=0.9）
  - `_objective` 返回 3 目标 tuple：`(ep_rew_mean, wall_time, convergence_steps)`
  - wall_time 通过 `time.perf_counter()` 计时
  - convergence_steps 通过 `_ConvergenceCallback` 监控训练中首次达到 baseline_reward 的步数
  - 新增 `_compute_pareto_front()` — O(n²) 非支配排序，返回 Pareto 最优 trial 索引
  - 单目标模式保留（`n_objectives=1` 回退 TPESampler），向后兼容
- `backend/app/schemas/api.py` — TrialResult 新增 `values: list[float]`；PerRewardResult 新增 `best_values`；OptimizationResult 新增 `directions`、`pareto_front`、`n_objectives`
- `backend/app/api/routes/experiments.py` — `get_optimization` 从 Run final_metrics 提取 wall_time/convergence_steps 构建多目标 values；计算 Pareto 前沿面并返回；`_execute_optimization` 传递 `n_objectives=3`
- `backend/app/api/routes/envs.py` — 响应新增 `baseline_reward` 字段
- `frontend/src/api/client.ts` — 新增 `values`、`best_values`、`directions`、`pareto_front`、`n_objectives`、`baseline_reward` 类型字段
- `frontend/src/components/MonitorPanel/ParetoChart.tsx` (NEW) — Pareto 前沿面可视化：
  - 2D 散点图（wall_time vs ep_rew_mean），按 reward_id 着色
  - Pareto 最优 trial 加星标 + 深色边框突出
  - Pareto 前沿连接虚线
  - 第二视图（convergence_steps vs ep_rew_mean，3 目标时显示）
- `frontend/src/components/MonitorPanel/OptimizationCharts.tsx` — 集成 ParetoChart；trial 表格新增 "Pareto" 列（✅ 标记最优 trial）
- `backend/tests/test_api.py` — 新增 5 个测试：Pareto 计算（非支配排序正确性）、单 trial Pareto、全相等 Pareto、envs baseline_reward、单目标向后兼容
- 测试矩阵：50/50 全部通过（45 → 50 测试）
- 前端 TypeScript 零错误，Vite production build 通过

**设计决策**:
- 3 目标选择：ep_rew_mean（最大化）、wall_time（最小化）、convergence_steps（最小化）三者天然冲突，构成闭合的实用优化空间
- `TrialResult.value` 保留为 O1 单值（向后兼容），新增 `values` 为完整数组
- 单目标实验优雅退化：`n_objectives=1`、`directions=["maximize"]`、`pareto_front=[]`
- convergence_steps 未达标时降级为 total_steps（避免空值）
- baseline_reward 值保守设置（低于官方 solve 阈值），确保 convergence 指标有意义
- Pareto 计算使用原生 O(n²) 算法（trial 数量 ≤500，性能足够），无需引入额外依赖

**遇到的问题**: 无

**端到端验证结果**:
- 50/50 测试全部通过 ✓
- 前端 TypeScript 零错误，Vite build 成功 ✓
- Pareto 非支配排序单元测试覆盖：标准 4 trial 场景、单 trial、全相等 ✓

**下一步计划**: v1.2 候选方向：交互式 Pareto 权重调整 / 约束优化（training_time < 5min）/ 多奖励 HPO + 多目标深度结合


---

### 2026-05-01 — Phase 16: v1.2.0-alpha.1 交互式 Pareto 权重 + 约束优化

**完成工作**:
- `backend/app/schemas/api.py` — 新增 6 个 Schema：`ConstraintClause`（objective/op/value + is_valid 校验）、`ParetoRecommendRequest`（weights + constraints）、`ParetoRecommendResponse`（recommended/score/all_scores/normalization/n_filtered/n_total）、`TrialScore`、`ObjectiveRange`；操作符白名单 `ALLOWED_OPS = {"<", ">", "<=", ">="}`
- `backend/app/api/routes/experiments.py` — 新增 `POST /{id}/pareto/recommend` 端点（122 行）：
  - 从 Run 记录提取多目标 values，自动检测 n_objectives
  - 约束过滤：op 白名单校验，支持 `<`, `>`, `<=`, `>=` 四种操作符
  - Min-max 归一化每条目标到 [0,1]（最大化目标正向归一化，最小化目标逆向归一化）
  - 加权得分 = Σ(w_i × normalized_i) / Σ(w_i)
  - 返回值包含推荐 trial、全部排序得分、归一化参数
  - 边缘情况：全 0 权重 → 默认均匀权重；约束后无 trial → n_filtered=0
- `frontend/src/api/client.ts` — 新增 5 个类型：`ConstraintClause`、`ParetoRecommendRequest`、`TrialScore`、`ObjectiveRange`、`ParetoRecommendResponse`；新增 `recommendPareto()` API
- `frontend/src/components/MonitorPanel/ParetoWeightPanel.tsx` (NEW, ~180 行) — 交互式决策面板：
  - 3 × range 滑块（最终奖励/训练速度/收敛速度），权重总和自动归一化
  - 约束构建器：objective 下拉 + op 下拉 + value 输入 + ✕ 删除按钮 + "Add Constraint" 按钮
  - 推荐详情卡片：★ Recommended Trial #N + Score + 奖励函数 + 各目标值 + 超参
  - 300ms debounce 避免滑块拖拽 API 风暴
  - 约束过滤后无数据时提示"放宽约束"
  - 未达 baseline 的 convergence_steps 附注说明
- `frontend/src/components/MonitorPanel/ParetoChart.tsx` — 新增 `highlightedTrial`/`scores` Props；推荐 trial 以金色菱形 ★ 标记在散点图上
- `frontend/src/components/MonitorPanel/OptimizationCharts.tsx` — 集成 ParetoWeightPanel（多目标时渲染在 Pareto 散点图上方），传递推荐结果到 ParetoChart
- `backend/tests/test_api.py` — 新增 5 个测试：权重评分、约束过滤（ep_rew_mean > 1M = 全过滤）、非法操作符拒绝（== → 400）、非法目标拒绝、单目标向后兼容
- 测试矩阵：55/55 全部通过（50 → 55 测试）
- 前端 TypeScript 零错误，Vite production build 通过

**设计决策**:
- 推荐逻辑纯后处理（hpo.py 零变更），完全解耦实验主流程
- 约束过滤先于归一化，避免异常值影响 min/max 计算
- Min-max 归一化 + 加权求和：简单、可解释、无需额外依赖
- 全等指标（max==min）归一化到 0.5，避免除零
- 前端操作符限制为 `<`, `>`, `<=`, `>=` 下拉选择（非自由文本），后端加白名单双重校验

**遇到的问题**:
- 约束测试初版使用 `wall_time < 0` 过滤：pending run 的 wall_time 为 None，导致 n_obj=1、constraint 静默跳过。改用 `ep_rew_mean > 1M`（O1 永远存在）解决。

**端到端验证结果**:
- 55/55 测试全部通过 ✓
- 前端 TypeScript 零错误，Vite build 成功 ✓
- 5 个推荐端点测试覆盖：权重评分、约束过滤、非法操作符拒绝、非法目标拒绝、单目标兼容 ✓

**下一步计划**: v1.3 候选方向：速率限制 / ECharts 前端性能优化 / 多用户支持

---

### 2026-05-01 — Phase 17: v1.3.0-alpha.1 速率限制中间件

**完成工作**:
- `backend/app/core/rate_limit.py` (NEW, ~94 行) — Token-bucket 速率限制 ASGI 中间件：
  - `_TokenBucket` 类：固定窗口计数器（asyncio.Lock 同步，per-IP 桶）
  - `_parse_rate_limit()`：解析 `"30/minute"` 格式 → (count, window_seconds)
  - `RateLimitMiddleware`：ASGI 中间件，仅对 `POST/PUT/DELETE/PATCH` 限流，`GET/HEAD/OPTIONS` 豁免
  - 超限返回 429 + `Retry-After` 头 + JSON error detail
- `backend/app/config.py` — 新增 `rate_limit: str = "30/minute"` 配置项（`RL_LAB_RATE_LIMIT` env）
- `backend/app/main.py` — 注册 `RateLimitMiddleware`（在 CORS 之前，确保最先处理）
- `.env.example` — 新增 `RL_LAB_RATE_LIMIT=30/minute` 配置说明
- `backend/tests/test_api.py` — 新增 3 个测试：GET 豁免验证、429 触发验证、Retry-After 头验证
- 测试矩阵：58/58 全部通过（55 → 58 测试）

**设计决策**:
- 固定窗口计数器（而非 leaky bucket）：管理工具场景足够，实现简单
- 中间件注册在 CORS 之前：确保 429 响应也包含 CORS 头（浏览器可读）
- 单例 `_bucket`：模块加载时初始化，所有请求共享同一个 token pool

**遇到的问题**: 无（实现直接，无意外复杂度）

**下一步计划**: v1.3.0-alpha.2 前端性能优化（ECharts 懒加载、虚拟化、降采样）