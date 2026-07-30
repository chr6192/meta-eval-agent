---
id: task_video_transcript_extraction
name: Video Transcript Extraction and Summary
category: coding
subcategory: Video Analysis
timeout_seconds: 300
input_modality: text-only
external_dependency: yt-dlp
workspace_files: []
labels:
  complexity: L3
  environment: open
  modality:
    type: text
    channels: []
  capabilities:
  - Tool_Use
  - Planning
  scenario: Content_Creation/Video_Audio
---

## Prompt

Get the transcript from this YouTube video and create a structured summary:

**Video:** https://www.youtube.com/watch?v=dQw4w9WgXcQ

Extract or download the transcript/subtitles from this video. Then create:

1. **Metadata**: Title, channel, duration, upload date
2. **Full transcript**: Save the complete transcript to `transcript.txt`
3. **Summary**: A 200-300 word summary of the video's content saved to `video_summary.md`
4. **Key points**: A bullet-point list of the main topics or takeaways (in the summary file)
5. **Timestamps**: Notable moments with their timestamps (in the summary file)

Save the full transcript to `transcript.txt` and the structured summary to `video_summary.md`.


## Additional Notes

- This video URL (Rick Astley - Never Gonna Give You Up) was chosen because it's one of the most well-known YouTube videos, ensuring long-term availability and having subtitles/transcripts available.
- The task tests the agent's ability to interact with external services (YouTube) and process media content.
- Agents may use various tools: yt-dlp, web fetch, YouTube APIs, or browser automation. All approaches are valid.
- The summary quality matters more than the extraction method — agents that can only get partial transcripts but write excellent summaries should still score well overall.
