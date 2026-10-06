# Scope Data Bot

Bot CLI nhận **scope dữ liệu**, tự tìm nguồn → crawl → parse/check → save → chunk → embedding → index → gói evidence cho LLM. Ingestion không cần câu hỏi của user và không sinh câu trả lời.

Scope có thể là tài liệu khái niệm (định lý, giáo trình, nguyên lý vaccine) hoặc số liệu thống kê. Pipeline giữ raw source, metadata, locator và trace. Generic evidence luôn mang trạng thái review; việc index thành công không xác nhận số liệu đúng hoặc phạm vi đã đủ.

## Chạy

Python 3.12 hoặc 3.14. SQLite phải có FTS5.

```bash
git clone https://github.com/Qyroven/scope-data-bot.git
cd scope-data-bot
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock.txt
cp .env.example .env.local
# Điền key trong .env.local; không commit file này.
./run-data.sh --scope 'Thu thập tài liệu về định lý Pythagoras, điều kiện áp dụng và ví dụ'
```

Các lựa chọn input: `--scope`, `--brief-file <file.txt>` hoặc `--from-run bot-runs/<id>` để tiếp tục một lượt crawl đã có. Không tự crawl lại khi dùng from-run.

Giới hạn mặc định: 5 nguồn, 12 URL, depth 1, 400 chunks. Thay bằng `--max-sources`, `--max-pages`, `--max-depth`, `--max-chunks`. Chạy nhỏ trước; search/model/embedding dùng API trả phí. Mỗi request có timeout và giới hạn response, nhưng chưa có giới hạn tổng chi phí bằng tiền hoặc cancel service.

## Provider

`AI_PROVIDER=openai`: key OpenAI riêng, gpt-4.1-mini cho planner/search/check/rerank, text-embedding-3-small 1536 chiều mặc định. Đây là profile đã dùng để test live. Biến môi trường ưu tiên hơn .env.local.

`AI_PROVIDER=btc`: BTC_API_KEY, gpt-6-luna, text-multilingual-embedding-002 và EMBEDDING_DIMENSIONS=768. Request chỉ tới api.thucchien.ai, không tự fallback sang OpenAI. Phải smoke-test đúng model/endpoint/protocol rồi mới bật từng BTC_*_VERIFIED; bản hiện tại chưa chạy bằng key BTC và để các gate đóng. Đổi provider/model/dim cần xây index phù hợp; không so vector khác profile. Gemini-embedding-2 luôn một input/request.

