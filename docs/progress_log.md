# 开发进度日志

## 状态摘要

| 项目 | 内容 |
|---|---|
| 当前阶段 | Phase 3 (v0.1.0-alpha.3) 已完成：前后端联调 + 端到端验证 |
| 最后 Tag | `v0.1.0-alpha.3` |
| 当前分支 | develop |
| 最后提交 | `87f1f79` → 即将提交 Phase 3 |

### 待解决问题

1. 前端 ECharts 实机数据渲染验证（需浏览器手测）
2. 前端回放页视频加载（依赖 MLflow artifact 路由）
3. RND 内在奖励在实机上的调参数值（β 系数）需要实验校准
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

**下一步计划**: 提交审查报告，等待批准后进入 Phase 4（v0.1.0 发布：联调收尾 + 文档补全 + 一键启动脚本完善）


