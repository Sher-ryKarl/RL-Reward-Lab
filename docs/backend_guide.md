# RL-Reward-Lab 后端开发者指南

> 版本：v1.3.0 | 最后更新：2026-05-02

## 1. 环境变量全表

所有配置通过 `RL_LAB_` 前缀的环境变量注入，在 `backend/app/config.py` 中通过 `pydantic-settings` 解析。

| 变量 | 默认值 | 类型 | 说明 |
|------|--------|------|------|
| `RL_LAB_PORT` | `8000` | int | Uvicorn 监听端口 |
| `RL_LAB_DEBUG` | `false` | bool | SQLAlchemy echo + FastAPI debug |
| `RL_LAB_CORS_ORIGINS` | `http://localhost:5173,http://localhost` | str | 逗号分隔的允许源 |
| `RL_LAB_DATABASE_URL` | `sqlite+aiosqlite:///...rl_lab.db` | str | SQLAlchemy async 连接串 |
| `RL_LAB_MLFLOW_TRACKING_URI` | `sqlite:///...mlflow.db` | str | MLflow 追踪 URI |
| `RL_LAB_SECRET_KEY` | 开发用默认值 | str | JWT HS256 签名密钥 |
| `RL_LAB_ADMIN_PASSWORD` | `admin123` | str | 管理员初始密码 (bcrypt 哈希后存储) |
| `RL_LAB_RATE_LIMIT` | `30/minute` | str | 写端点速率限制 |
| `RL_LAB_DEFAULT_TOTAL_STEPS` | `50000` | int | 新建实验默认训练步数 |
| `RL_LAB_MAX_TOTAL_STEPS` | `2000000` | int | 单次训练最大步数 |
| `RL_LAB_MAX_CONCURRENT_RUNS` | `4` | int | 同时训练的 Run 数量上限 |
| `RL_LAB_DEVICE` | `cuda` 或 `cpu` (自动检测) | str | PyTorch 设备 |
| `RL_LAB_DATA_DIR` | `<project_root>/data` | path | 数据持久化目录 |

依据：`backend/app/config.py:9-44`、`.env.example:1-36`

---

## 2. 项目结构

```
backend/
├── app/
│   ├── main.py                    # FastAPI 应用入口、lifespan、中间件注册
│   ├── config.py                  # pydantic-settings 配置类
│   ├── api/
│   │   ├── deps.py                # get_db, get_current_user 依赖
│   │   └── routes/
│   │       ├── auth.py            # POST /login, /register, GET /me
│   │       ├── experiments.py     # CRUD + HPO + Pareto recommend
│   │       ├── runs.py            # GET/DELETE run + replay video
│   │       ├── stream.py          # SSE /runs/{id}/stream
│   │       ├── demos.py           # Demo CRUD + collect
│   │       ├── rewards.py         # 内置 + 自定义奖励
│   │       ├── envs.py            # 环境列表
│   │       └── algos.py           # 算法列表
│   ├── core/
│   │   ├── auth.py                # JWT 签发/验证, bcrypt 哈希
│   │   ├── rate_limit.py          # Token-bucket ASGI 中间件
│   │   ├── registry.py            # ENV_REGISTRY, ALGO_REGISTRY, 兼容性检查
│   │   └── reward_editor.py       # AST 沙盒校验 + JSON 持久化
│   ├── db/
│   │   ├── models.py              # User, Experiment, Run, Demo ORM
│   │   └── database.py            # engine, async_session, init_db (迁移)
│   ├── rewards/
│   │   ├── base.py                # RewardSpec 基类
│   │   ├── variants.py            # R0-R4 5 个内置奖励 + 注册表
│   │   ├── wrappers.py            # PBRSWrapper, DenseProgressWrapper, ...
│   │   ├── rnd.py                 # RND 内在动机回调
│   │   └── custom_spec.py         # CustomRewardSpec
│   ├── schemas/
│   │   └── api.py                 # Pydantic v2 请求/响应模型
│   └── workers/
│       ├── scheduler.py           # 训练调度、信号量、bridge、ProcessPoolExecutor
│       ├── run_one.py             # 单个训练 run 的执行（在子进程中运行）
│       ├── hpo.py                 # Optuna NSGA-II/TPE sweep
│       ├── callbacks.py           # StreamCallback (训练 → mp.Queue)
│       └── collect_demo.py        # 专家轨迹收集
├── tests/
│   ├── test_api.py                # 53 个 API 集成测试
│   └── conftest.py                # pytest fixtures
├── Dockerfile                     # 生产镜像
├── pyproject.toml                 # 依赖与构建配置
└── uv.lock                        # 依赖锁定
```