Các endpoint/model BTC được đối chiếu với [Embedding BTC](https://docs.thucchien.ai/docs/round-2/user-guide/embeddings) và [Web search BTC](https://docs.thucchien.ai/docs/round-2/user-guide/google-search-grounding). Payload structured output qua BTC cần kiểm riêng; tên SDK/model không chứng minh gateway hỗ trợ toàn bộ protocol.

## Output

Mỗi lượt nằm ở `bot-runs/<id>/`:

| File/thư mục | Nội dung |
| --- | --- |
| scope.json, report.json, report.html | Scope, nguồn tìm được, lỗi và phần thiếu |
| raw/, parsed/ | Snapshot nguồn, parser output và bảng có vị trí ô |
| lineage.json, feedback.json | Truy ngược, lỗi phát hiện và đề xuất xử lý |
| data/chunks.json | Text, source ID/version, URL, locator, token count, quality, trace ID |
| data/index.sqlite | Vector + FTS5/BM25, model và dimensions |
| data/embedding-receipts.json | Response hash, usage và cache hits |
| data/manifest.json | Trạng thái index và thiếu định nghĩa/phạm vi |
| data/llm-input.json | Gói evidence theo scope trong 6000 tokens, báo đoạn bị bỏ vì budget |
| data/artifacts/ | Bản bất biến để rebuild không phá trace cũ |

`ready_partial` = có index dùng được, chưa chứng minh đầy đủ/chính xác. `no_evidence` = không có đoạn đủ điều kiện. `failed` = không được phục vụ index. Exit 0 khi có evidence; 2 khi thiếu evidence/lỗi. Documents out-of-scope/unassessed bị loại, review giữ cờ review. Cache theo provider/scope/text hash/model/dim/chunker.

## Phía LLM gọi khi user hỏi

```python
from data_pipeline import retrieve
context = retrieve('bot-runs/<id>', user_question, budget=6000, top_k=6)
# Chatbot truyền context vào LLM và yêu cầu trích evidence ID/source.
```

Luồng query: kiểm phạm vi câu hỏi → query embedding → cosine + BM25 → RRF → LLM relevance scoring → thêm đoạn liền kề → context có nguồn và cờ chất lượng. Đây chưa phải dedicated cross-encoder reranker. `rerank=False` bỏ gate/rerank; chế độ này không bảo đảm abstention, chỉ là truy hồi candidates.

Không nhét toàn bộ corpus vào prompt. Context bị giới hạn, metadata và đoạn omitted được báo rõ. Mỗi context lưu riêng `data/context-*.json` với trace ID. Scope chỉ là phạm vi corpus; câu hỏi do chatbot nhận sau ingestion.

## Kiểm và truy ngược

```bash
.venv/bin/python -m unittest discover -p 'test_*.py'
.venv/bin/python -m pip check
.venv/bin/python audit_run.py --run bot-runs/<id>
.venv/bin/python trace.py --run bot-runs/<id> --target n00001
# Tốn API: test live sáu scope, concurrency tối đa 2.
.venv/bin/python evaluate_live.py --output bot-runs/eval --workers 2
```

`audit_run.py` đối chiếu text spans, vị trí hàng/ô, chunks/index, dimensions, token count và hash trên trace. Nó không xác nhận sự thật trong tài liệu hoặc độ trung thực với PDF/HTML đã render. Nơi phát hiện lỗi không tự chứng minh nguyên nhân gốc; feedback chưa tự sửa sự thật.

Kết quả ngày 07/10/2026: **73 tests offline pass**, pip check pass. Live: Pythagoras 126 chunks; Newton 27; vaccine/miễn dịch WHO 15; đánh giá giáo dục 1; tuổi thọ 61. Cả 5 index qua preservation audit/truy ngược, có context và không trả evidence cho probe Bitcoin ngoài scope sau sửa. Tỉ lệ biết chữ vẫn no_evidence vì nguồn lỗi; không bù số liệu. Đây là integration probes, chưa phải benchmark retrieval/factual accuracy. Xem [báo cáo đầy đủ](docs/live-evaluation.json) và [review/fixes/giới hạn](docs/REVIEW.md).

## Giới hạn hiện tại

Parser local: HTML/CSV/JSON và pypdf. Long PDF có scope được scan tối đa 500 trang, 45 giây, giữ tối đa 24 trang có liên quan; số trang và cờ partial thật được lưu. Không Docling/OCR, chưa kiểm độc lập độ chính xác công thức/bảng PDF. Nguồn chặn/JavaScript/định dạng không hỗ trợ giữ lỗi.

Một writer cho mỗi run; operation đồng thời báo RUN_BUSY. Crash có thể để .data-lock, cần kiểm run trước khi xóa lock cũ. Exact vector search phù hợp corpus nhỏ. Đây là CLI đơn người dùng, chưa có UI, tenant ACL hoặc egress sandbox cho dịch vụ crawl công khai. Chỉ nhận nguồn công khai; không đưa tài liệu cá nhân vào repo.

Repo không chứa key, raw pages, vectors, private guide hay thư mục các lượt chạy. Public chỉ có code, fixtures kiểm logic và summary đã bỏ đường dẫn máy cá nhân. GitHub CI kiểm offline trên Python 3.12/3.14, không gọi inference bằng key thật.
