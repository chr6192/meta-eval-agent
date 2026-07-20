import pytest
from benchmark.tools import bench_load, stage, paths


@pytest.fixture(scope="module")
def staged(tmp_path_factory):
    if not paths.SRC_BENCH.exists():
        pytest.skip("原始数据缺失")
    out = tmp_path_factory.mktemp("bench")
    ids = stage.discover_task_ids()[:3]
    stage.stage_all(ids, {"train": ids, "test": []}, out)
    return out, ids


def test_iter_split_tasks(staged):
    out, ids = staged
    got = list(bench_load.iter_split_tasks(out, "train"))
    assert set(got) == set(ids)


def test_load_task_gold(staged):
    out, ids = staged
    g = bench_load.load_task_gold(out, ids[0])
    assert "candidates" in g.labels
    assert isinstance(g.reachable_weight, float)
    for c in g.labels["candidates"].values():
        assert isinstance(c["passed"], bool)


def test_load_candidate_io(staged):
    out, ids = staged
    g = bench_load.load_task_gold(out, ids[0])
    key = next(iter(g.labels["candidates"]))
    io = bench_load.load_candidate_io(out, ids[0], key)
    assert io.workspace_path.is_dir()
    assert isinstance(io.transcript, list)
