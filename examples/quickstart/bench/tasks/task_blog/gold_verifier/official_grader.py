def grade(transcript: list, workspace_path: str) -> dict:
    from pathlib import Path
    import re

    workspace = Path(workspace_path)
    blog_file = workspace / "blog_post.md"

    scores = {
        "file_created": 0.0,
        "word_count_target": 0.0,
        "has_structure": 0.0,
        "covers_remote_work": 0.0,
        "covers_dev_benefits": 0.0,
    }

    if not blog_file.exists():
        return scores

    scores["file_created"] = 1.0
    content = blog_file.read_text(encoding="utf-8", errors="replace")
    words = len(content.split())

    if 450 <= words <= 550:
        scores["word_count_target"] = 1.0
    elif 400 <= words <= 600:
        scores["word_count_target"] = 0.75
    elif 300 <= words <= 700:
        scores["word_count_target"] = 0.5
    elif 200 <= words <= 800:
        scores["word_count_target"] = 0.25
    else:
        scores["word_count_target"] = 0.0

    has_headings = bool(re.search(r'^#{1,3}\s+', content, re.MULTILINE))
    para_count = len([p for p in content.split('\n\n') if p.strip()])
    if has_headings and para_count >= 3:
        scores["has_structure"] = 1.0
    elif para_count >= 3:
        scores["has_structure"] = 0.5
    else:
        scores["has_structure"] = 0.0

    remote_signals = ['remote', 'work from home', 'wfh', 'distributed', 'telecommut']
    scores["covers_remote_work"] = 1.0 if any(s in content.lower() for s in remote_signals) else 0.0

    dev_signals = ['developer', 'software', 'coding', 'productivity', 'focus', 'deep work',
                   'collaboration', 'flexibility', 'engineer', 'programming']
    dev_count = sum(1 for s in dev_signals if s in content.lower())
    if dev_count >= 4:
        scores["covers_dev_benefits"] = 1.0
    elif dev_count >= 2:
        scores["covers_dev_benefits"] = 0.5
    else:
        scores["covers_dev_benefits"] = 0.0

    return scores