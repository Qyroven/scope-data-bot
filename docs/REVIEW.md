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

PDF/image/Office processing now uses isolated Docling 2.134.0 with local EasyOCR vi/en and table extraction. PDF native mode remains available explicitly. Default Docling processing covers the first 40 pages with a 180-second process-group timeout and clear partial flags; no guessed scope page selection is presented as full coverage. Native Docling JSON and page/bbox/cell references survive normalization and chunking. Parser models are downloaded only during setup; normal workers are offline for model retrieval, disable remote services and do not inherit API credentials/proxies. This is not a general OS network/memory sandbox.

The earlier pypdf smoke test re-parsed a saved official 350-page PDF in 7.14 seconds, retaining 24 pages and 56,330 characters with true page numbers. pypdf emitted rotated-text warnings, so this is not evidence of complete PDF/table extraction. The literacy statistics discovery failure remains in the six-scope report; this parser smoke does not change that outcome. See pdf-parser-smoke.json.

Code Review plugin CI diagnostics for PR #1 confirmed Python 3.12/3.14 jobs passed on the implementation commit. Its annotations identified deprecated Node 20 actions and the impending ubuntu-latest migration; the workflow was updated to current official action releases and ubuntu-24.04. This is CI evidence, not an independent semantic code review.

## Remaining limits

- Generic documents and numbers are review evidence, not independently verified facts. The old World Bank adapter checks consistency against the same source.
- Source-category hints are not a complete authority registry. The supplied scope can request particular publishers, but there is no universal publisher authenticity proof.
- Local DNS/public-IP checks are not a network sandbox against DNS rebinding; do not expose this CLI as a multi-tenant public crawl service without egress isolation.
- Semantic scope and relevance gates can still misclassify. Five off-topic probes do not establish a false-positive rate.
- Scope coverage remains partial. The education literacy statistics run found only inaccessible sources and retained no evidence.
- No tenant ACL/auth service, policy effective-date lifecycle, deployment UI, cancellation service or cost-based kill switch is claimed.
- Exact vector scan is for small corpora. Rendered parser probes reveal real OCR/table errors: paired rows merge, a Vietnamese numerical cell is missing, and portions of prose are lost. These are documented model limitations, not repaired by inventing source content. Formula enrichment is disabled and complex formula fidelity is unverified.
- The parser worker has time/input/output/Office decompression/image-size limits, not a hard memory limit. First-page-range truncation may miss relevant later material; a partial result is never a completeness claim. Oversized table rows fail rather than split values unsafely.
- Interrupted processes can leave .data-lock; an operator must inspect the run before removing a stale lock. Failed rebuilds stop serving that run.

See live-evaluation.json for retained failures and run-level counts. No raw crawled documents or secrets are included in this repository.

## Docling/OCR integration review

Reviewed full transport, planner/search/ranking/check, crawler/format routing, subprocess/cache, HTML/table and Docling normalization, chunk/vector/index/context, trace/audit, CLI/bootstrap and CI code. Uniform Ruff formatting, unused imports/constants removed, explicit strict zips and lint regressions are now enforced in CI.

| Finding | Fix | Verification |
| --- | --- | --- |
| Generic traced wrapper cannot forward new parser keyword arguments | Forward keyword options on traced and untraced paths | Crawl→Docling→save integration regression |
| OCR child can inherit credentials/proxy/Python injection | Allowlisted child environment, local models, no arbitrary URL input | Worker environment regression; no AI key used for parse |
| Hanging parser outlives caller | Separate process group and hard timeout, terminate descendants | Real sleeping-worker timeout regression |
| Same raw PDF with different OCR/config versions shares document identity | Include library/config/content fingerprint in document version; parse cache includes worker/dependency lock and setup model fingerprint | Config preserved in parsed artifacts |
| Model merges data rows or misses cells | Preserve raw recognized strings/null, flag multiple-number cells and missing grid coordinates, carry warnings into page and table chunks | Rendered English/Vietnamese document comparisons, no auto-filled numbers |
| Normalization may corrupt native Docling coordinates/text | Audit native JSON text, pages, cell coordinates/header flags/bboxes against normalized data | Two real parser corpora pass, tampering regression |
| PDF page cap loses coverage silently | Save total pages/selected pages/partial note | 350-page official PDF limited to page 1 explicitly marked partial |
| Long-text chunking repeatedly tokenizes huge suffixes | Exponential local upper bound before binary search | Same spans; 1.6293s→0.1968s on one 268k-character microbenchmark |
| Vector query norm recomputed for every chunk; zip truncation can hide mismatch | Compute query norm once, require one query vector, strict zips | Existing vector/count/contract tests |
| Wrapper only checks imports, allowing wrong/stale dependency versions | Shared pinned bootstrap and requirements hash | CLI help/bootstrap smoke, pip compatibility checks |
| Universal parser lock installs unnecessary CUDA packages on Linux | Compile/install CPU backend with platform markers | Separate CPU parser CI smoke |

Local evidence: **87 executed offline tests pass**, one optional real Docling DOCX/Unicode/table smoke passes, lint/format and both runtime compatibility checks pass. Four fresh scope-driven live tests (mathematics, physics, health, education) create 170 chunks total, preserve hashes/source spans, retrieve context and abstain on the Bitcoin probe. They used HTML sources, so they are not claimed as OCR end-to-end search tests. Separate manually supplied PDF/image parser corpora create 24 real 1536-dimensional vectors and valid contexts, with native-JSON/preservation audit and backward hashes passing.

PDF scan test has zero native pypdf text but yields 94 recognized characters through Docling/EasyOCR. DOCX/PPTX/XLSX/formula-PDF probes show format support, not universal layout/fidelity accuracy. Model-weight file fingerprints are recorded at setup in ignored .parser-models.json and included in parser config; they are not rehashed on every document. Rerun setup after changing weights. See [docling-evaluation.json](docling-evaluation.json) for counts, observed failures and benchmark caveats.
