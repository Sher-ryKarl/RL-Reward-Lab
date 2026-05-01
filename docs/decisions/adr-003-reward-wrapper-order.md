# ADR-003: Reward Wrapper Order in VecEnv

**状态**: 已采纳

**日期**: 2026-05-01

**背景**: SB3 的 `Monitor` wrapper 负责记录 episode 级别的 reward/长度统计到 `ep_info_buffer`，而 reward shaping wrapper 会修改 step 返回的 reward。两个 wrapper 的嵌套顺序直接影响 `ep_rew_mean` 记录的是原始任务奖励还是塑形后的奖励。

**决策**: 永远使用 `Monitor(RewardWrapper(env))`，即 Monitor 在最外层

**原理**:
```
正确: Monitor(PBRSWrapper(env))
  env.step() → (obs, r_extrinsic, ...)
  PBRSWrapper.step() → (obs, r_extrinsic + shaping, ..., info["reward_components"])
  Monitor.step() → log r_extrinsic to ep_info_buffer  ✓

错误: PBRSWrapper(Monitor(env))
  env.step() → ... → Monitor.step() → log r_shaped to ep_info_buffer
  PBRSWrapper.step() → add shaping to already-logged r_shaped
  ep_info_buffer 记录的是塑形后的值，不同奖励变体之间对比失真  ✗
```

**PBRS done 帧处理**:
done 时 shaping 设为 0，避免用下一幀的 observation 计算 Φ（"偷未来信息"）。

```python
if terminated or truncated:
    shaping = 0.0  # 保持策略不变性
else:
    shaping = gamma * Phi(s') - Phi(s)
```

**后果**:
- (+) 所有变体的 `ep_rew_mean` 曲线可跨变体直接对比（都记录的是原始任务奖励）
- (+) 前端 reward 分量分解图使用 info["reward_components"] 分别展示各分量
- (-) 新 contributor 容易出错，需要在代码审查中强调这一约定

**关联**: ADR-001 (tech stack), SB3 官方文档 `vec_envs.rst`