---

## 3. 启动与数据库初始化

### 启动命令

```bash
# 开发模式 (热重载)
uv run uvicorn app.main:app --reload --port 8000

# 生产模式 (Docker)
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Lifespan 事件

```python
# backend/app/main.py:19-22
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()   # 启动时执行
    yield              # 应用运行中
    # shutdown 暂无需清理
```

### `init_db()` 执行顺序

```python
# backend/app/db/database.py:30-88
async def init_db() -> None:
    async with engine.begin() as conn:
        # 1. 建表 (SQLAlchemy Base.metadata.create_all)
        await conn.run_sync(Base.metadata.create_all)

        # 2. 幂等迁移 (SQLite 不支持 IF NOT EXISTS for ALTER TABLE)
        _migrations = [
            ("experiment", "user_id", "VARCHAR(12) REFERENCES \"user\"(id)"),
            ("demo", "user_id", "VARCHAR(12) REFERENCES \"user\"(id)"),
        ]
        for tbl, col, col_def in _migrations:
            try:
                await conn.execute(
                    text(f"ALTER TABLE {tbl} ADD COLUMN {col} {col_def}")
                )
            except Exception:
                pass  # Column already exists

        # 3. 种子 admin 用户 (如果不存在)
        result = await conn.execute(
            text("SELECT id FROM \"user\" WHERE username = 'admin'")
        )
        if result.fetchone() is None:
            hashed = bcrypt.hashpw(
                settings.admin_password.encode(), bcrypt.gensalt()
            ).decode()
            uid = secrets.token_hex(6)
            await conn.execute(
                text("INSERT INTO \"user\" (id, username, hashed_password, created_at) "
                     "VALUES (:id, 'admin', :pw, datetime('now'))"),
                {"id": uid, "pw": hashed},
            )

        # 4. 将旧数据 (无 user_id) 归属到 admin
        for tbl in ("experiment", "demo"):
            result = await conn.execute(
                text(f"SELECT COUNT(*) FROM {tbl} WHERE user_id IS NULL")
            )
            if result.scalar_one() > 0:
                await conn.execute(
                    text(f"UPDATE {tbl} SET user_id = :uid WHERE user_id IS NULL"),
                    {"uid": admin_id},
                )
```

> **注意**：`ASGITransport`（pytest 使用的 httpx 传输层）**不触发 lifespan 事件**。因此测试中通过独立的 session-scoped fixture 手动执行建表和种子数据。

---

## 4. API 路由组织

### 路由注册

```python
# backend/app/main.py:41-48
app.include_router(algos.router)         # /api/v1/algos
app.include_router(auth.router)          # /api/v1/auth/*
app.include_router(demos.router)         # /api/v1/demos
app.include_router(envs.router)          # /api/v1/envs
app.include_router(rewards.router)       # /api/v1/rewards
app.include_router(experiments.router)   # /api/v1/experiments/*
app.include_router(runs.router)          # /api/v1/runs/*
app.include_router(stream.router)        # /api/v1/runs/{id}/stream
```

### 端点速查

| 方法 | 路径 | 处理器文件 | 限速 | 认证 |
|------|------|-----------|------|------|
| POST | `/api/v1/auth/register` | `routes/auth.py:42` | 是 | 否 |
| POST | `/api/v1/auth/login` | `routes/auth.py:28` | 是 | 否 |
| GET | `/api/v1/auth/me` | `routes/auth.py:63` | 否 | 是 |
| GET | `/api/v1/envs` | `routes/envs.py` | 否 | 否 |
| GET | `/api/v1/algos` | `routes/algos.py` | 否 | 否 |
| GET | `/api/v1/rewards` | `routes/rewards.py:24` | 否 | 是 |
| POST | `/api/v1/rewards/custom` | `routes/rewards.py:42` | 是 | 是 |
| DELETE | `/api/v1/rewards/custom/{id}` | `routes/rewards.py:61` | 是 | 是 |
| GET | `/api/v1/experiments` | `routes/experiments.py:121` | 否 | 是 |
| POST | `/api/v1/experiments` | `routes/experiments.py:36` | 是 | 是 |
| GET | `/api/v1/experiments/{id}` | `routes/experiments.py:161` | 否 | 是 |
| GET | `/api/v1/experiments/{id}/optimization` | `routes/experiments.py:179` | 否 | 是 |
| POST | `/api/v1/experiments/{id}/pareto/recommend` | `routes/experiments.py:270` | 是 | 是 |
| GET | `/api/v1/runs/{id}` | `routes/runs.py:20` | 否 | 否 |
| DELETE | `/api/v1/runs/{id}` | `routes/runs.py:39` | 是 | 是 |
| GET | `/api/v1/runs/{id}/stream` | `routes/stream.py:23` | 否 | 否 |
| GET | `/api/v1/runs/{id}/replay` | `routes/runs.py:62` | 否 | 否 |
| GET | `/api/v1/demos` | `routes/demos.py:21` | 否 | 是 |
| POST | `/api/v1/demos` | `routes/demos.py:32` | 是 | 是 |
| DELETE | `/api/v1/demos/{id}` | `routes/demos.py:106` | 是 | 是 |
| GET | `/health` | `main.py:52` | 否 | 否 |

---

## 5. 认证与多用户

### JWT 流程

```
注册:  POST /register {username, password}
       → 校验 username 唯一性 (DB query)
       → bcrypt.hashpw(password)
       → INSERT User
       → jwt.encode({"sub": user.id, "exp": now+24h}, secret_key, HS256)
       → 返回 {access_token, user: {id, username}}

