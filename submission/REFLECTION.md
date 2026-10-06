# Reflection — Day 20 Lab (Personal Report)

> **Đây là báo cáo cá nhân.** Số liệu của bạn **không** so sánh được với bạn cùng lớp
> — chỉ so **before vs after trên chính máy bạn**. Rubric chấm độ rõ ràng của setup,
> đo lường và **lập luận**, không chấm tốc độ tuyệt đối.
>
> `make verify` sẽ fail nếu còn placeholder chưa điền. Đó là cố ý.

**Họ Tên:** Nguyễn Duy Phong
**MSSV:** 2A202602834
**Cohort:** K4
**Ngày submit:** 2026-10-06

---

## 1. Hardware & runtime  *(rubric 1, 2 — 10 điểm)*

> Từ `make probe`. Paste output hoặc điền tay.

- **OS:** Ubuntu 24.04 LTS on Windows 11 (WSL 2)
- **CPU:** AMD Ryzen 7 7435HS
- **Cores:** 8 physical / 16 logical
- **CPU extensions:** AVX2
- **RAM:** 7.7 GB (WSL) / 16 GB physical
- **Accelerator:** NVIDIA GeForce RTX 3050 Laptop GPU (4096 MiB)
- **llama.cpp asset đã tải:** llama-b10488-bin-ubuntu-vulkan-x64.tar.gz
- **Model đã dùng:** Gemma 4 E2B (`LAB_MODEL=gemma4-e2b`)
- **Quantization:** UD-Q4_K_XL + UD-Q2_K_XL (từ `models/active.json`)

**Chạy ở đâu:** laptop của tôi
_(Nếu dùng cloud fallback: nói rõ vì sao — RAM < 8 GB, setup fail, v.v. Không mất điểm.)_

**Setup story** (≤ 80 chữ): điều gì cần thay đổi để lab chạy trên máy bạn? Có bước
nào fail rồi phải workaround không?

Do Smart App Control trên Windows 11 chặn nạp DLL của server (mã lỗi 4551), tôi chuyển sang chạy trực tiếp trong Ubuntu WSL 2 trên máy. Môi trường WSL nhận diện đầy đủ GPU RTX 3050 và chạy mượt mà không gặp rào cản code integrity.

---

## 2. Đo lường  *(rubric 3, 4, 5 — 20 điểm)*

> Paste bảng từ `benchmarks/01-quickstart-results.md` (`make bench` tự sinh).

| Quantization | Size (GB) | Load (ms) | TTFT P50/P95 (ms) | TPOT P50/P95 (ms) | E2E P50/P95/P99 (ms) | Decode (tok/s) |
|---|--:|--:|--:|--:|--:|--:|
| UD-Q4_K_XL | 2.97 | 63826 | 461 / 620 | 116.2 / 136.9 | 7682 / 9247 / 9247 | 8.6 |
| UD-Q2_K_XL | 2.24 | 48368 | 558 / 745 | 90.5 / 99.2 | 6199 / 6889 / 6889 | 11.0 |

**Quan sát** (≤ 60 chữ): 2-bit nhanh hơn bao nhiêu, và **có đáng không**? Bạn đã thử
hỏi cùng một câu trên cả hai (`make serve` vs `.venv/bin/python labs/02-serve/serve.py --compare`)
chưa? Chất lượng khác nhau thế nào?

2-bit decode nhanh hơn 1.28x (11.0 vs 8.6 tok/s), nạp nhanh hơn 24%. Tuy nhiên ở bài test ngữ nghĩa thực tế, 2-bit giảm độ chính xác rõ rệt; bản 4-bit đáng dùng hơn nhiều cho tương tác thực tế.

---

## 3. Serving under load  *(rubric 8, 9, 10 — 20 điểm)*

> Từ `benchmarks/02-server-results.md` (`make load-report`).

| Users | RPS | P50 (ms) | P95 (ms) | P99 (ms) | Eff. concurrency | Failures |
|--:|--:|--:|--:|--:|--:|--:|
| 10 | 0.23 | 25000 | 53000 | 53000 | 6.7 | 0.0% |
| 50 | 0.38 | 32000 | 51000 | 56000 | 11.9 | 0.0% |

- **Offered load tăng 5×, throughput thực tăng:** 1.60×
- **P95 tăng:** 0.96×
- **Effective concurrency ở 50 users:** 11.9 so với `--parallel` = 4 slots

**Peak `llamacpp:n_busy_slots_per_decode`** (từ `make metrics` khi `make load-50` đang
chạy): 3.84 / 4 slots

**Saturation reading** (≤ 80 chữ): server của bạn bão hoà ở đâu, và **bằng chứng nào**
thuyết phục bạn? Nếu P95 tăng nhanh hơn RPS thì phần latency thêm đó là queue time hay
compute time — bạn biết bằng cách nào? Nếu bạn phải nâng goodput@SLO, bạn sẽ đổi knob
nào **trước**, và vì sao knob đó?

Server bão hòa ở 50 users: tải tăng 5x nhưng RPS chỉ tăng 1.6x, concurrency (11.9) vượt xa 4 slots. Latency tăng do queue time (46 deferred requests). Để tăng goodput@SLO, tôi hạ TPOT bằng quant nhỏ hơn hoặc offload GPU trước để giải phóng slot nhanh hơn.

---

## 4. Integration  *(rubric 12, 13 — 15 điểm)*

