# Evaluator 报告（split=demo）

- **覆盖率 coverage**: 可比 obs 48/48（1.0）；覆盖 task 6/6
- 观测数 n_obs: 48（可比 48）
- **D1 outcome**: micro=0.8541666666666666 macro=0.8541666666666666
- **D1 对照（gold score≥0.99）**: micro=0.8541666666666666（高于主口径=阈值效应；≤主口径=verifier 真错）
- **D1′ 误判**: false-pass=7 false-fail=0
- **D2 score**: MAE=0.34985218253968253 Spearman=0.5029372279626796
- **D3 排序**: pairwise=0.34579439252336447 Kendall=0.308411214953271（107 对）
- **可达性归一**: raw_macro=0.8541666666666666 reachable_weighted=0.8273809523809523