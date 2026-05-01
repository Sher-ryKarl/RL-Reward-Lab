# 需求澄清记录

> 本文档记录所有与用户的问答澄清过程。每次需求模糊点必须在此闭环。

---

## 已澄清

### Q1: 技术栈选型是否全盘采纳 `技术栈选型.md`？（2026-05-01）

**回答**: 全盘采纳。React+TS+Vite / FastAPI+Uvicorn / SB3 四件套 / MLflow+SQLite / SSE / Optuna(v0.2) / uv 包管理。

### Q2: v0.1 锁定 MountainCar-v0 + CartPole-v1 + PPO + 5 Reward 变体？（2026-05-01）

**回答**: 认可。两个环境、PPO 唯一算法、R0_sparse / R1_dense / R2_pbrs_potential / R3_curiosity_rnd / R4_misleading 五种奖励变体。

### Q3: 前端是否按 React 方案推进？（2026-05-01）

**回答**: 以 React 18 + TypeScript 5 + Vite 方案推进。

### Q4: Phase 1 从后端核心开始？（2026-05-01）

**回答**: 同意。后端是所有功能的依赖基础，先从后端搭建。

### Q5: 目录结构是否确认？（2026-05-01）

**回答**: 符合预期，前后端分离、文档独立、测试齐全。

---

## 待澄清

（暂无）
