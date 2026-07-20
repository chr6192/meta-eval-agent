"""所有路径的单一真相源。其它模块只从这里取路径，不自己拼。"""
from pathlib import Path

# benchmark/tools/paths.py -> repo 根是 parents[2]
REPO_ROOT = Path(__file__).resolve().parents[2]

DATA_ROOT = REPO_ROOT / "origin_data"
SRC_BENCH = DATA_ROOT / "pawbench-v1.0"
SOURCE_BENCHMARK = "pawbench-v1.0"
TASKS_DIR = SRC_BENCH / "tasks"
ASSETS_DIR = SRC_BENCH / "assets"

# 候选矩阵：单 harness (qwenpaw) × 8 个 model，跑分都在同一 run 下
RUN_ID = "20260615_111519"
HARNESS = "qwenpaw"
MODELS = [
    "glm-5.1",
    "kimi-k2.6",
    "qwen3.6-27b",
    "qwen3.6-35b-a3b",
    "qwen3.6-max-preview",
    "qwen3.6-plus",
    "qwen3.7-max",
    "qwen3.7-plus",
]

# 每个 (harness, model, run) 的跑分根目录；key = {harness}__{model}
FRAMEWORK_BASES = {
    f"{HARNESS}__{model}": DATA_ROOT / RUN_ID / "pawbench" / model / HARNESS
    for model in MODELS
}

CANDIDATE_SPECS = [
    {"key": f"{HARNESS}__{model}", "harness": HARNESS, "model": model, "run_id": RUN_ID}
    for model in MODELS
]

# benchmark 产出根（split 视图的单一真相源在 BENCH_OUT/splits/）
BENCH_OUT = REPO_ROOT / "benchmark" / "verifier-author-bench-v1"

# GT/答案侧文件名隔离模式（宪法 C3 + C17）——**staging 侧**物理隔离用
# 调用方用 fnmatch / 逐段匹配（lib.is_gt_path）：把 GT 文件挡在考题层之外。
# "gt" 匹配名为 gt 的文件或目录，其余为 glob 模式。
GT_PATTERNS = ["gt", "optimal_*", "expected_*", "reference_*", "solution_*",
               "answer_*", "golden_*", "ground_truth*"]
