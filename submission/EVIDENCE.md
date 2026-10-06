# Measurement provenance

All replacement measurement evidence is from the local laptop's Ubuntu WSL2
environment. `hardware.json` is a new probe of that environment. WSL has 7.7 GiB
RAM available; the host's physical RAM is about 16 GB. Probe recommends the smaller
Qwen model, but the measured model remains the existing Gemma 4 E2B manifest.

The base rerun uses CPU inference (`LAB_N_GPU_LAYERS=0`), 8 threads, context 2048,
4 continuous-batching slots, reasoning off, and port 8090 rather than the lab's
default port 8080. Benchmark max output is 64 tokens, 10 prompts
per quantization, with warm-up discarded. Load runs are 60 seconds at 10 and 50
users; metrics samples overlap the 50-user run. The server is restarted before
50-user load and before the three-query pipeline to clear unfinished requests.
Tuning measures tg128 independently; its thread choice is not silently applied
to serving.

`submission/logs/*.txt` preserves actual command output, command line, and exit
status. `Captured at` headers are UTC; add 7 hours for local Vietnam/Bangkok time.
Locust's own log timestamps already use local UTC+7. `server.txt`
contains the actual launch command and listener messages. No API credentials are
needed for this lab. The five PNGs capture a browser viewer of the actual logs,
with that origin explicitly stated in each image; they do not impersonate a
terminal session. The old generated terminal mockups are replaced.

The Locust shutdown hook exports `_final_stats.csv`; after the process exits the
runner promotes this unchanged final snapshot to the standard `_stats.csv` file.
This avoids the periodic writer's last sample lagging the printed summary.

`scripts/sync_submission.py` copies measured tables and data-derived summaries
into Markdown and REFLECTION without changing raw JSON/CSV values. Mechanisms
such as cache contention and bandwidth saturation remain hypotheses, not
hardware-counter measurements. The pipeline uses toy retrieval; N16–N19 are
stubbed, and N20 HTTP serving is real. No bonus is claimed. A same-prompt answer
comparison is saved in `benchmarks/01-quality-comparison.json` and `logs/quality.txt`;
it is an illustrative check, not a general quality evaluation.

GitHub publication and pasting the repository URL into the LMS are separate
submission steps. Local verification does not establish either step.