登录:  POST /login {username, password}
       → SELECT User WHERE username = body.username
       → bcrypt.checkpw(password, user.hashed_password)
       → jwt.encode(...)
       → 返回 {access_token, user: {id, username}}

请求:  GET /api/v1/experiments
       → HTTPBearer 提取 Authorization: Bearer <token>
       → jwt.decode(token, secret_key) → 提取 user_id ("sub")
       → SELECT User WHERE id = user_id
       → 返回 User ORM 对象 (注入到路由处理器的 _user 参数)
```

依据：`backend/app/api/routes/auth.py:27-65`、`backend/app/core/auth.py:16-30`、`backend/app/api/deps.py:28-69`

### 测试认证旁路

```python
# backend/app/api/deps.py:32-48
async def get_current_user(...) -> User:
    if os.environ.get("PYTEST_CURRENT_TEST"):
        # 测试模式下：自动以 admin 身份认证
        result = await db.execute(select(User).where(User.username == "admin"))
        user = result.scalar_one_or_none()
        if user is None:
            # 首次运行：动态创建 admin
            user = User(id=_new_user_id(), username="admin",
                        hashed_password=hash_password(settings.admin_password))
            db.add(user)
            await db.commit()
        return user
    # ... 正常 JWT 解析逻辑
```

> 这个旁路是必需的，因为 `httpx.ASGITransport` 不会触发 FastAPI lifespan，导致 `init_db()` 中的 admin 种子不执行。

### 多用户数据隔离实现

所有带 `_user` 参数的路由都在查询中附加 `WHERE user_id = _user.id`：

```python
# backend/app/api/routes/experiments.py:131 — 列表过滤
stmt = select(Experiment).where(Experiment.user_id == _user.id)

# backend/app/api/routes/experiments.py:168 — 详情过滤
where(Experiment.id == exp_id, Experiment.user_id == _user.id)

# backend/app/api/routes/runs.py:40-44 — Run 通过 JOIN 验证所有权
select(RunModel)
    .join(Experiment, RunModel.experiment_id == Experiment.id)
    .where(RunModel.id == run_id, Experiment.user_id == _user.id)

# backend/app/core/reward_editor.py:97-101 — 自定义奖励过滤
def list_custom(user_id: str = "") -> list[dict]:
    if user_id:
        return [e for e in all_entries if e.get("user_id") == user_id]
```

---

## 6. 训练调度器详解

### 数据流图

参见 [架构文档第 3 节](architecture.md#3-训练子进程通信核心架构决策)。

### 关键代码路径

**`schedule_run()`** — `backend/app/workers/scheduler.py:57-101`：

```python
async def schedule_run(run_model, experiment, queue):
    mp_queue = _manager.Queue(maxsize=500)        # 跨进程代理队列

    async with _run_semaphore:                     # 限制并发
        bridge_task = asyncio.create_task(
            _bridge(mp_queue, queue, run_model.id) # 启动转发
        )

        await loop.run_in_executor(
            executor,                               # ProcessPoolExecutor
            run_one,                                # 子进程入口
            run_model.id, experiment.env_id, ...
            mp_queue,                               # 子进程通过此队列回传数据
        )
    # finally: 发送 None 哨兵 → 等待 bridge 排空 → 清理
