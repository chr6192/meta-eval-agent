# Rubric: Video Transcript Extraction and Summary

Task: extract a YouTube video transcript into `transcript.txt` and produce a structured `video_summary.md` with metadata, 200–300 word summary, key points, and timestamps.

Scoring: **PASS** requires all must-have criteria ≥ 0.99. Agentic-judge dimensions contribute to `score` only.

| Criterion (breakdown key) | Must-have | Weight in score | Description |
|---|---|---|---|
| `transcript_file_exists` | Yes | — | `transcript.txt` exists in workspace and is non-empty. |
| `transcript_substantive` | Yes | — | Transcript has ≥400 characters, ≥5 timestamp markers, and ≥8 lyric/content lines (not a stub). |
| `summary_file_exists` | Yes | — | `video_summary.md` exists and has substantive content (>50 chars). |
| `metadata_four_fields` | Yes | — | Summary includes **title**, **channel**, **duration**, and **upload date** with values. |
| `summary_word_count_200_300` | Yes | — | Summary body is 200–300 words inclusive. |
| `key_points_bullets` | Yes | — | At least 3 bullet key points / takeaways. |
| `timestamps_notable_moments` | Yes | — | At least 3 timestamped notable moments. |
| `transcript_summary_alignment` | Yes | — | ≥10 shared content words (length ≥4) between transcript lyrics and summary, with overlap ratio ≥0.2. |
| `agentic_judge_summary_content_quality` | No | 50% | Summary is coherent, on-topic, not keyword stuffing (0–1). |
| `agentic_judge_summary_grounded_in_transcript` | No | 50% | Main summary claims are supported by `transcript.txt` (0–1). |

## Partial credit (deterministic, cannot pass gate alone)

- `transcript_substantive`: 0.5 if partial transcript (200+ chars, 3+ timestamps).
- `metadata_four_fields`: 0.5 if 3 of 4 metadata fields present.
- `summary_word_count_200_300`: 0.5 if 150–199 or 301–350 words.
- `key_points_bullets` / `timestamps_notable_moments` / `transcript_summary_alignment`: 0.5 for partial fulfillment.

## PASS / FAIL

- **PASS**: all must-have keys ≥ 0.99.
- **FAIL**: any must-have < 0.99. Agentic-judge scores still computed for ranking among failures.
