# Issues to unblock project vision

This document contains prioritized, actionable GitHub issues for the File-Sharing-P2P project. The repository currently has Issues disabled; I am adding these as a tracked file (ISSUES.md). If you enable Issues in the repository I can open them directly.

Each item includes: title, description, steps to reproduce / impact, suggested fix, priority, and estimated effort (Small/Medium/Large). Use the text below to create GitHub issues or enable Issues and I will open them for you.

---

## 1) Make part downloads concurrent (parallelize per-part downloads)

- Priority: P0 (Critical)
- Effort: Medium

Description:
The current download flow performs per-part download requests sequentially (requests.post in a loop or through a single-threaded Flask server), so parts are downloaded one after the other. This prevents the app from benefiting from parallel downloads from multiple peers and severely limits throughput.

Impact:
- Slows downloads dramatically for multi-part files and defeats the P2P design.

Suggested fix:
- Replace the sequential loop with concurrent execution. Two practical options:
  - Minimal change: call the existing blocking request_download directly using concurrent.futures.ThreadPoolExecutor (bounded max_workers) and wait for results as they complete.
  - Better/scale: rewrite request_download and the download manager to be async using asyncio streams + asyncio.gather and use an asyncio.Semaphore to cap concurrency.
- Ensure the Flask endpoint does not become the bottleneck (call request_download directly from the same process or run Flask with threaded=True or under a WSGI server with workers if still using HTTP hops).

Checklist:
- Implement threadpool prototype and validate parallel downloads locally.
- Add timeouts/retries and per-part progress.
- Add per-part checksums and verify before stitching.

---

## 2) Make collector (receiver) non-blocking and ACK on successful save

- Priority: P0 (Critical)
- Effort: Small

Description:
collector.respond_peer calls save_data synchronously (base64 decode + file write) inside an asyncio-based accept loop. That blocks the event loop while writing to disk and may delay other incoming connections. Also, the sender records part ownership in the DB without an explicit acknowledgement from the receiver that the part was saved.

Impact:
- Receiver cannot service other peers concurrently while saving, reducing overall throughput.
- Database may claim parts present on peers that failed to write, causing broken downloads.

Suggested fix:
- Offload base64 decode + file write to a background thread using asyncio.to_thread or use aiofiles for async writes.
- Only update the central registry (Part entry) after the receiver confirms successful write (ACK). Add an explicit ACK/NACK exchange between sender and collector.

Checklist:
- Make save_data non-blocking (async wrapper or to_thread).
- Implement a simple textual or JSON ACK message on the TCP connection and update DB only after ACK.

---

## 3) Avoid sending large base64 blobs inside JSON; use framed raw bytes or length-prefixed frames

- Priority: P0 (Critical)
- Effort: Medium

Description:
Parts are transmitted as base64-encoded strings inside JSON. Base64 increases bandwidth by ~33% and requires copying large strings into memory. Sending large base64 blobs in JSON is memory-inefficient and CPU-heavy.

Impact:
- High CPU and memory usage for large files; slow transfers.

Suggested fix:
- Use a small JSON/metadata header followed by raw bytes, or a length-prefixed frame protocol. Example: send a JSON header with meta and an integer length, then stream raw bytes for the part. Or use a simple multipart framing scheme.
- If sticking with JSON, at least send base64 in streaming chunks rather than a single giant JSON value.

---

## 4) Make storage path and server config configurable (remove hardcoded paths/URLs)

- Priority: P1
- Effort: Small

Description:
The code hardcodes server URLs (127.0.0.1:5000) and storage paths (/home/<user>/.localran/). This breaks cross-platform usage and prevents flexible deployment.

Suggested fix:
- Use environment variables or a config file (dotenv already used for DB URI) for SERVER, ports, and storage path.
- Respect XDG Base Directory on Linux and provide sensible defaults for other OSes.

---

## 5) Add per-part integrity checks (checksums) and verify before stitching

- Priority: P1
- Effort: Small

Description:
There is no per-part checksum or verification step before stitching parts together. This risks producing corrupted final files.

Suggested fix:
- Compute and store a SHA-256 per part during upload; send checksum in metadata. Receiver verifies decoded part matches checksum and only ACKs if it does.

---

## 6) Improve error handling, timeouts, and retries for network operations

- Priority: P1
- Effort: Small

Description:
Many socket and HTTP calls lack robust timeouts, retries, or backoff strategies. The system can hang waiting on slow peers.

Suggested fix:
- Add per-connection timeouts and limited retries with exponential backoff. Ensure callers fail fast when peers are dead.

---

## 7) Add authentication/authorization and secure transport for peer transfers

- Priority: P0
- Effort: Large

Description:
There is no authentication between peers and no TLS. Any machine on the network could send/receive parts. This is a security risk for production use.

Suggested fix:
- Add lightweight authentication (shared tokens or API keys) and optionally use TLS (mutual TLS if possible). Consider using signed metadata for parts.

---

## 8) Improve logging, structured errors and API responses

- Priority: P2
- Effort: Small

Description:
The code uses prints and inconsistent API responses. Use Python logging and consistent JSON HTTP responses with proper status codes.

Suggested fix:
- Replace prints with logging (with levels), standardize API error payloads, and add observability for transfers.

---

## 9) Packaging and local dev: add Docker / docker-compose and README

- Priority: P2
- Effort: Small

Description:
There is no easy way to run the full stack locally (Mongo + backend + frontend). Add a docker-compose for dev convenience and update README with run steps.

Suggested fix:
- Add docker-compose.yml with services for mongo and the backend, and instructions in README.

---

## 10) Tests and CI

- Priority: P2
- Effort: Medium

Description:
No unit or integration tests. Add tests for DB wrappers, distributor.populate_peers logic, and download/upload flows.

Suggested fix:
- Add pytest tests for core logic and a lightweight integration test that runs the collector in-process.

---

# Next steps
1. Enable Issues for the repository so I can open these issues directly on GitHub.
2. Alternatively, review the items above and tell me which ones you want me to prioritize; I can create PRs for small fixes (e.g., make collector non-blocking, fix sequential download behavior) immediately.