```

**`_bridge()`** — `backend/app/workers/scheduler.py:40-55`：

```python
async def _bridge(mp_queue, async_queue, run_id):
    loop = asyncio.get_running_loop()
    while True:
        try:
            msg = await loop.run_in_executor(
                None,
                lambda: mp_queue.get(timeout=1.0),  # 阻塞在 executor 线程中
            )
            if msg is None:   # 哨兵信号
                break
            await async_queue.put(msg)
        except Exception:
            continue           # 超时则继续轮询
```

**`run_one()`** — `backend/app/workers/run_one.py:53-178`：

```python
def run_one(run_id, env_id, reward_id, algo, hp, total_steps, seed, queue):
    spec = REWARD_REGISTRY[reward_id]

    def make_env():
        e = gym.make(env_id)
        e = spec.wrap(e, env_id=env_id)
        e = Monitor(e)
        return e

    vec = DummyVecEnv([make_env])

    # 算法分发
    if algo == "PPO":
        model = PPO("MlpPolicy", vec, **algo_hp)
    elif algo == "DQN":
        model = DQN("MlpPolicy", vec, **algo_hp)
    elif algo == "SAC":
        model = SAC("MlpPolicy", vec, **algo_hp)
    elif algo == "BC":
        model = BCPolicyWrapper(bc_trainer.policy, ...)

    # 训练 (回调每 1000 步向 mp_queue 推送指标)
    model.learn(total_timesteps=total_steps,
                callback=StreamCallback(queue, run_id, reward_id, every=1000))

    # 保存模型 + 录制回放视频 + 发送完成信号
    model.save(checkpoint_path)
    mlflow.log_artifact(checkpoint_path)
    _record_replay(env_id, spec, model, run_id)
```

### 并发控制

```python
# backend/app/workers/scheduler.py:32-34
_run_semaphore = asyncio.Semaphore(
    min(settings.max_concurrent_runs, MAX_CPU_WORKERS)
)
```

- `MAX_CPU_WORKERS = cpu_count - 2`（最少 1）
- 每个训练 Run 获取一个信号量槽位
- `async with _run_semaphore:` 确保同时训练数不超过上限

---

## 7. HPO 引擎详解

### 入口

```python
# backend/app/api/routes/experiments.py:88-96
background_tasks.add_task(
    _execute_optimization,
    exp.id, body.search_space, body.n_trials, body.reward_ids, hp,
)
```

### `run_sweep()` 流程

```python
# backend/app/workers/hpo.py:151-293
async def run_sweep(exp_id, env_id, algo_id, total_steps,
                    search_space, n_trials, reward_ids, fixed_hp, n_objectives=3):
    # 1. 创建 Optuna study
    if n_objectives >= 2:
        sampler = NSGAIISampler(seed=0)
        study = optuna.create_study(
            study_name=f"sweep-{exp_id}",
            storage=RDBStorage(url=settings.database_url...),
            sampler=sampler,
            directions=["maximize", "minimize", "minimize"][:n_objectives],
        )
    else:
        # 单目标回退 (TPE)
        study = optuna.create_study(sampler=TPESampler(), direction="maximize")

    # 2. 运行所有 trial (在 executor 中同步执行)
    trial_results = await loop.run_in_executor(None, _run_trials)

    # 3. 计算 Pareto 前沿
    pareto_indices = _compute_pareto_front(trial_results)

    # 4. 写 Run 记录到数据库
    for tr in trial_results:
        run = RunModel(
            experiment_id=exp_id,
            reward_id=tr["reward_id"],
            seed=tr["trial_number"],
            hyperparams=tr["params"],
            status="done",
            final_metrics={...},
        )
        db.add(run)
```

### 搜索空间采样

```python
# backend/app/workers/hpo.py:128-148
def _sample_params(trial, search_space, fixed_hp):
    hp = {}
    for name, spec in search_space.items():
        dist = spec.get("type", "float")
        if dist == "loguniform":
            hp[name] = trial.suggest_float(name, spec["low"], spec["high"], log=True)
        elif dist == "uniform":
            hp[name] = trial.suggest_float(name, spec["low"], spec["high"])
        elif dist == "int":
            hp[name] = trial.suggest_int(name, spec["low"], spec["high"])
        elif dist == "categorical":
            hp[name] = trial.suggest_categorical(name, spec["choices"])
    # 合并固定超参
    for name, val in fixed_hp.items():
        hp.setdefault(name, val)
    return hp
