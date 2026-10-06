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
./setup-parser.sh  # Cần uv; tải model Docling/OCR local một lần, runtime Python 3.12 riêng.
./run-data.sh --scope 'Thu thập tài liệu về định lý Pythagoras, điều kiện áp dụng và ví dụ'
```

Các lựa chọn input: `--scope`, `--brief-file <file.txt>` hoặc `--from-run bot-runs/<id>` để tiếp tục một lượt crawl đã có. Không tự crawl lại khi dùng from-run.

`--parser docling --ocr auto` dùng Docling, giữ text PDF có sẵn và OCR vùng ảnh. `--ocr full` OCR toàn trang; `--ocr off` tắt OCR. `--document-max-pages 40` giới hạn số trang đầu, luôn báo partial nếu tài liệu dài hơn. Các flag parse chỉ áp dụng cho lượt scope mới; `--from-run` không parse lại bản gốc.

`setup-parser.sh` cài dependency đã pin trong `.venv-docling`, tải layout/table/EasyOCR tiếng Việt/Anh. Không cần key AI cho parse, tài liệu được xử lý local. Máy khác cần chạy setup một lần; có thể dùng lại cùng model embedding nếu provider hỗ trợ. Model parse không phụ thuộc gateway BTC/OpenAI.

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
| parsed/* với parser Docling | Native Docling JSON, trang/bbox, grid ô gộp, config/version, cảnh báo OCR/bảng và cờ partial |
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

context = retrieve("bot-runs/<id>", user_question, budget=6000, top_k=6)
# Chatbot truyền context vào LLM và yêu cầu trích evidence ID/source.
```

Luồng query: kiểm phạm vi câu hỏi → query embedding → cosine + BM25 → RRF → LLM relevance scoring → thêm đoạn liền kề → context có nguồn và cờ chất lượng. Đây chưa phải dedicated cross-encoder reranker. `rerank=False` bỏ gate/rerank; chế độ này không bảo đảm abstention, chỉ là truy hồi candidates.

Không nhét toàn bộ corpus vào prompt. Context bị giới hạn, metadata và đoạn omitted được báo rõ. Mỗi context lưu riêng `data/context-*.json` với trace ID. Scope chỉ là phạm vi corpus; câu hỏi do chatbot nhận sau ingestion.

## Kiểm và truy ngược

```bash
.venv/bin/python -m unittest discover -p 'test_*.py'
.venv/bin/python -m pip check
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/python audit_run.py --run bot-runs/<id>
.venv/bin/python trace.py --run bot-runs/<id> --target n00001
# Tốn API: test live sáu scope, concurrency tối đa 2.
.venv/bin/python evaluate_live.py --output bot-runs/eval --workers 2
```

`audit_run.py` đối chiếu text spans, vị trí hàng/ô, chunks/index, dimensions, token count và hash trên trace. Nó không xác nhận sự thật trong tài liệu hoặc độ trung thực với PDF/HTML đã render. Nơi phát hiện lỗi không tự chứng minh nguyên nhân gốc; feedback chưa tự sửa sự thật.

Kết quả ngày 07/10/2026: **87 tests offline pass**, lint/format và pip check pass. Vòng live mới: Pythagoras 116 chunks; Newton 24; vaccine/miễn dịch 18; đánh giá giáo dục 12. Cả 4 index qua audit/truy ngược và không trả evidence cho probe Bitcoin ngoài scope. Vòng trước gồm cả tuổi thọ và thất bại nguồn biết chữ vẫn lưu riêng. Đây là integration probes, chưa phải benchmark retrieval/factual accuracy. Xem [vòng mới](docs/docling-evaluation.json), [vòng trước](docs/live-evaluation.json) và [review/fixes/giới hạn](docs/REVIEW.md).

Parser đã thử PDF native có bảng, PDF scan không có lớp chữ, ảnh trang tiếng Việt, DOCX/PPTX/XLSX và PDF công thức. Hai corpus parse QA tạo **24 chunks/vector thật 1536 chiều**, qua native-JSON/preservation audit và truy ngược; nguồn QA được cung cấp thủ công, không phải bài test tìm nguồn tự động. Có lỗi model thật: gộp hàng bảng tiếng Anh, OCR bỏ sót ô `2,7` và mất chữ tiếng Việt. Các lỗi quan sát được ghi trong báo cáo; bot giữ null/cảnh báo, không tự điền số. Scan/layout/OCR không được coi là đã xác minh vì parse chạy thành công.

## Giới hạn hiện tại

Parser nhẹ cho HTML/CSV/JSON; Docling local cho PDF, PNG/JPEG/TIFF/WebP một frame và DOCX/PPTX/XLSX. OCR EasyOCR vi/en, bảng TableFormer, CPU mặc định 2 threads. Docling mặc định xử lý 40 trang đầu, timeout cứng 180 giây, tối đa input 10 MB/500 trang PDF, output 600k ký tự/20 MB JSON; file Office có giới hạn giải nén, ảnh tối đa 20 MP. Timeout kết thúc cả nhóm tiến trình. Chưa có hard memory sandbox; không dùng trực tiếp cho upload không tin cậy từ nhiều tenant.

`.env.example` yêu cầu Docling. `DOCUMENT_PARSER=auto` dùng Docling khi runtime đã cài; nếu chưa có thì PDF dùng pypdf và ghi hạn chế rõ, ảnh/Office báo cần setup. `--parser native` chọn pypdf. Native long PDF vẫn giữ tối đa 24 trang theo scope (scan tối đa 500 trang/45 giây). Cache parse local theo raw/config/worker/dependency-lock, không cache assessment; không bị lẫn scope. Cache không phải kho bằng chứng: từng run vẫn giữ raw/parsed và trace riêng.

Formula enrichment, mô tả ảnh/biểu đồ và chữ viết tay chưa được kiểm chứng; chưa bật các model enrichment nặng. Không có cam kết đọc đúng mọi công thức/bảng, hay mọi ngôn ngữ. Nguồn chặn/JavaScript/định dạng không hỗ trợ giữ lỗi. Tham khảo API sử dụng tại [Docling OCR](https://docling-project.github.io/docling/_generated/examples/full_page_ocr/) và [offline/local models](https://docling-project.github.io/docling/usage/advanced_options/).

Một writer cho mỗi run; operation đồng thời báo RUN_BUSY. Crash có thể để .data-lock, cần kiểm run trước khi xóa lock cũ. Exact vector search phù hợp corpus nhỏ. Đây là CLI đơn người dùng, chưa có UI, tenant ACL hoặc egress sandbox cho dịch vụ crawl công khai. Chỉ nhận nguồn công khai; không đưa tài liệu cá nhân vào repo.

Repo không chứa key, raw pages, vectors, private guide hay thư mục các lượt chạy. Public chỉ có code, fixtures kiểm logic và summary đã bỏ đường dẫn máy cá nhân. GitHub CI kiểm offline trên Python 3.12/3.14, không gọi inference bằng key thật.
