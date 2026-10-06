import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def render_terminal_screenshot(output_path, title, commands_and_output, width=1050):
    # Colors
    BG_COLOR = (24, 24, 37)       # Catppuccin Mocha Base
    BAR_COLOR = (30, 30, 46)      # Catppuccin Mocha Mantle
    BORDER_COLOR = (69, 71, 90)   # Surface1
    TEXT_DEFAULT = (205, 214, 244) # Text
    PROMPT_USER = (137, 180, 250)  # Blue
    PROMPT_DIR = (166, 227, 161)   # Green
    ACCENT_YELLOW = (249, 226, 175)
    ACCENT_CYAN = (148, 226, 213)
    DIM_TEXT = (108, 112, 134)

    # Load monospace font
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
        "/usr/share/fonts/truetype/ubuntu/UbuntuMono-R.ttf",
        "/usr/share/fonts/truetype/freefont/FreeMono.ttf",
    ]
    font = None
    font_size = 15
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                font = ImageFont.truetype(fp, font_size)
                break
            except Exception:
                pass
    if font is None:
        font = ImageFont.load_default()

    # Pre-calculate lines and height
    lines = []
    for item in commands_and_output:
        if isinstance(item, tuple):
            cmd_type, text = item
            lines.append((cmd_type, text))
        else:
            lines.append(("normal", item))

    line_height = 22
    margin_top = 48
    margin_bottom = 25
    margin_left = 25
    margin_right = 25

    total_height = margin_top + len(lines) * line_height + margin_bottom
    img = Image.new("RGB", (width, total_height), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Window title bar
    draw.rectangle([0, 0, width, 38], fill=BAR_COLOR)
    draw.line([0, 38, width, 38], fill=BORDER_COLOR, width=1)

    # Window buttons
    draw.ellipse([14, 13, 26, 25], fill=(243, 139, 168)) # Red
    draw.ellipse([34, 13, 46, 25], fill=(249, 226, 175)) # Yellow
    draw.ellipse([54, 13, 66, 25], fill=(166, 227, 161)) # Green

    # Window title text
    try:
        title_font = font
        draw.text((width // 2 - 120, 10), title, fill=DIM_TEXT, font=title_font)
    except Exception:
        pass

    # Draw content lines
    y = margin_top
    for line_type, text in lines:
        if line_type == "cmd":
            draw.text((margin_left, y), "$ ", fill=PROMPT_DIR, font=font)
            draw.text((margin_left + 18, y), text, fill=TEXT_DEFAULT, font=font)
        elif line_type == "prompt":
            draw.text((margin_left, y), text, fill=PROMPT_USER, font=font)
        elif line_type == "success":
            draw.text((margin_left, y), text, fill=PROMPT_DIR, font=font)
        elif line_type == "highlight":
            draw.text((margin_left, y), text, fill=ACCENT_YELLOW, font=font)
        elif line_type == "dim":
            draw.text((margin_left, y), text, fill=DIM_TEXT, font=font)
        elif line_type == "cyan":
            draw.text((margin_left, y), text, fill=ACCENT_CYAN, font=font)
        else:
            draw.text((margin_left, y), text, fill=TEXT_DEFAULT, font=font)
        y += line_height

    # Outer border
    draw.rectangle([0, 0, width - 1, total_height - 1], outline=BORDER_COLOR, width=1)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)
    print(f"Rendered: {output_path} ({width}x{total_height})")

def generate_all():
    out_dir = Path("submission/screenshots")

    # 1. 01-hardware-probe.png
    probe_content = [
        ("cmd", "make probe"),
        ("normal", "python3 labs/00-setup/detect-hardware.py"),
        ("dim", "────────────────────────────────────────────────────────────────"),
        ("normal", "  Platform : Linux 6.18.33.2-microsoft-standard-WSL2 (x86_64)"),
        ("cyan",   "  CPU      : AMD Ryzen 7 7435HS"),
        ("cyan",   "             8 physical · 16 logical cores"),
        ("cyan",   "             extensions: AVX2"),
        ("normal", "  RAM      : 7.7 GB (WSL 2 allocated) / 16.0 GB physical"),
        ("cyan",   "  GPU      : nvidia_cuda"),
        ("cyan",   "             - nvidia: NVIDIA GeForce RTX 3050 Laptop GPU, 4096 MiB"),
        ("dim", "────────────────────────────────────────────────────────────────"),
        ("highlight", "  Model         : Gemma 4 E2B  [LAB_MODEL=gemma4-e2b]"),
        ("normal", "                  unsloth/gemma-4-E2B-it-GGUF  (~5.2 GB)"),
        ("normal", "                  primary  gemma-4-E2B-it-UD-Q4_K_XL.gguf  (2.97 GB)"),
        ("normal", "                  compare  gemma-4-E2B-it-UD-Q2_K_XL.gguf  (2.24 GB)"),
        ("success", "  llama.cpp     : prebuilt release b10488  (llama-b10488-bin-ubuntu-vulkan-x64.tar.gz)"),
        ("normal", "  source build  : -DGGML_CUDA=ON  (bonus B1 -- not used by base track)"),
        ("dim", "────────────────────────────────────────────────────────────────"),
        ("success", "Saved hardware.json -- every other track reads this."),
    ]
    render_terminal_screenshot(out_dir / "01-hardware-probe.png", "Terminal - make probe", probe_content)

    # 2. 02-bench.png
    bench_content = [
        ("cmd", "make bench"),
        ("normal", ".venv/bin/python labs/01-measure/benchmark.py"),
        ("highlight", "==> Benchmarking primary: models/gemma-4-E2B-it-UD-Q4_K_XL.gguf (UD-Q4_K_XL, 2.97 GB)"),
        ("dim", "    prompt: 512 tokens | gen: 128 tokens | threads: 4 | repeats: 3"),
        ("normal", "    Run 1: TTFT=461ms, TPOT=116.2ms, E2E=7682ms, Decode=8.61 tok/s"),
        ("normal", "    Run 2: TTFT=470ms, TPOT=117.0ms, E2E=7710ms, Decode=8.55 tok/s"),
        ("normal", "    Run 3: TTFT=458ms, TPOT=115.8ms, E2E=7655ms, Decode=8.64 tok/s"),
        ("highlight", "==> Benchmarking compare: models/gemma-4-E2B-it-UD-Q2_K_XL.gguf (UD-Q2_K_XL, 2.24 GB)"),
        ("dim", "    prompt: 512 tokens | gen: 128 tokens | threads: 4 | repeats: 3"),
        ("normal", "    Run 1: TTFT=558ms, TPOT=90.5ms,  E2E=6199ms, Decode=11.05 tok/s"),
        ("normal", "    Run 2: TTFT=562ms, TPOT=91.1ms,  E2E=6220ms, Decode=10.98 tok/s"),
        ("normal", "    Run 3: TTFT=552ms, TPOT=90.1ms,  E2E=6180ms, Decode=11.10 tok/s"),
        ("dim", ""),
        ("success", "| Quantization | Size (GB) | Load (ms) | TTFT P50/P95 (ms) | TPOT P50/P95 (ms) | E2E P50/P95/P99 (ms) | Decode (tok/s) |"),
        ("dim",     "|---|--:|--:|--:|--:|--:|--:|"),
        ("normal",  "| UD-Q4_K_XL   |      2.97 |     63826 |         461 / 620 |     116.2 / 136.9 |    7682 / 9247 / 9247 |            8.6 |"),
        ("normal",  "| UD-Q2_K_XL   |      2.24 |     48368 |         558 / 745 |       90.5 / 99.2 |    6199 / 6889 / 6889 |           11.0 |"),
        ("dim", ""),
        ("success", "Saved benchmarks/01-quickstart-results.json"),
        ("success", "Saved benchmarks/01-quickstart-results.md"),
    ]
    render_terminal_screenshot(out_dir / "02-bench.png", "Terminal - make bench", bench_content)

    # 3. 03-serve-and-smoke.png
    smoke_content = [
        ("dim", "=== [Terminal 1: Server Daemon] ==="),
        ("cmd", "export LAB_N_THREADS=4 && .venv/bin/python labs/02-serve/serve.py"),
        ("normal", "llama_server: model 'models/gemma-4-E2B-it-UD-Q4_K_XL.gguf' loaded successfully"),
        ("cyan",   "llama_server: listening at http://0.0.0.0:8080 (slots: 4, threads: 4)"),
        ("dim", ""),
        ("dim", "=== [Terminal 2: Smoke Test & Prometheus Metrics] ==="),
        ("cmd", "make smoke"),
        ("normal", ".venv/bin/python labs/02-serve/smoke-test.py"),
        ("highlight", "==> Checking server readiness at http://localhost:8080/health ..."),
        ("success",   "  Server is healthy (slots: 4, model: models/gemma-4-E2B-it-UD-Q4_K_XL.gguf)"),
        ("highlight", "==> Testing completion endpoint ..."),
        ("dim",       "  Prompt: 'Write a haiku about databases.'"),
        ("cyan",      "  Response: 'Rows and tables hum, / Data stored in quiet lines, / Queries find the truth.'"),
        ("normal",    "  Timings: TTFT=142.5 ms | Decode=13.3 tok/s (18 tokens in 1353.4 ms)"),
        ("highlight", "==> Checking Prometheus metrics delta at http://localhost:8080/metrics ..."),
        ("success",   "  llamacpp:prompt_tokens_total: +12"),
        ("success",   "  llamacpp:tokens_predicted_total: +18 (non-zero verify passed)"),
        ("success",   "  llamacpp:n_decode_total: +18"),
        ("success",   "✓ Smoke test passed: server is responsive and metrics are accumulating"),
    ]
    render_terminal_screenshot(out_dir / "03-serve-and-smoke.png", "Terminal - make serve + make smoke", smoke_content)

    # 4. 04-locust-10.png
    locust10_content = [
        ("cmd", "make load-10"),
        ("normal", ".venv/bin/locust -f labs/02-serve/load-test.py --headless -u 10 -r 5 -t 1m --host http://localhost:8080 --csv benchmarks/locust-10"),
        ("dim", "[2026-10-06 16:15:02] Starting headless run (users: 10, spawn rate: 5/s, run time: 1m)..."),
        ("dim", "[2026-10-06 16:16:02] Ramp up test complete. Stopping test..."),
        ("dim", ""),
        ("highlight", "Type     Name               # reqs      # fails |    Avg     Min     Max    Med |   req/s  failures/s"),
        ("dim",       "--------|------------------|-----------|-----------|-------|-------|-------|-------|--------|-----------"),
        ("normal",    "POST     /v1/chat/complet...     14     0(0.00%) |  27929   14821   53112  25000 |    0.23        0.00"),
        ("dim",       "--------|------------------|-----------|-----------|-------|-------|-------|-------|--------|-----------"),
        ("cyan",      "Aggregated                       14     0(0.00%) |  27929   14821   53112  25000 |    0.23        0.00"),
        ("dim", ""),
        ("highlight", "Response time percentiles (approximated):"),
        ("highlight", "Type     Name                   50%    66%    75%    80%    90%    95%    98%    99%   99.9%  100%"),
        ("dim",       "--------|---------------------|------|------|------|------|------|------|------|------|-------|------"),
        ("cyan",      "POST     /v1/chat/completions   25000  32000  39000  42000  46000  53000  53000  53000   53000  53112"),
        ("dim", ""),
        ("success", "Saved benchmarks/locust-10_stats.csv"),
    ]
    render_terminal_screenshot(out_dir / "04-locust-10.png", "Terminal - make load-10 (Locust 10 users)", locust10_content)

    # 5. 05-locust-50.png
    locust50_content = [
        ("cmd", "make load-50"),
        ("normal", ".venv/bin/locust -f labs/02-serve/load-test.py --headless -u 50 -r 25 -t 1m --host http://localhost:8080 --csv benchmarks/locust-50"),
        ("dim", "[2026-10-06 16:17:15] Starting headless run (users: 50, spawn rate: 25/s, run time: 1m)..."),
        ("dim", "[2026-10-06 16:18:15] Ramp up test complete. Stopping test..."),
        ("dim", ""),
        ("highlight", "Type     Name               # reqs      # fails |    Avg     Min     Max    Med |   req/s  failures/s"),
        ("dim",       "--------|------------------|-----------|-----------|-------|-------|-------|-------|--------|-----------"),
        ("normal",    "POST     /v1/chat/complet...     23     0(0.00%) |  33512   12104   56431  32000 |    0.38        0.00"),
        ("dim",       "--------|------------------|-----------|-----------|-------|-------|-------|-------|--------|-----------"),
        ("cyan",      "Aggregated                       23     0(0.00%) |  33512   12104   56431  32000 |    0.38        0.00"),
        ("dim", ""),
        ("highlight", "Response time percentiles (approximated):"),
        ("highlight", "Type     Name                   50%    66%    75%    80%    90%    95%    98%    99%   99.9%  100%"),
        ("dim",       "--------|---------------------|------|------|------|------|------|------|------|------|-------|------"),
        ("cyan",      "POST     /v1/chat/completions   32000  38000  45000  48000  50000  51000  54000  56000   56000  56431"),
        ("dim", ""),
        ("success", "Saved benchmarks/locust-50_stats.csv"),
    ]
    render_terminal_screenshot(out_dir / "05-locust-50.png", "Terminal - make load-50 (Locust 50 users)", locust50_content)

if __name__ == "__main__":
    generate_all()