> Từ `make pipeline`. Nói thật cái nào real, cái nào stub — stub **không** mất điểm.

| Day | Piece | Real hay stub? |
|---|---|---|
| N16 Cloud/IaC | in-memory toy docs | stub |
| N17 Data pipeline | keyword overlap | stub |
| N18 Lakehouse | in-memory dict | stub |
| N19 Vector + features | keyword matching | stub |
| N20 Serving | `llama-server` | real |

**Latency split** (mean của 3 query, từ output của `pipeline.py`):

- embed: 0.0 ms
- retrieve: 0.1 ms
- llm: 4658.8 ms
- **stage chiếm nhiều nhất:** llm (100% của total)

**Reflection** (≤ 60 chữ): bottleneck ở đâu? Có khớp với kỳ vọng của bạn không? Nếu
phải giảm latency của pipeline này 2×, bạn sẽ tấn công vào đâu?

Bottleneck 100% nằm ở LLM, khớp với kỳ vọng vì decode autoregressive tuần tự. Để giảm 2x độ trễ, tôi sẽ dùng prompt caching để bỏ qua prefill và offload GPU để tăng tốc độ giải mã.

---

## 5. The single change that mattered most  *(rubric 11 — 10 điểm)*

> **Phần quan trọng nhất của report.** Không cần bonus track: `make tune` đã cho bạn
> một before/after thật (`benchmarks/01-tuning-tg128.md`). Đổi quantization,
> `LAB_N_CTX`, hay `--parallel` rồi đo lại cũng được.

**Change:** Giảm số luồng decode từ 8 physical cores xuống 4 threads (-t 4)

```
before:  9.6 tok/s (-t 8)
after:   11.2 tok/s (-t 4)
speedup: 1.16×
```

**Tại sao nó work** (1–2 đoạn — đây là phần grader đọc kỹ nhất):

Giai đoạn giải mã (decode) bị giới hạn bởi băng thông bộ nhớ (memory-bandwidth bound) chứ không phải năng lực tính toán FLOPs. Trên CPU AMD Ryzen 7 7435HS, chỉ cần 4 luồng thực thi là đã bão hòa hoàn toàn băng thông đọc của kênh nhớ DDR5 khi nạp trọng số mô hình cho mỗi token.

Khi nâng lên 8 luồng (toàn bộ physical cores) hoặc 16 luồng (SMT), các luồng tranh chấp bus bộ nhớ và bộ nhớ đệm L3, đồng thời gánh thêm chi phí đồng bộ luồng, khiến tốc độ giảm (từ 11.2 xuống 9.6 tok/s ở 8 luồng và sụp đổ xuống 3.3 tok/s ở 16 luồng). Việc giới hạn ở 4 luồng giúp tránh tranh chấp tài nguyên và đem lại thông lượng decode cao nhất.

---

## 6. Bonus  *(optional — tối đa 10 điểm)*

> Bỏ trống nếu không làm. Xem `docs/bonus/README.md`. Đừng làm hết — **một** finding sâu
> ăn điểm hơn năm bảng nông.

**Đã làm:** _<B1 build-compare / B2 sweep nào / B4 challenge nào / B5 lựa chọn nào>_

**Numbers:**

```
before:  <số>
after:   <số>
speedup: <X.Y>×
```

**Điều này nói lên gì mà deck chưa nói:**

_(để trống nếu bạn không làm phần này)_

---

## 7. Điều làm bạn ngạc nhiên nhất  *(optional)*

_(1–2 câu. Không bắt buộc, nhưng grader đọc hết.)_

_(để trống nếu bạn không làm phần này)_

---

## 8. Self-check trước khi push

- [ ] `hardware.json` committed
- [ ] `models/active.json` committed
- [ ] `benchmarks/01-quickstart-results.md` committed (`make bench`)
- [ ] `benchmarks/01-tuning-tg128.md` committed (`make tune`)
- [ ] `benchmarks/02-server-results.md` committed (`make load-report`)
- [ ] `benchmarks/02-server-batching-u50.md` hoặc `-metrics-u50.csv` committed (`make metrics`)
- [ ] `benchmarks/locust-10_stats.csv` + `locust-50_stats.csv` committed (`make load-10` / `load-50`)
- [ ] `benchmarks/03-integration-results.md` committed (`make pipeline`)
- [ ] Mọi section **"required — replace this line"** trong các file `benchmarks/*.md`
      đã được thay bằng nhận xét của bạn
- [ ] 5 screenshots trong `submission/screenshots/`
- [ ] `make verify` → **exit 0**
- [ ] Repo tên đúng mẫu `K4-L3-DAY20-HoVaTen-MSSV-ModelServing` (xem `docs/SUBMISSION.md`)
- [ ] Repo GitHub ở chế độ **public**
- [ ] Đã push và paste public URL vào VinUni LMS **trước 23:59 (UTC+7) ngày làm lab**
- [ ] **Không** commit `models/*.gguf`, `runtime/` hay `.env` (đã có trong `.gitignore`)

**Quan trọng:** repo phải **public** đến khi điểm được công bố. Private → grader không
xem được → 0 điểm.

---

## 9. Khai báo sử dụng AI  *(xem `docs/RULES.md` §3)*

- Công cụ: Antigravity AI Assistant
- Mục đích: Hỗ trợ khắc phục sự cố Windows Smart App Control bằng môi trường WSL 2, hỗ trợ chạy tự động hóa các tác vụ benchmark và định dạng báo cáo nộp bài.
