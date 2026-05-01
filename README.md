# RL-Reward-Lab

**强化学习奖励函数设计与自动化调参可视化平台**

一个面向 RL 研究的实验平台，专注于奖励函数设计、自动化超参搜索与多维可视化分析。

## 当前状态

- **阶段**: 初始化，项目骨架搭建中
- **版本**: 尚未发布

## 技术栈（v0.1）

| 层 | 选型 |
|---|---|
| 前端 | React 18 + TypeScript 5 + Vite + Apache ECharts 5 |
| 后端 | FastAPI 0.135+ + Uvicorn + Pydantic v2 |
| 训练 | Stable-Baselines3 2.3+ + sb3-contrib + RLeXplore + imitation |
| 实验追踪 | MLflow 3.7+ (SQLite backend) |
| 数据库 | SQLite → PostgreSQL (v0.4+) |
| 超参优化 | Optuna 4.x (v0.2 起) |

## 快速开始

> 待 v0.1 完成后补充。

## 文档

- [架构设计](docs/architecture.md)
- [开发日志](docs/progress_log.md)
- [需求澄清](docs/requirements_clarification.md)
- [技术决策](docs/decisions/)

## 许可证

MIT