```

### 收敛检测回调

```python
# backend/app/workers/hpo.py:41-60
class _ConvergenceCallback(BaseCallback):
    def _on_step(self) -> bool:
        if self.n_calls % self.check_freq != 0:
            return True
        recent = [ep["r"] for ep in self.model.ep_info_buffer]
        if np.mean(recent) >= self.baseline:
            self.convergence_step = self.num_timesteps  # 记录收敛步数
        return True
```

---

## 8. 奖励沙盒安全模型

### 安全分层

```
第1层: AST 白名单 → 禁止危险语法
第2层: 内置函数白名单 → 禁止 os/system/eval/exec
第3层: 导入白名单 → 仅允许 math, numpy
第4层: ProcessPoolExecutor 子进程隔离 → 训练代码在独立进程中运行
```

依据：`backend/app/core/reward_editor.py:26-185`

### AST 节点白名单

```python
# backend/app/core/reward_editor.py:33-51
ALLOWED_AST_NODES = {
    ast.Module, ast.FunctionDef, ast.arguments, ast.arg,
    ast.Return, ast.Assign, ast.AugAssign,
    ast.BinOp, ast.UnaryOp, ast.BoolOp, ast.Compare,
    ast.If, ast.IfExp, ast.Name, ast.Constant, ast.Attribute,
    ast.Call, ast.Expr, ast.Pass, ast.Break, ast.Continue,
    ast.For, ast.While, ast.Load, ast.Store,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod,
    ast.USub, ast.UAdd, ast.Not, ast.Invert,
    ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
    ast.And, ast.Or,
    ast.Tuple, ast.List, ast.Dict, ast.Subscript, ast.Slice,
    ast.Index, ast.Starred, ast.keyword,
    ast.Import, ast.ImportFrom, ast.alias,
}
```

### 校验步骤

```python
# backend/app/core/reward_editor.py:122-181
def validate(code: str) -> None:
    # 1. AST 解析
    tree = ast.parse(code)

    # 2. 检查函数定义数量 == 1
    func_defs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    if len(func_defs) != 1:
        raise ValueError(f"found {len(func_defs)} function definitions, expected 1")

    # 3. 函数名必须为 "reward_fn"
    if fn.name != "reward_fn":
        raise ValueError(...)

    # 4. 签名必须为 (obs, reward, terminated, truncated)
    param_names = [a.arg for a in fn.args.args]
    if param_names != ["obs", "reward", "terminated", "truncated"]:
        raise ValueError(...)

    # 5. 遍历所有 AST 节点 → 白名单检查
    for node in ast.walk(tree):
        if type(node) not in ALLOWED_AST_NODES:
            raise ValueError(f"Disallowed syntax: {type(node).__name__}")

    # 6. 检查内置函数引用
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            if node.id in builtins and node.id not in ALLOWED_BUILTINS:
                raise ValueError(f"Disallowed builtin: '{node.id}'")

    # 7. 检查 import 语句 → 白名单
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] not in ALLOWED_IMPORTS:
                    raise ValueError(f"Disallowed import: '{alias.name}'")
        elif isinstance(node, ast.ImportFrom):
            if node.module.split(".")[0] not in ALLOWED_IMPORTS:
                raise ValueError(f"Disallowed import from: '{node.module}'")
```

### 持久化

```python
# backend/app/core/reward_editor.py:84-91
def register(code: str, name: str = "", user_id: str = "") -> str:
    validate(code)                                              # 先校验
    rid = _hash(code)  # C_ + SHA256[:12]                      # 幂等去重
    _custom_rewards[rid] = {"code": code, "name": name, "user_id": user_id}
    _save_persisted()                                           # 写 JSON 文件
    return rid
```

### 子进程加载

```python
# backend/app/rewards/variants.py:166-183
def _load_custom_rewards_into_registry() -> None:
    from app.core.reward_editor import list_custom
    from app.rewards.custom_spec import CustomRewardSpec

    for entry in list_custom():
        rid = entry["reward_id"]
        if rid not in REWARD_REGISTRY:
            REWARD_REGISTRY[rid] = CustomRewardSpec(rid, entry["name"], entry["code"])

