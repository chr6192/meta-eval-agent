from benchmark.tools import metrics


def _obs(task, cand, dp, gp, ds=0.0, gs=0.0):
    return {"task_id": task, "cand": cand, "derived_passed": dp,
            "gold_passed": gp, "derived_score": ds, "gold_score": gs}


def test_d1_outcome_micro_macro():
    obs = [_obs("t1", "a", True, True), _obs("t1", "b", False, True),
           _obs("t2", "a", False, False), _obs("t2", "b", True, True)]
    d1 = metrics.d1_outcome(obs)
    assert d1["micro"] == 0.75
    assert abs(d1["macro"] - 0.75) < 1e-9
    assert d1["n"] == 4


def test_d1_prime_false_pass_fail():
    obs = [_obs("t1", "a", True, False),
           _obs("t1", "b", False, True),
           _obs("t2", "a", True, True)]
    d = metrics.d1_prime(obs)
    assert d["false_pass"] == 1
    assert d["false_fail"] == 1


def test_d1_skips_none():
    obs = [_obs("t1", "a", None, True), _obs("t1", "b", True, True)]
    d1 = metrics.d1_outcome(obs)
    assert d1["n"] == 1
    assert d1["micro"] == 1.0


def test_d1_empty_and_all_none():
    assert metrics.d1_outcome([])["micro"] is None
    assert metrics.d1_outcome([])["n"] == 0
    assert metrics.d1_prime([]) == {"false_pass": 0, "false_fail": 0, "n": 0}
    # 全 None 过滤后等价于空
    obs = [_obs("t1", "a", None, None)]
    assert metrics.d1_outcome(obs)["n"] == 0


def test_d2_mae():
    obs = [_obs("t1", "a", True, True, ds=0.8, gs=1.0),
           _obs("t1", "b", False, False, ds=0.2, gs=0.0)]
    d2 = metrics.d2_score(obs)
    assert abs(d2["mae"] - 0.2) < 1e-9


def test_d2_spearman_perfect_monotonic():
    obs = [_obs("t", str(i), True, True, ds=i * 0.1, gs=i * 2.0) for i in range(5)]
    d2 = metrics.d2_score(obs)
    assert abs(d2["spearman"] - 1.0) < 1e-9


def test_d2_spearman_inverse():
    obs = [_obs("t", str(i), True, True, ds=i, gs=-i) for i in range(5)]
    d2 = metrics.d2_score(obs)
    assert abs(d2["spearman"] - (-1.0)) < 1e-9


def test_d2_single_pair_spearman_none():
    obs = [_obs("t", "a", True, True, ds=0.5, gs=0.9)]
    d2 = metrics.d2_score(obs)
    assert d2["n"] == 1
    assert abs(d2["mae"] - 0.4) < 1e-9
    assert d2["spearman"] is None        # n<2 → 不可算


def test_d2_all_tie_derived_spearman_none():
    obs = [_obs("t", "a", True, True, ds=0.5, gs=0.1),
           _obs("t", "b", True, True, ds=0.5, gs=0.9)]
    d2 = metrics.d2_score(obs)
    assert d2["spearman"] is None        # derived 全并列 → 零方差
    assert d2["n"] == 2


def test_d3_pairwise_perfect():
    obs = [_obs("t1", "a", True, True, ds=0.9, gs=0.9),
           _obs("t1", "b", True, True, ds=0.5, gs=0.6),
           _obs("t1", "c", False, False, ds=0.1, gs=0.2)]
    d3 = metrics.d3_rank(obs)
    assert d3["pairwise_acc"] == 1.0


def test_d3_pairwise_fully_inverted():
    obs = [_obs("t1", "a", True, True, ds=0.1, gs=0.9),
           _obs("t1", "b", True, True, ds=0.5, gs=0.6),
           _obs("t1", "c", False, False, ds=0.9, gs=0.2)]
    d3 = metrics.d3_rank(obs)
    assert d3["pairwise_acc"] == 0.0
    assert d3["kendall_tau"] == -1.0       # 全反序 → τ=-1
    assert d3["n_pairs"] == 3


def test_d3_skips_single_candidate_tasks():
    obs = [_obs("solo", "a", True, True, ds=0.5, gs=0.5)]
    d3 = metrics.d3_rank(obs)
    assert d3["n_pairs"] == 0
    assert d3["pairwise_acc"] is None


def test_d3_partial_agreement():
    # 3 candidate：gold a>b>c；derived a>c>b → 对 (a,b)✓ (a,c)✓ (b,c)✗ → 2/3
    obs = [_obs("t1", "a", True, True, ds=0.9, gs=0.9),
           _obs("t1", "b", True, True, ds=0.2, gs=0.6),
           _obs("t1", "c", False, False, ds=0.5, gs=0.2)]
    d3 = metrics.d3_rank(obs)
    assert d3["n_pairs"] == 3
    assert abs(d3["pairwise_acc"] - 2 / 3) < 1e-9


def test_d3_multi_task_aggregates():
    # 两个 task 各 2 candidate，pairs 只在 task 内成对，n_pairs 求和
    obs = [_obs("t1", "a", True, True, ds=0.9, gs=0.9), _obs("t1", "b", True, True, ds=0.1, gs=0.1),
           _obs("t2", "a", True, True, ds=0.1, gs=0.9), _obs("t2", "b", True, True, ds=0.9, gs=0.1)]
    d3 = metrics.d3_rank(obs)
    assert d3["n_pairs"] == 2              # 每 task 1 对，跨 task 不成对
    assert d3["pairwise_acc"] == 0.5       # t1 对、t2 错


def test_reachable_weighted_macro():
    obs = [_obs("t1", "a", True, True), _obs("t2", "a", True, False)]
    rw = {"t1": 1.0, "t2": 0.0}
    out = metrics.reachable_weighted_macro(obs, rw)
    assert abs(out["raw_macro"] - 0.5) < 1e-9
    assert abs(out["reachable_weighted_macro"] - 1.0) < 1e-9


def test_reachable_weighted_macro_all_zero_weight():
    obs = [_obs("t1", "a", True, False)]
    out = metrics.reachable_weighted_macro(obs, {"t1": 0.0})
    assert out["reachable_weighted_macro"] is None


def test_reachable_weighted_macro_fractional_weights():
    obs = [_obs("t1", "a", True, True),    # t1 acc = 1.0
           _obs("t2", "a", True, False)]   # t2 acc = 0.0
    rw = {"t1": 0.8, "t2": 0.2}
    out = metrics.reachable_weighted_macro(obs, rw)
    assert abs(out["raw_macro"] - 0.5) < 1e-9
    assert abs(out["reachable_weighted_macro"] - 0.8) < 1e-9   # (1.0*0.8 + 0.0*0.2)/1.0


def test_d1_score_threshold():
    # derived 全 True；gold_score: 1.0(>=0.99→True 一致) / 0.5(<0.99→False 不一致)
    obs = [_obs("t1", "a", True, True, gs=1.0), _obs("t1", "b", True, False, gs=0.5)]
    d = metrics.d1_score_threshold(obs, threshold=0.99)
    assert d["micro"] == 0.5            # a 一致(True==True), b 不一致(True!=False)
    assert d["threshold"] == 0.99
    assert d["n"] == 2


def test_d1_score_threshold_skips_none_derived():
    obs = [_obs("t1", "a", None, True, gs=1.0), _obs("t1", "b", True, True, gs=1.0)]
    d = metrics.d1_score_threshold(obs)
    assert d["n"] == 1                  # None derived 跳过
