# RL-Reward-Lab 用户手册

> 版本：v1.3.0 | 最后更新：2026-05-01

## 目录

1. [快速开始](#1-快速开始)
2. [平台概览](#2-平台概览)
3. [环境与算法](#3-环境与算法)
4. [奖励函数设计](#4-奖励函数设计)
5. [创建与管理实验](#5-创建与管理实验)
6. [演示数据与行为克隆](#6-演示数据与行为克隆)
7. [自动化超参优化 (HPO)](#7-自动化超参优化-hpo)
8. [交互式 Pareto 决策](#8-交互式-pareto-决策)
9. [多用户协作](#9-多用户协作)
10. [部署与运维](#10-部署与运维)
11. [常见问题 (FAQ)](#11-常见问题-faq)
12. [附录](#12-附录)

---

## 1. 快速开始

### 1.1 前提条件

- **Docker Desktop**（推荐）或 Podman（见附录 Linux 配置）
- 至少 4 GB 可用磁盘空间
- （可选）Python ≥3.10 + Node.js ≥18（用于本地开发）

### 1.2 一键启动（Docker，推荐）

```bash
git clone https://github.com/Sher-ryKarl/RL-Reward-Lab.git
cd RL-Reward-Lab
docker compose up -d
```

启动后：

| 服务 | 地址 |
|------|------|
| 前端界面 | [http://localhost](http://localhost) |
| 后端健康检查 | [http://localhost:8000/health](http://localhost:8000/health) |

默认管理员账号：`admin` / `admin123`（**首次登录后务必修改密码**）。

### 1.3 本地开发

```bash
# 后端
pip install uv
uv pip install --system -e ".[dev]"
uv run uvicorn app.main:app --reload --port 8000

# 前端 (另一个终端)
cd frontend && npm install --legacy-peer-deps && npm run dev
```

打开 [http://localhost:5173](http://localhost:5173)。

### 1.4 修改默认管理员密码

编辑项目根目录下的 `.env` 文件（从 `.env.example` 复制）：

```bash
cp .env.example .env
```

修改以下行：

```env
RL_LAB_ADMIN_PASSWORD=你的安全密码
```

重启服务后生效：

```bash
docker compose down && docker compose up -d
```

---

## 2. 平台概览

### 2.1 核心概念

RL-Reward-Lab 是一个**强化学习奖励函数设计与自动调参可视化化平台**。它解决的核心问题是：

> 同样的 RL 算法，奖励函数设计不同，训练结果天差地别。
> 手工尝试每个奖励 × 每个超参的组合极其耗时，
> 而本平台让你在一个界面中**批量创建、可视化对比、自动搜索最优组合**。

### 2.2 工作流程

```
1. 注册/登录
      ↓
2. 选择环境 + 算法 + 奖励函数（可多选）
      ↓
3. （可选）开启 Optuna 自动超参搜索
      ↓
4. 提交实验 → 后台开始训练
      ↓
5. 实时监控学习曲线、多奖励对比
      ↓
6. （可选）从训练好的策略收集专家演示 → 行为克隆
      ↓
7. Pareto 前沿分析 → 选出最优 Trial
```

### 2.3 导航结构

| 页面 | 路由 | 功能 |
|------|------|------|
| 实验列表 | `/` | 浏览、筛选、搜索、批量对比实验 |
| 新建实验 | `/new` | 配置环境/算法/奖励/超参，提交训练 |
| 实验详情 | `/experiments/:id` | 实时监控曲线、回放视频、HPO 分析 |
| 演示管理 | `/demos` | 管理专家演示数据，一键 BC 克隆 |
| 批量对比 | `/compare?ids=...` | 多实验多 Run 的学习曲线叠加对比 |
| 登录 | `/login` | 账号登录 |
| 注册 | `/register` | 创建新账号 |

### 2.4 全局特性

- **数据隔离**：每个用户只能看到自己的实验、演示和自定义奖励
- **速率限制**：创建/修改类操作 30 次/分钟（GET 读取不限）
- **自动刷新**：实验列表和详情页每 3–5 秒轮询最新状态
- **实时流**：学习曲线通过 SSE (Server-Sent Events) 推送，无需手动刷新

---

## 3. 环境与算法

### 3.1 支持的 5 个 Gymnasium 环境

| 环境 ID | 名称 | 动作空间 | 目标 | 参考收敛分数 |
|---------|------|----------|------|-------------|
| `MountainCar-v0` | Mountain Car | Discrete (3) | 小车冲上右坡顶 | ≥ -110 |
| `CartPole-v1` | CartPole | Discrete (2) | 平衡摆杆不落 | ≥ 195 |
| `LunarLander-v2` | Lunar Lander | Discrete (4) | 平稳着陆月面 | ≥ 200 |
| `Acrobot-v1` | Acrobot | Discrete (3) | 双连杆摆到目标高度 | ≥ -100 |
| `Pendulum-v1` | Pendulum | Continuous (1) | 倒立摆上摆稳定 | ≥ -500 |

### 3.2 支持的 4 个算法

| 算法 ID | 名称 | 适用环境 | 特点 |
|---------|------|----------|------|
| `PPO` | Proximal Policy Optimization | Discrete + Continuous | 通用标杆算法，稳定性好 |
| `DQN` | Deep Q-Network | Discrete only | 离线策略，经验回放 |
| `SAC` | Soft Actor-Critic | Continuous only | 最大熵探索，适合连续动作 |
| `BC` | Behavioral Cloning | Discrete + Continuous | 从专家演示数据模仿学习 |

### 3.3 环境-算法兼容性

在新建实验页面，选择环境后，不兼容的算法会自动灰掉（不可选）：

| 环境 | PPO | DQN | SAC | BC |
|------|-----|-----|-----|----|
| MountainCar (Discrete) | ✓ | ✓ | ✗ | ✓ |
| CartPole (Discrete) | ✓ | ✓ | ✗ | ✓ |
| LunarLander (Discrete) | ✓ | ✓ | ✗ | ✓ |
| Acrobot (Discrete) | ✓ | ✓ | ✗ | ✓ |
| Pendulum (Continuous) | ✓ | ✗ | ✓ | ✓ |

### 3.4 可调超参（以 PPO 为例）

每个算法的默认超参已预设，你可以自由修改：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `learning_rate` | 3e-4 | 学习率 |
| `n_steps` | 2048 | 每轮收集步数 |
| `batch_size` | 64 | 训练批次大小 |
| `gamma` | 0.99 | 折扣因子 |
| `gae_lambda` | 0.95 | GAE 平滑系数 |
| `ent_coef` | 0.0 | 熵正则化系数 |
| `clip_range` | 0.2 | PPO 裁剪范围 |

> **提示**：如果你想自动搜索最优超参组合，请参考[第 7 章——自动化超参优化](#7-自动化超参优化-hpo)。

---

## 4. 奖励函数设计

### 4.1 什么是奖励函数？

奖励函数是 RL 的"指挥棒"——agent 根据奖励信号调整策略。一个设计不当的奖励函数会导致 agent "刷分"而不是完成目标任务（这就是 *reward hacking*）。

### 4.2 5 种内置奖励变体

| ID | 名称 | 原理 | 最佳教学用途 |
|----|------|------|-------------|
| **R0_sparse** | Sparse (终局成功) | 仅达成目标给 +1，其余为 0 | 演示"无 shaping 学不会" |
| **R1_dense** | Dense (进度信号) | 根据位置/高度/角度给出连续进度分数 | 与 Sparse 对比，展示 shaping 的作用 |
| **R2_pbrs_potential** | PBRS (势函数塑形) | Φ(s') - Φ(s)，策略不变形塑形 | 展示有理论保证的 shaping 方法 |
| **R3_curiosity_rnd** | Curiosity (RND 内在动机) | 内在探索奖励 + 稀疏外部奖励 | 展示探索驱动 vs 奖励塑形 |
| **R4_misleading** | ⚠ Misleading (教学反例) | 奖励速度/角速度而非任务目标 | reward hacking 的反面教材 |

### 4.3 各环境下的奖励行为

**MountainCar-v0（小车爬山）：**
- R0_sparse：只有到达旗帜 +1，其余 0 → **通常学不会**
- R1_dense：`r = position + 1.2`，越靠右分越高
- R2_pbrs：`Φ(s) = position + 0.5 × velocity²`
- R3_curiosity：Sparse + RND 探索奖励
- R4_misleading：奖励 `|velocity|` → agent 原地来回晃

**CartPole-v1（倒立摆平衡）：**
- R1_dense：`r = position + 1.2`
- R4_misleading：奖励 `|velocity|` → agent 疯狂晃动

**LunarLander-v2（月球着陆）：**
- R1_dense：`r = altitude`（高度作为进度）
- R2_pbrs：`Φ(s) = altitude + 0.3 × uprightness`
- R4_misleading：奖励 `|vx| + |vy|` → 鼓励高速下坠

**Pendulum-v1（倒立摆连续控制）：**
- R1_dense：`r = cos(θ)` → 越接近直立越好
- R2_pbrs：`Φ(s) = cos(θ) - 0.5 × θ̇²`
- R4_misleading：奖励 `|angular velocity|` → 鼓励不停旋转

### 4.4 自定义奖励函数（! 实验性）

在新建实验页面，点击奖励选择区的"**Edit**"按钮，打开 Monaco 代码编辑器。

**编写规则**：
- 定义一个 `reward_fn(obs, reward, terminated, truncated) -> float` 函数
- 作用域内可以使用 `import gymnasium as gym`、`import numpy as np`、`import math`
- **禁止导入**：`os`、`sys`、`subprocess`、`socket`、`eval`、`exec` 等危险模块

**示例——自定义稠密奖励（CartPole）：**

```python
def reward_fn(obs, reward, terminated, truncated):
    # 平衡杆角度越小、小车位置越居中越好
    x, v, theta, theta_dot = obs
    r = 1.0 - abs(theta) * 2.0 - abs(x) * 0.5
    if terminated:
        r -= 10.0  # 失败惩罚
    return r
```

提交后，自定义奖励会出现在奖励选择列表中（名称带你的用户 ID 前缀），可以和其他内置奖励一起参与实验。

**安全机制**：
- 代码经过 AST 白名单校验，阻止危险模块导入
- 代码持久化到磁盘，重启后仍然可用
- 每个用户只能删除自己创建的自定义奖励

---

## 5. 创建与管理实验

### 5.1 创建实验

操作步骤：

1. 点击导航栏 **"New"** 或实验列表页的 **"+ New"** 按钮
2. 填写/选择以下配置（带 * 为必填）：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| Experiment Name | 实验名称，留空自动生成时间戳名 | `Exp-xxx` |
| Environment | 从 5 个环境中选择 | `MountainCar-v0` |
| Algorithm | PPO / DQN / SAC / BC | `PPO` |
| Reward Variants | 多选，至少选一个 | `R0_sparse, R1_dense` |
| Hyperparameters | 可修改任意参数 | 各算法默认值 |
| Total Steps | 总训练步数（BC 为批次数） | 50,000 |
| Seeds | 随机种子，逗号分隔 | `0` |

3. （可选）开启 **Optuna HPO** 开关——详见[第 7 章](#7-自动化超参优化-hpo)
4. 点击 **"Start Experiment"**

**多奖励 × 多种子**：如果你选择了 5 个奖励变体 + 3 个 seed，系统会创建 5×3 = 15 个独立的训练 Run。

**示例**：
- 环境：`CartPole-v1`
- 算法：`PPO`
- 奖励：`R0_sparse`、`R1_dense`、`R2_pbrs_potential`
- Seeds：`0,1,2`
- Steps：`50000`

→ 提交后生成 1 个 Experiment，包含 9 个 Run。

### 5.2 监控实验

在实验详情页面，你可以：

**实时学习曲线**：
- 点击任意 Run 按钮，下方实时显示该 Run 的 episode reward 曲线
- 曲线通过 SSE 推送，无需手动刷新
- 连接状态：Live（绿色）/ Reconnecting（黄色）

**训练健康指标**（Health Card）：
- 最新 episode reward
- 平均 episode reward
- 学习率
- 总步数

**多 Run 对比**：
- 点击 **"Compare All (N)"**，叠加显示所有 Run 的学习曲线

**策略回放视频**：
- 训练完成的 Run 会自动录制 MP4 回放视频
- 在 Monitor 面板下方可观看

### 5.3 实验筛选与搜索

在实验列表页提供了四维筛选：

| 筛选器 | 用法 | 示例 |
|--------|------|------|
| 搜索框 | 按名称模糊搜索 | 输入 "cartpole" |
| Status | 按状态过滤 | `done`、`running` |
| Env ID | 按环境 ID 精确匹配 | `LunarLander-v2` |
| Algo ID | 按算法 ID 精确匹配 | `PPO` |

支持分页（10/20/50 条每页），状态每 5 秒自动刷新。

### 5.4 批量对比

1. 在实验列表页勾选 2 个以上实验
2. 点击绿色 **"Compare (N)"** 按钮
3. 跳转到对比页面，展示所有选中实验的所有 Run 学习曲线叠加

### 5.5 克隆实验

在实验详情页右上角，点击 **"Clone & Re-run"**，会自动跳转到新建实验页面并预填当前实验的环境和算法配置。

---

## 6. 演示数据与行为克隆

### 6.1 什么是演示数据（Demo）？

演示数据是**专家策略的 (状态, 动作) 轨迹数据集**，可用于 Behavioral Cloning（行为克隆）训练。

### 6.2 收集演示数据

1. 确保有一个状态为 **done** 的 PPO Run
2. 在实验详情页找到该 Run，点击 **"+Demo"** 按钮
3. 输入收集的 episode 数量（1–50，默认 5）
4. 点击 **"Collect"** → 后台用训练好的策略运行 N 个 episode，记录轨迹
5. 成功后提示 "Demo collected! Go to Demos page to view."

### 6.3 管理演示数据

前往 **Demos** 页面，可以：
- 查看所有已收集的 Demo（名称、环境、episode 数、步数）
- 点击 **"Clone (BC)"** → 自动跳转新建实验页，环境已匹配，算法预选 BC
- 点击 **"Delete"** → 删除 Demo

### 6.4 运行 Behavioral Cloning (BC)

1. 在 Demos 页面点击某个 Demo 的 **"Clone (BC)"**
2. 确认环境已自动匹配
3. 算法自动选为 **BC**
4. 在 "Clone Source" 下拉框中选择要克隆的 Demo
5. 设置 **Training Batches**（例如 100）
6. 点击 **"Start Experiment"**

BC 不需要设置奖励函数——它直接从演示数据模仿行为。

---

## 7. 自动化超参优化 (HPO)

### 7.1 概述

手动逐个尝试超参组合是低效的。RL-Reward-Lab 集成了 **Optuna**（TPE Sampler），自动探索"奖励函数 × 超参数"的最佳组合。

### 7.2 启用 HPO

1. 在新建实验页，勾选 **"Optuna Hyperparameter Optimization"**
2. 定义搜索空间（至少一个维度），例如：

```
learning_rate → loguniform(1e-5, 1e-2)
n_steps       → categorical(512, 1024, 2048)
gamma         → uniform(0.9, 1.0)
```

具体语法（`SearchSpaceEditor` 组件提供下拉选择）：
- `uniform(low, high)` —— 连续均匀分布
- `loguniform(low, high)` —— 对数均匀分布
- `categorical(a, b, c)` —— 离散选项
- `int(low, high)` —— 整数范围

3. 设置 **Number of Trials**（2–500，常用 30）
4. 确保至少选择一个奖励变体
5. 点击 **"Start Experiment"**

### 7.3 HPO 执行过程

- Optuna TPE 采样器在搜索空间内迭代 Trial
- 每个 Trial 自动训练指定步数，记录最终 ep_rew_mean
- 多奖励同时参与搜索——同一个超参组合会尝试不同奖励函数
- Trial 过程中的 Run 记录会自动创建到实验下

### 7.4 查看 HPO 结果

在实验详情页，HPO 实验会显示紫色的 **"Optuna Hyperparameter Search"** 统计面板，包含：

- **优化历史图**（Optimization History）：每个 Trial 的 objective value
- **参数重要性图**（Parameter Importances）：各超参对目标函数的影响权重
- **多奖励对比图**：各奖励函数下的最优值

### 7.5 多目标优化（NSGA-II）

平台默认使用**三目标优化**：

| 目标 | 方向 | 含义 |
|------|------|------|
| `ep_rew_mean` | ↑ 最大化 | 最终 episode reward |
| `wall_time` | ↓ 最小化 | 训练耗时 |
| `convergence_steps` | ↓ 最小化 | 达到收敛的步数 |

NSGA-II 算法同时优化这三个目标，并在 Pareto 前沿图中展示最优权衡解。

---

## 8. 交互式 Pareto 决策

### 8.1 什么是 Pareto 前沿？

在多目标优化中，很少有单一 Trial 在所有目标上都最优。Pareto 前沿（Pareto Front）是一组"**非被支配**"的解——任何 Pareto 上的 Trial 都不可能在不降低一个目标的情况下提升另一个目标。

### 8.2 查看 Pareto 前沿

在 HPO 实验详情页的 Optimization 面板中，包含三张可视化图表：

| 图表 | 说明 |
|------|------|
| **2D 散点图** | reward vs wall_time，Pareto 点高亮显示 |
| **3D 散点图** | reward × wall_time × convergence，Pareto 前沿一目了然 |
| **平行坐标图** | 展示 Pareto 点在各维度的分布 |

### 8.3 交互式权重推荐

在 Pareto 决策面板中，你可以：

1. **拖动权重滑块**：
   - 奖励权重（Reward Weight）：0–100
   - 速度权重（Speed Weight）：0–100
   - 收敛权重（Convergence Weight）：0–100

2. **添加约束过滤**（可选）：
   - 例如：`ep_rew_mean >= 200` —— 只看 reward 达到门槛的 Trial
   - 例如：`wall_time < 300` —— 只看训练时间在 300 秒内的 Trial
   - 支持 `<`、`<=`、`>`、`>=` 四种运算符

3. **查看推荐结果**：
   - 系统对所有满足约束的 Trial 做 min-max 归一化
   - 按你的权重加权计算综合得分
   - 返回得分最高的 **推荐 Trial**，并列出了所有 Trial 的得分排名

### 8.4 使用场景示例

> 我关心最终性能，但训练时间不能超过 5 分钟。

操作：
1. 添加约束：`wall_time < 300`
2. 权��：Reward=80, Speed=10, Convergence=10
3. 系统自动返回满足时间限制下 reward 最高的 Trial

---

## 9. 多用户协作

### 9.1 注册与登录

**注册**：
1. 访问 `/register`
2. 输入用户名（3–64 字符）和密码（≥6 字符）
3. 确认密码
4. 点击 "Create Account" → 成功后自动登录

**登录**：
1. 访问 `/login`
2. 输入用户名和密码
3. 点击 "Sign In"

### 9.2 数据隔离

每个用户的实验、演示和自定义奖励**完全隔离**：
- 用户 A 看不到用户 B 的实验
- 用户 A 不能删除、取消用户 B 的实验
- 自定义奖励以用户为单位进行读写控制

### 9.3 持久化凭证

- JWT Token 存储在浏览器 localStorage，有效期 24 小时
- 关闭浏览器后重新打开无需重新登录（Token 有效期内）
- 点击导航栏 **"Logout"** 清除凭证

### 9.4 默认管理员账号

首次启动时，系统自动创建管理员账号：

| 用户名 | 默认密码 |
|--------|----------|
| `admin` | `admin123` |

**部署到生产环境后务必立即修改密码**，方法见 [1.4 节](#14-修改默认管理员密码)。

> 目前所有用户的权限相同（均能创建实验、删除自己的数据），后续版本可能增加管理员面板。

---

## 10. 部署与运维

### 10.1 Docker Compose（生产推荐）

```bash
# 启动
docker compose up -d

# 停止
docker compose down

# 查看日志
docker compose logs -f backend

# 重建（代码更新后）
docker compose up -d --build
```

### 10.2 环境变量配置

所有可配置的环境变量（`.env` 文件）：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `RL_LAB_PORT` | `8000` | 后端端口 |
| `RL_LAB_DEBUG` | `false` | FastAPI debug 模式 |
| `RL_LAB_DATABASE_URL` | `sqlite+aiosqlite:////app/data/rl_lab.db` | 数据库连接串 |
| `RL_LAB_MLFLOW_TRACKING_URI` | `sqlite:////app/data/mlflow.db` | MLflow 追踪 URI |
| `RL_LAB_SECRET_KEY` | 开发用默认值 | JWT 签名密钥（生产请更换） |
| `RL_LAB_ADMIN_PASSWORD` | `admin123` | 管理员默认密码 |
| `RL_LAB_RATE_LIMIT` | `30/minute` | 写端点速率限制 |
| `RL_LAB_DEFAULT_TOTAL_STEPS` | `50000` | 默认训练步数 |
| `RL_LAB_MAX_TOTAL_STEPS` | `2000000` | 最大训练步数 |
| `RL_LAB_MAX_CONCURRENT_RUNS` | `4` | 同时训练的最大 Run 数 |
| `RL_LAB_DEVICE` | 自动检测 | `cpu` 或 `cuda` |
| `RL_LAB_CORS_ORIGINS` | `http://localhost` | 允许的前端域名（逗号分隔） |
| `FRONTEND_PORT` | `80` | 前端 Nginx 端口 |

### 10.3 从 SQLite 迁移到 PostgreSQL

```bash
# 1. 修改 .env
RL_LAB_DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/rl_lab

# 2. 重启
docker compose down && docker compose up -d
```

平台使用 SQLAlchemy，启动时自动创建表结构。

### 10.4 数据持久化

Docker Compose 将 `./data/` 目录挂载到容器内：

```
data/
├── rl_lab.db        # 实验元数据
├── mlflow.db        # MLflow 追踪日志
├── demos/           # 专家演示数据文件
├── custom_rewards.json  # 自定义奖励代码
└── recordings/      # 策略回放视频
```

**备份**只需备份整个 `data/` 目录。

### 10.5 GPU 加速

```bash
# .env
RL_LAB_DEVICE=cuda
```

Docker Compose 中如需 GPU 访问，取消 `docker-compose.yml` 中 backend 服务的 `deploy.resources.reservations.devices` 注释（需要 nvidia-docker）。

### 10.6 速率限制

写操作（POST/PUT/DELETE/PATCH）每 IP 默认限制 30 次/分钟。超出后返回 HTTP 429，`Retry-After` 头部指示何时可重试。

调整方式：
```bash
# .env
RL_LAB_RATE_LIMIT=60/minute
```

---

## 11. 常见问题 (FAQ)

### Q1: 为什么 MountainCar 用 R0_sparse 学不会？

稀疏奖励（Sparse）只在到达终点时给 +1 奖励。MountainCar 需要先往左开积累势能再往右，但 Sparse 奖励下 agent 没有信号引导，探索不到目标区域。这是教学设计的核心——展示无 shaping 时的训练困难。改用 R1_dense 或 R2_pbrs 即可学会。

### Q2: R4_misleading 的训练曲线为什么很高但实际表现很差？

Misleading 奖励故意引导 agent 刷分——例如奖励速度绝对值。Agent 很快学会"疯狂晃动"或"高速飞行"来最大化奖励，但从不完成任务。这是 reward hacking 的经典范例。观看回放视频可以直观看到 agent 的"作弊"行为。

### Q3: BC 需要设置奖励函数吗？

不需要。Behavioral Cloning 直接从专家演示的 (状态, 动作) 数据中学习，不需要奖励信号。新建 BC 实验时，奖励选择区会自动隐藏。

### Q4: HPO 优化和普通训练有什么区别？

普通训练：你指定超参 → 按指定种子运行每个奖励函数 → 得到 N 个 Run。

HPO：你指定搜索空间 → Optuna 自动尝试不同超参组合 → 每个 Trial 都是一个 Run → 推荐最优组合。

HPO 适合不确定用什么超参时进行探索，普通训练适合已知参数后进行复现或对比。

### Q5: 如何复制/克隆一个实验？

在实验详情页右上角点击 "Clone & Re-run" → 自动跳转新建页面并预填环境、算法。超参和奖励需要手动重新配置。

### Q6: 为什么我的自定义奖励提交后报错？

常见原因：
1. 语法错误——检查 Python 代码，确保缩进正确
2. 导入禁用模块——只允许 `gymnasium`、`numpy`、`math`
3. 函数签名不正确——必须为 `def reward_fn(obs, reward, terminated, truncated):`

### Q7: 速率限制返回 429 错误怎么办？

等待 `Retry-After` 头部指定的秒数后重试。GET 请求（读取数据）不受限制。如果频繁遇到，可调整 `RL_LAB_RATE_LIMIT` 配置。

### Q8: 数据存储在哪里？如何备份？

所有数据在项目根目录的 `data/` 文件夹下。备份文件夹即可。详细结构见 [10.4 节](#104-数据持久化)。

### Q9: 能不能多人同时使用？

可以。每个用户注册独立账号，实验数据完全隔离。所有资源的查询和修改都限定在当前用户范围内。

### Q10: 如何更新到最新版本？

```bash
git pull
docker compose down
docker compose up -d --build
```

数据库迁移会在后端启动时自动执行（幂等）。

---

## 12. 附录

### 12.1 内置奖励函数对照表

| 环境 | R0_sparse | R1_dense | R2_pbrs (Φ) | R4_misleading |
|------|-----------|----------|-------------|---------------|
| MountainCar | `1.0 if arrived else 0.0` | `position + 1.2` | `pos + 0.5×v²` | `abs(velocity)` |
| CartPole | `1.0 if not done else 0.0` | `position + 1.2` | `pos + 0.5×v²` | `abs(velocity)` |
| LunarLander | `1.0 if landed else 0.0` | `altitude` | `alt + 0.3×(1−|θ|)` | `abs(vx) + abs(vy)` |
| Acrobot | `1.0 if reached else 0.0` | tip height formula | tip height | `abs(ω₁) + abs(ω₂)` |
| Pendulum | `1.0 if upright else 0.0` | `cos(θ)` | `cos(θ) − 0.5×θ̇²` | `abs(θ̇)` |

> R3_curiosity_rnd 在所有环境中使用相同机制：外部稀疏奖励 + RND 内在动机。

### 12.2 API 端点速查

| 方法 | 路径 | 说明 | 限速 |
|------|------|------|------|
| POST | `/api/v1/auth/register` | 注册 | 是 |
| POST | `/api/v1/auth/login` | 登录 | 是 |
| GET | `/api/v1/auth/me` | 当前用户信息 | 否 |
| GET | `/api/v1/experiments` | 实验列表 | 否 |
| POST | `/api/v1/experiments` | 创建实验 | 是 |
| GET | `/api/v1/experiments/{id}` | 实验详情 | 否 |
| GET | `/api/v1/experiments/{id}/optimization` | HPO 结果 | 否 |
| POST | `/api/v1/experiments/{id}/pareto/recommend` | Pareto 推荐 | 是 |
| GET | `/api/v1/runs/{id}/stream` | SSE 学习曲线 | 否 |
| DELETE | `/api/v1/runs/{id}` | 取消 Run | 是 |
| GET | `/api/v1/rewards` | 奖励列表 | 否 |
| POST | `/api/v1/rewards` | 创建自定义奖励 | 是 |
| DELETE | `/api/v1/rewards/{id}` | 删除自定义奖励 | 是 |
| GET | `/api/v1/demos` | Demo 列表 | 否 |
| POST | `/api/v1/demos` | 创建 Demo | 是 |
| DELETE | `/api/v1/demos/{id}` | 删除 Demo | 是 |

### 12.3 默认超参（每个算法）

**DQN**：
| 参数 | 默认值 |
|------|--------|
| `learning_rate` | 1e-4 |
| `buffer_size` | 100,000 |
| `learning_starts` | 1,000 |
| `batch_size` | 32 |
| `tau` | 1.0 |
| `gamma` | 0.99 |
| `exploration_fraction` | 0.1 |
| `exploration_initial_eps` | 1.0 |
| `exploration_final_eps` | 0.02 |

**SAC**：
| 参数 | 默认值 |
|------|--------|
| `learning_rate` | 3e-4 |
| `buffer_size` | 100,000 |
| `learning_starts` | 100 |
| `batch_size` | 256 |
| `tau` | 0.005 |
| `gamma` | 0.99 |
| `ent_coef` | auto |
| `use_sde` | false |

**BC**：
| 参数 | 默认值 |
|------|--------|
| `batch_size` | 32 |
| `l2_weight` | 1e-4 |
| `optimizer_kwargs.lr` | 1e-3 |

### 12.4 版本历史

| 版本 | 主题 |
|------|------|
| v0.1–v0.5 | 训练链路、多算法、BC 克隆 |
| v0.6 | 自定义奖励编辑器 |
| v0.7 | 筛选/分页/批量对比 |
| v0.8 | 连续环境 + SAC |
| v0.9 | 多奖励 Optuna HPO |
| v1.0 | Docker + CI + JWT 认证 |
| v1.1 | NSGA-II 多目标优化 |
| v1.2 | 交互式 Pareto 权重推荐 |
| v1.3 | 速率限制 + 多用户 + 前端优化 |

### 12.5 参考资源

- [Ng, Harada & Russell (ICML 1999) — Policy Invariance Under Reward Transformations](https://ai.stanford.edu/~ang/papers/shaping-icml99.pdf)
- [Burda et al. (ICLR 2019) — Exploration by Random Network Distillation](https://arxiv.org/abs/1810.12894)
- [Optuna Documentation](https://optuna.readthedocs.io/)
- [Stable-Baselines3 Documentation](https://stable-baselines3.readthedocs.io/)
- [Gymnasium Documentation](https://gymnasium.farama.org/)

---

> 本手册随 RL-Reward-Lab 持续更新。如有疑问或建议，请通过 GitHub Issues 反馈。