_load_custom_rewards_into_registry()  # import 时自动执行
```

> Windows spawn 模式下，子进程从零启动 Python，`variants.py` 被 import 时自动调用 `_load_custom_rewards_into_registry()`，保证自定义奖励对子进程可见。

---

## 9. 添加新环境/算法/奖励

### 添加新环境

1. 在 `backend/app/core/registry.py:33-64` 的 `ENV_REGISTRY` 中添加条目：
```python
"MyNewEnv-v0": EnvMeta(
    env_id="MyNewEnv-v0",
    name="My New Env",
    action_space="discrete",  # or "continuous"
    baseline_reward=200,      # 收敛参考值
),
```

2. 在 `backend/app/rewards/variants.py` 的 `_progress_fn()`、`_phi_fn()`、`_misleading_fn()` 中为新环境添加分支（可选——已有默认降级逻辑）。

3. 在 `backend/app/api/routes/envs.py` 中确认 `list_envs()` 自动从 `ENV_REGISTRY` 读取。

### 添加新算法

1. 在 `backend/app/core/registry.py:66-130` 的 `ALGO_REGISTRY` 中添加条目：
```python
"MY_ALGO": AlgoMeta(
    algo_id="MY_ALGO",
    name="My Algorithm",
    discrete=True,
    continuous=False,
    default_hp={"learning_rate": 1e-3, ...},
),
```

2. 在 `backend/app/workers/run_one.py:95-140` 的 `run_one()` 中添加分支：
```python
elif algo == "MY_ALGO":
    model = MyAlgo("MlpPolicy", vec, device=settings.device, seed=seed, **algo_hp)
```

3. 在 `backend/app/workers/hpo.py:94-101` 的 `_objective()` 中同样添加分支。

### 添加新内置奖励

1. 在 `backend/app/rewards/variants.py` 中添加新的 `RewardSpec` 子类：
```python
class MyNewReward(RewardSpec):
    id = "R5_my_new"
    name = "My New Reward"
    description = "..."
    source_type = "handcrafted"
    terms = ["extrinsic"]

    def wrap(self, env: gym.Env, env_id: str = "") -> gym.Env:
        return MyNewWrapper(env)
```

2. 将实例添加到 `REWARD_REGISTRY` 字典中。

---

## 10. 测试指南

### 运行测试

```bash
# 全部测试
pytest backend/tests/ -q

# 单个测试
pytest backend/tests/test_api.py::test_create_experiment_basic -q

# 带详细输出
pytest backend/tests/ -v
```

### 测试架构

```python
# backend/tests/test_api.py — 使用 session-scoped fixture
@pytest.fixture(scope="session")
def _init_test_db():
    """手动建表 + 种子 admin, 解决 ASGITransport 不触发 lifespan 的问题."""
    import os
    os.environ["PYTEST_CURRENT_TEST"] = "1"

    # 删除旧 DB
    db_path = Path("data/test_rl_lab.db")
    if db_path.exists():
        db_path.unlink()

    # 使用同步 SQLite engine 建表
    sync_engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(sync_engine)

    # 种子 admin 用户
    with sync_engine.connect() as conn:
        conn.execute(text("INSERT INTO user (...) VALUES (...)"))
        conn.commit()

# 测试客户端
@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
```

### 关键注意事项

| 陷阱 | 原因 | 解决方案 |
|------|------|----------|
| Rate limit 污染 | `_bucket` 是全局单例 | 在 finally 块中 `_bucket._buckets.clear()` |
| Username 冲突 | SQLite DB 持久化 | session fixture 在开始时删除旧 DB 文件 |
| PermissionError | function fixture delete/recreate DB | 改用 session-scoped + sync engine |
| 422 instead of 401 | LoginBody 新增 username 必填字段 | 测试 body 需包含 `{"username": "admin", "password": "admin123"}` |

### 测试清单（53 项）

| 类别 | 数量 | 示例 |
|------|------|------|
| Auth (注册/登录/me) | 6 | `test_register_success`, `test_register_username_conflict` |
| Experiment CRUD | 5 | `test_create_experiment_basic`, `test_list_experiments` |
| Run 管理 | 4 | `test_cancel_run`, `test_get_run_not_found` |
| Demo 管理 | 4 | `test_create_demo`, `test_delete_demo` |
| 自定义奖励 | 3 | `test_create_custom_reward`, `test_custom_reward_syntax_error` |
| HPO / Pareto | 5 | `test_optimization_result`, `test_pareto_recommend` |
| 速率限制 | 3 | `test_rate_limit_writes`, `test_rate_limit_bypass_gets` |
| 跨用户隔离 | 3 | `test_cross_user_read_isolation`, `test_cross_user_write_rejected` |
| 环境/算法/健康 | 5 | `test_list_envs`, `test_list_algos`, `test_health_check` |
| 边界/校验 | 15 | `test_bc_requires_demo`, `test_invalid_algo_env_combo` 等 |
