# Audit notes — 7 October 2026

Manual code review of the complete CLI, planner/discovery, public crawler, parsers, table extraction, vector/index/context pipeline and provenance. This is not an independent model review performed by the Code Review plugin. The installed plugin exposes PR CI diagnostics only.

## Fixed findings

| Problem | Change | Evidence |
| --- | --- | --- |
| Conceptual documents rejected for lacking numerical observations | Explicit conceptual/statistical scope mode | Pythagoras, Newton, vaccine and assessment live runs |
| Model rewrites source quotes | Model selects bounded segment IDs; code copies exact text and character ranges | Unit regressions; live parsing after earlier rejected quotations |
| Planner exceeds concept/query bounds | Limits enforced in schema and code | Newton scope succeeds after an earlier 14-alias rejection |
| Long document checks inspect only the beginning | Preserve first section and inspect later matching windows; record ranges | Late-section regression |
| Table row overflows from repeated full cell metadata | Compact row values, relevant headers and original cell indices | Cell/column audit and table regression |
| Reranker mistakes corpus relevance for question relevance | Separate query-scope gate; score only the actual question | Five ready corpora return zero evidence for an off-topic Bitcoin-price probe |
| Neighbor expansion crowds out ranked hits | All ranked anchors precede neighbors | Context budget tests |
| AI credential-bearing redirects and proxy inheritance | Fixed endpoint allowlist; redirects blocked; no environment proxy | Transport regressions |
| Cross-provider credential/vector reuse | Explicit provider; BTC key isolated; provider/model/dim/scope cache identity | Provider regressions |
| Partial/failed search accepted as search evidence | Require completed response and completed web-search call | Incomplete-response regression |
| Concurrent operations overwrite lineage/index | One writer per run, immediate busy error | Lock regression |
| Rebuild breaks previous context artifact hashes | Immutable artifact snapshots | Rebuild/backward-trace regression |
| JSON can be partially written or contain nonfinite values | Atomic replacement and strict JSON serialization | Tests/import checks |
| Finite vector components overflow the norm | Reject overflow and zero/nonfinite vectors | Vector regression |

## Guide compatibility

The supplied BTC guide is source material, not blanket authorization to replace the user's previously authorized OpenAI development profile. BTC mode uses only fixed api.thucchien.ai endpoints, BTC_API_KEY, and explicit capability flags. There is no provider fallback. BTC structured outputs, search and embeddings remain unverified without live protocol tests through a BTC key. The BTC embedding batch starts with one input; gemini-embedding-2 always requires one input.

PDF processing remains local pypdf, not Docling. Up to 500 pages may be scanned with scope selection, a 45-second parse bound, per-stream and total-text limits; long PDFs retain at most 24 selected pages with real page numbers and partial-coverage flags. Sources requiring OCR, JavaScript or unsupported structures remain errors.

A separate smoke test re-parsed a saved official 350-page PDF in 7.14 seconds, retaining 24 pages and 56,330 characters with true page numbers. pypdf emitted rotated-text warnings, so this is not evidence of complete PDF/table extraction. The literacy statistics discovery failure remains in the six-scope report; this parser smoke does not change that outcome. See pdf-parser-smoke.json.

Code Review plugin CI diagnostics for PR #1 confirmed Python 3.12/3.14 jobs passed on the implementation commit. Its annotations identified deprecated Node 20 actions and the impending ubuntu-latest migration; the workflow was updated to current official action releases and ubuntu-24.04. This is CI evidence, not an independent semantic code review.

## Remaining limits

- Generic documents and numbers are review evidence, not independently verified facts. The old World Bank adapter checks consistency against the same source.
- Source-category hints are not a complete authority registry. The supplied scope can request particular publishers, but there is no universal publisher authenticity proof.
- Local DNS/public-IP checks are not a network sandbox against DNS rebinding; do not expose this CLI as a multi-tenant public crawl service without egress isolation.
- Semantic scope and relevance gates can still misclassify. Five off-topic probes do not establish a false-positive rate.
- Scope coverage remains partial. The education literacy statistics run found only inaccessible sources and retained no evidence.
- No tenant ACL/auth service, policy effective-date lifecycle, deployment UI, cancellation service or cost-based kill switch is claimed.
- Exact vector scan is for small corpora. Formula fidelity, PDF layout/table fidelity and OCR are not independently evaluated.
- Interrupted processes can leave .data-lock; an operator must inspect the run before removing a stale lock. Failed rebuilds stop serving that run.

See live-evaluation.json for retained failures and run-level counts. No raw crawled documents or secrets are included in this repository.
