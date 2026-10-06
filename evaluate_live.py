"""Bounded live integration probes, not a factual accuracy benchmark.

python evaluate_live.py --output bot-runs/multi-topic --workers 2
Paid AI calls: six scopes, <=3 discovery queries/scope, <=3 crawled URLs,
<=200 chunks/scope, one relevant and one off-topic retrieval probe per ready run.
Never uses model-generated answers as a ground-truth oracle.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import time

from bot import run_bot
from data_pipeline import build, retrieve, tokens
from engine import save_json
from trace import explain
from audit_run import audit

CASES = [
    ("education_statistics", "Thu thập số liệu tỷ lệ biết chữ của người từ 15 tuổi trở lên tại Việt Nam 2020-2022, mẫu số là tổng dân số từ 15 tuổi trở lên.", "Các nguồn có số liệu biết chữ cho những năm nào và còn thiếu gì?"),
    ("health_statistics", "Thu thập số liệu tuổi thọ kỳ vọng khi sinh, cả hai giới tại Việt Nam 2020-2022.", "Định nghĩa tuổi thọ khi sinh trong tài liệu là gì? Có số liệu năm nào?"),
    ("mathematics", "Thu thập tài liệu giảng dạy về định lý Pythagoras: phát biểu, điều kiện tam giác vuông, chứng minh và ví dụ.", "Định lý Pythagoras cần điều kiện nào và quan hệ giữa các cạnh là gì?"),
    ("physics", "Thu thập tài liệu giáo trình về định luật thứ hai Newton, F = ma, điều kiện áp dụng, đơn vị lực và ví dụ.", "Định luật thứ hai Newton liên hệ lực, khối lượng và gia tốc thế nào?"),
    ("health_concepts", "Thu thập tài liệu giải thích nguyên lý vaccine và miễn dịch cộng đồng từ WHO, phân biệt phòng nhiễm và phòng bệnh nặng.", "Tài liệu giải thích miễn dịch cộng đồng và vai trò của vaccine như thế nào?"),
    ("education_concepts", "Thu thập tài liệu giải thích formative assessment và summative assessment trong giáo dục, định nghĩa, khác biệt và ví dụ.", "Khác biệt giữa formative assessment và summative assessment trong nguồn là gì?"),
]


def probe(case, output):
    label, brief, question = case
    started = time.monotonic()
    result = {"case": label, "scope": brief, "status": "failed"}
    try:
        report, folder = run_bot(brief, output / label, max_sources=3, max_pages=3, max_depth=0,
                                search_provider="openai", planner="model")
        manifest = build(folder, max_chunks=200)
        result.update(run=str(folder), crawl_status=report["status"], mode=manifest["scope"].get("content_mode"),
            counts=report.get("counts", {}), candidates=len(report.get("candidates", [])),
            chunks=manifest["chunk_count"], status=manifest["status"], ambiguities=manifest["ambiguities"],
            crawl_error=report.get("error"))
        if manifest["chunk_count"]:
            preservation = audit(folder)
            bundle = retrieve(folder, question, budget=6000, top_k=4)
            backward = explain(folder, bundle["trace_id"])
            off_topic = retrieve(folder, "What is the current price of Bitcoin right now?", top_k=4)
            result.update(context_evidence=len(bundle["evidence"]),
                context_tokens=tokens(json.dumps(bundle, ensure_ascii=False)),
                trace_id=bundle["trace_id"], trace_stages=sorted({n["stage"] for n in backward["backward_trace"]}),
                integrity_pass=all(n["artifact_integrity"] is not False for n in backward["backward_trace"]),
                preservation_audit=preservation['status'],
                off_topic_evidence=len(off_topic["evidence"]), off_topic_abstained=not bool(off_topic["evidence"]),
                quality=sorted({c["quality"] for c in bundle["evidence"]}))
            save_json(folder / "data/evaluation.json", result)
    except Exception as error:
        result["error"] = str(error)
    result["seconds"] = round(time.monotonic()-started, 2)
    save_json(output / (label + ".json"), result)
    print("[eval] " + json.dumps(result, ensure_ascii=False), flush=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workers", type=int, choices=(1,2), default=1)
    parser.add_argument("--cases",nargs='+',choices=[c[0] for c in CASES])
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        cases=[c for c in CASES if not args.cases or c[0] in args.cases]
        results = list(pool.map(lambda case: probe(case, args.output), cases))
    save_json(args.output / "summary.json", {"type": "live_integration_not_accuracy_benchmark", "results": results,
        "limitations": "No independently labeled relevance corpus or factual oracle. Review docs remain unverified. Failed/no-evidence cases are retained."})


if __name__ == "__main__":
    main()
