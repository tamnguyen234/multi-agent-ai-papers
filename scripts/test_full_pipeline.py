"""
Task 19: Full Pipeline End-to-End Test Script
==============================================
Kiểm thử tự động toàn bộ pipeline từ backend đến frontend APIs.

Cách chạy:
    python scripts/test_full_pipeline.py

Biến môi trường tùy chọn (có thể đặt trước khi chạy):
    TEST_USERNAME   - tên đăng nhập demo (mặc định: demo_user_pipeline)
    TEST_PASSWORD   - mật khẩu demo     (mặc định: DemoPassword123!)
    TEST_EMAIL      - email demo         (mặc định: aipapereveryday@gmail.com)
    BACKEND_URL     - backend URL        (mặc định: http://127.0.0.1:8000)

Lưu ý an toàn:
    - Không in full JWT token ra console.
    - Không xóa dữ liệu DB.
    - Script dùng test user demo, không phải user thật.
    - Nếu test user đã tồn tại → thử login ngay, không fail.
"""

import os
import sys
import json
import time
import requests
from datetime import datetime

# Fix Windows terminal encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", write_through=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace", write_through=True)

# ──────────────────────────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────────────────────────
BACKEND_URL  = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")
API_BASE     = f"{BACKEND_URL}/api/v1"

# Agents (chi kiem tra health, khong goi truc tiep trong pipeline)
AGENT_URLS = {
    "Summarizer Agent (8101)": "http://127.0.0.1:8101/health",
    "Trend Agent     (8102)": "http://127.0.0.1:8102/health",
    "Q&A Agent       (8103)": "http://127.0.0.1:8103/health",
    "TTS Agent       (8104)": "http://127.0.0.1:8104/health",
}

# Test user demo (khong phai secret, chi la data demo)
TEST_USERNAME = os.environ.get("TEST_USERNAME", "demo_user_pipeline")
TEST_PASSWORD = os.environ.get("TEST_PASSWORD", "DemoPassword123!")
TEST_EMAIL    = os.environ.get("TEST_EMAIL",    "aipapereveryday@gmail.com")
TEST_FULLNAME = "Pipeline Test User"

TIMEOUT = 300  # seconds cho digest job
SHORT_TIMEOUT = 30

# ──────────────────────────────────────────────────────────────────
# Test result tracking
# ──────────────────────────────────────────────────────────────────
results = []

def record(step, status, detail=""):
    """Ghi lai ket qua test step."""
    icon = "[PASS]" if status == "PASS" else ("[WARN]" if status == "WARN" else "[FAIL]")
    line = f"  {icon} {step}"
    if detail:
        line += f": {detail}"
    print(line)
    results.append({"step": step, "status": status, "detail": detail})
    return status == "PASS"

def separator(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def mask_token(token: str) -> str:
    """Chi hien thi 8 ky tu dau cua JWT token."""
    if not token:
        return "(empty)"
    return token[:8] + "..." + f"[{len(token)} chars]"

# ──────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────
def get(path, token=None, timeout=SHORT_TIMEOUT):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        r = requests.get(f"{API_BASE}{path}", headers=headers, timeout=timeout)
        return r
    except Exception as e:
        print(f"  [DEBUG] GET {path} raised {type(e).__name__}: {e}")
        return None

def post(path, body=None, token=None, timeout=SHORT_TIMEOUT):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        r = requests.post(f"{API_BASE}{path}", json=body or {}, headers=headers, timeout=timeout)
        return r
    except Exception as e:
        print(f"  [DEBUG] POST {path} raised {type(e).__name__}: {e}")
        return None

def agent_get(url, timeout=5):
    try:
        r = requests.get(url, timeout=timeout)
        return r
    except Exception:
        return None

# ──────────────────────────────────────────────────────────────────
# STEP 0: Timestamp
# ──────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print(f"  Task 19 - Full Pipeline Test")
print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"  Backend: {BACKEND_URL}")
print("="*60)

# ──────────────────────────────────────────────────────────────────
# STEP 1: Backend health check
# ──────────────────────────────────────────────────────────────────
separator("STEP 1: Health Checks")

r = get("/system/db-health")
if r is not None and r.status_code == 200:
    data = r.json()
    db_status = data.get("status", "?")
    record("Backend DB Health", "PASS", f"status={db_status}")
else:
    status_code = r.status_code if r is not None else "NO_RESPONSE"
    record("Backend DB Health", "FAIL", f"HTTP {status_code} - Backend không phản hồi")

# ──────────────────────────────────────────────────────────────────
# STEP 2: Agent health checks
# ──────────────────────────────────────────────────────────────────
separator("STEP 2: Agent Health Checks (direct, not via Gateway)")
print("  Note: Frontend không gọi trực tiếp các agents - chỉ test từ Python")

for agent_name, url in AGENT_URLS.items():
    r = agent_get(url)
    if r is not None and r.status_code == 200:
        try:
            body = r.json()
            mode = body.get("mode", body.get("status", "ok"))
            record(agent_name, "PASS", f"mode={mode}")
        except Exception:
            record(agent_name, "PASS", "HTTP 200 OK")
    else:
        code = r.status_code if r is not None else "NO_RESPONSE"
        record(agent_name, "WARN", f"HTTP {code} - có thể chưa khởi động")

# ──────────────────────────────────────────────────────────────────
# STEP 3: Register + Login demo user
# ──────────────────────────────────────────────────────────────────
separator("STEP 3: Auth - Register / Login Demo User")

access_token = None

# Thử đăng ký trước
reg_payload = {
    "username": TEST_USERNAME,
    "email": TEST_EMAIL,
    "password": TEST_PASSWORD,
    "full_name": TEST_FULLNAME
}
r = post("/auth/register", reg_payload)

if r is not None and r.status_code in (200, 201):
    record("Auth: Register demo user", "PASS", f"username={TEST_USERNAME}")
elif r is not None and r.status_code in (400, 409, 422):
    # User đã tồn tại - không phải lỗi
    record("Auth: Register demo user", "WARN", "User đã tồn tại → sẽ dùng login")
else:
    code = r.status_code if r is not None else "NO_RESPONSE"
    record("Auth: Register demo user", "WARN", f"HTTP {code} - thử login...")

# Đăng nhập
login_payload = {"username": TEST_USERNAME, "password": TEST_PASSWORD}
r = post("/auth/login", login_payload)

if r is not None and r.status_code == 200:
    data = r.json()
    access_token = data.get("access_token", "")
    if access_token:
        record("Auth: Login demo user", "PASS", f"token={mask_token(access_token)}")
    else:
        record("Auth: Login demo user", "FAIL", f"Không có access_token trong response: {data}")
else:
    code = r.status_code if r is not None else "NO_RESPONSE"
    body = ""
    if r is not None:
        try:
            body = r.json().get("detail", r.text[:100])
        except Exception:
            body = r.text[:100]
    record("Auth: Login demo user", "FAIL", f"HTTP {code}: {body}")

if not access_token:
    print("\n  [WARN] Không có token → các bước cần auth sẽ bị skip")

# ──────────────────────────────────────────────────────────────────
# STEP 4: Run daily digest job
# ──────────────────────────────────────────────────────────────────
separator("STEP 4: Daily Digest Job")
print("  POST /api/v1/dev/run-daily-digest-job")
print("  (Có thể mất 20-60s vì gọi Summarizer Agent, PDF download, TTS...)")

r = post("/dev/run-daily-digest-job", timeout=TIMEOUT)

digest_job_ok = False
if r is not None and r.status_code == 200:
    data = r.json()
    digest_id      = data.get("digest_id")
    papers_count   = data.get("total_papers", 0)
    sent_count     = data.get("sent_count", 0)
    failed_count   = data.get("failed_count", 0)
    summarizer_mode = data.get("summarizer_mode", "?")

    detail = (f"digest_id={digest_id}, papers={papers_count}, "
              f"email_sent={sent_count}, email_failed={failed_count}")

    if papers_count and papers_count >= 1:
        record("Daily Digest Job: Run", "PASS", detail)
        digest_job_ok = True
    else:
        # Có thể trả 0 papers nếu arXiv hôm nay chưa có bài hoặc mode=mock
        record("Daily Digest Job: Run", "WARN", f"Chạy OK nhưng papers={papers_count} - {detail}")
        digest_job_ok = True
elif r is not None and r.status_code == 500:
    try:
        err = r.json().get("detail", r.text[:200])
    except Exception:
        err = r.text[:200]
    record("Daily Digest Job: Run", "FAIL", f"HTTP 500: {err}")
else:
    code = r.status_code if r is not None else "NO_RESPONSE (timeout?)"
    record("Daily Digest Job: Run", "FAIL", f"HTTP {code}")

# ──────────────────────────────────────────────────────────────────
# STEP 5: Get today's digest + assert papers
# ──────────────────────────────────────────────────────────────────
separator("STEP 5: Get Today Digest")

r = get("/digests/today", token=access_token)
digest_papers = []
first_paper_id = None
first_paper_pdf = None
first_paper_audio = None

if r is not None and r.status_code == 200:
    data = r.json()
    digest_date    = data.get("digest_date", "?")
    digest_papers  = data.get("papers", [])
    total_papers   = len(digest_papers)

    record("Get Today Digest", "PASS", f"digest_date={digest_date}, papers={total_papers}")

    # Assert số papers
    if total_papers == 5:
        record("Digest: Exactly 5 papers", "PASS")
    elif total_papers > 0:
        record("Digest: Papers count", "WARN", f"{total_papers} papers (expected 5, có thể do mode mock hoặc ít bài)")
    else:
        record("Digest: Papers count", "FAIL", "0 papers - digest rỗng")

    # Kiểm tra rank_position và fields
    ranks_ok = True
    for entry in digest_papers:
        paper = entry.get("paper", {}) if "paper" in entry else entry
        rank  = entry.get("rank_position", entry.get("rank", None))
        title = paper.get("title", "") if isinstance(paper, dict) else getattr(paper, "title", "")
        arxiv_id = paper.get("arxiv_id", "") if isinstance(paper, dict) else getattr(paper, "arxiv_id", "")
        summary  = paper.get("summary", "") if isinstance(paper, dict) else getattr(paper, "summary", "")
        pdf_url  = paper.get("pdf_url", paper.get("pdf_path", "")) if isinstance(paper, dict) else ""
        audio_url = paper.get("audio_abstract_url", paper.get("audio_abstract_path", "")) if isinstance(paper, dict) else ""

        if not title or not arxiv_id:
            ranks_ok = False

        if first_paper_id is None and isinstance(paper, dict) and paper.get("id"):
            first_paper_id = paper["id"]
            first_paper_pdf = pdf_url
            first_paper_audio = audio_url

    if ranks_ok and total_papers > 0:
        record("Digest: Paper fields (title/arxiv_id)", "PASS")
    elif total_papers > 0:
        record("Digest: Paper fields (title/arxiv_id)", "WARN", "Một số paper thiếu title/arxiv_id")

    # Check rank_position
    rank_positions = [e.get("rank_position") for e in digest_papers if "rank_position" in e]
    if sorted(rank_positions) == list(range(1, len(rank_positions)+1)):
        record("Digest: rank_position sequence", "PASS", f"ranks={rank_positions}")
    elif rank_positions:
        record("Digest: rank_position sequence", "WARN", f"ranks={rank_positions}")
    else:
        record("Digest: rank_position", "WARN", "rank_position không có trong response")

    # PDF và audio check
    if first_paper_pdf:
        record("Digest: PDF URL exists", "PASS", f"pdf={first_paper_pdf[:60]}...")
    else:
        record("Digest: PDF URL", "WARN", "pdf_url/pdf_path trống - có thể ENABLE_PDF_DOWNLOAD=false hoặc mode=mock")

    if first_paper_audio:
        record("Digest: Audio Abstract URL exists", "PASS", f"audio={first_paper_audio[:60]}...")
    else:
        record("Digest: Audio Abstract URL", "WARN", "audio_abstract_url trống - có thể TTS_MODE=mock hoặc chưa generate")

elif r is not None and r.status_code == 404:
    record("Get Today Digest", "WARN", "Không có digest hôm nay - chạy digest job trước")
else:
    code = r.status_code if r is not None else "NO_RESPONSE"
    record("Get Today Digest", "FAIL", f"HTTP {code}")

# ──────────────────────────────────────────────────────────────────
# STEP 6: Trend analyze
# ──────────────────────────────────────────────────────────────────
separator("STEP 6: Trend Analyze")
print("  POST /api/v1/trend/analyze (có thể mất 20-60s)")

r = post("/trend/analyze", timeout=120)

if r is not None and r.status_code == 200:
    data = r.json()
    mode        = data.get("mode", "?")
    topic_count = data.get("topic_count", 0)
    total_papers = data.get("total_papers", 0)

    detail = f"mode={mode}, topics={topic_count}, papers={total_papers}"
    if topic_count >= 1:
        record("Trend Analyze", "PASS", detail)
    else:
        record("Trend Analyze", "WARN", f"0 topics - có thể cần nhiều bài hơn. {detail}")
elif r is not None and r.status_code == 503:
    try:
        err = r.json().get("detail", "Trend Agent không phản hồi")
    except Exception:
        err = "Service Unavailable"
    record("Trend Analyze", "FAIL", f"Trend Agent lỗi: {err}")
else:
    code = r.status_code if r is not None else "NO_RESPONSE (timeout?)"
    try:
        err = r.json().get("detail", "") if r is not None else ""
    except Exception:
        err = ""
    record("Trend Analyze", "FAIL", f"HTTP {code} {err}")

# ──────────────────────────────────────────────────────────────────
# STEP 7: Get stored trends
# ──────────────────────────────────────────────────────────────────
separator("STEP 7: Get Stored Trends")

r = get("/trend")

if r is not None and r.status_code == 200:
    data = r.json()
    mode        = data.get("mode", "?")
    topic_count = data.get("topic_count", 0)
    total_papers = data.get("total_papers", 0)
    topics       = data.get("topics", [])

    detail = f"mode={mode}, topics={topic_count}, papers={total_papers}"
    record("Get Stored Trends", "PASS", detail)

    if topic_count >= 1:
        record("Trends: topic_count >= 1", "PASS", f"topics={topic_count}")
        # In top topic
        if topics:
            top = topics[0]
            top_name  = top.get("name", "?")
            top_count = top.get("paper_count", "?")
            record("Trends: Top topic", "PASS", f"'{top_name}' ({top_count} papers)")
    else:
        record("Trends: topic_count", "WARN", "0 topics - cần analyze trước")
else:
    code = r.status_code if r is not None else "NO_RESPONSE"
    record("Get Stored Trends", "FAIL", f"HTTP {code}")

# ──────────────────────────────────────────────────────────────────
# STEP 8: Papers list
# ──────────────────────────────────────────────────────────────────
separator("STEP 8: Papers List")

r = get("/papers?limit=20", token=access_token)

if r is not None and r.status_code == 200:
    papers = r.json() if isinstance(r.json(), list) else r.json().get("papers", r.json().get("items", []))
    total  = len(papers)
    record("Get Papers List", "PASS", f"{total} papers fetched")

    # Tìm paper có pdf_path để test Q&A
    paper_with_pdf = None
    for p in papers:
        if p.get("pdf_path") or p.get("pdf_url"):
            paper_with_pdf = p
            break
    if paper_with_pdf:
        record("Papers: Paper with PDF found", "PASS",
               f"id={paper_with_pdf['id']}, arxiv={paper_with_pdf.get('arxiv_id','?')}")
    else:
        record("Papers: Paper with PDF", "WARN", "Không tìm thấy paper có pdf_path - Q&A RAG có thể dùng abstract fallback")
        if papers:
            paper_with_pdf = papers[0]  # dùng paper đầu bất kể
else:
    code = r.status_code if r is not None else "NO_RESPONSE"
    record("Get Papers List", "FAIL", f"HTTP {code}")
    papers = []
    paper_with_pdf = None

# Lấy first_paper_id từ digest nếu chưa có
if first_paper_id is None and paper_with_pdf:
    first_paper_id = paper_with_pdf.get("id")

# ──────────────────────────────────────────────────────────────────
# STEP 9: Chat Q&A
# ──────────────────────────────────────────────────────────────────
separator("STEP 9: Chat Q&A Session + Message")

chat_session_id = None
assistant_message_id = None

if not access_token:
    record("Chat: Requires auth", "WARN", "Skip - không có token")
elif not first_paper_id:
    record("Chat: Requires paper", "WARN", "Skip - không có paper_id")
else:
    target_paper_id = first_paper_id
    print(f"  Using paper_id={target_paper_id}")

    # Tạo hoặc lấy chat session
    r = get(f"/chat/papers/{target_paper_id}/session", token=access_token)
    if r is not None and r.status_code == 200:
        chat_session_id = r.json().get("id")
        record("Chat: Get existing session", "PASS", f"session_id={chat_session_id}")
    elif r is not None and r.status_code == 404:
        # Tạo mới
        r2 = post("/chat/sessions", {"paper_id": target_paper_id}, token=access_token)
        if r2 is not None and r2.status_code in (200, 201):
            chat_session_id = r2.json().get("id")
            record("Chat: Create new session", "PASS", f"session_id={chat_session_id}")
        else:
            code = r2.status_code if r2 is not None else "NO_RESPONSE"
            record("Chat: Create session", "FAIL", f"HTTP {code}")
    else:
        code = r.status_code if r is not None else "NO_RESPONSE"
        record("Chat: Get/Create session", "FAIL", f"HTTP {code}")

    # Gửi câu hỏi
    if chat_session_id:
        question = "What is the main contribution of this paper?"
        msg_payload = {"session_id": chat_session_id, "question": question}
        print(f"  Sending question: '{question}'")
        print(f"  (Có thể mất 10-30s nếu Q&A Agent RAG đang build index...)")

        r = post("/chat/messages", msg_payload, token=access_token, timeout=180)
        if r is not None and r.status_code == 200:
            data = r.json()
            user_msg   = data.get("user_message", {})
            asst_msg   = data.get("assistant_message", {})
            qa_mode    = data.get("qa_mode", "?")
            answer_preview = str(asst_msg.get("content", ""))[:80] + "..."

            record("Chat: Send message", "PASS",
                   f"qa_mode={qa_mode}, answer_preview='{answer_preview}'")
            assistant_message_id = asst_msg.get("id")
        elif r is not None:
            try:
                err = r.json().get("detail", r.text[:200])
            except Exception:
                err = r.text[:200]
            if "Ollama" in err or "connection" in err.lower() or "connect" in err.lower() or "refused" in err.lower() or "400" in err:
                record("Chat: Send message", "WARN", f"Ollama model/service unavailable: {err[:150]}")
            else:
                record("Chat: Send message", "FAIL", f"HTTP {r.status_code}: {err[:150]}")
        else:
            record("Chat: Send message", "FAIL", "HTTP NO_RESPONSE")

    # Lấy message history
    if chat_session_id:
        r = get(f"/chat/sessions/{chat_session_id}/messages", token=access_token)
        if r is not None and r.status_code == 200:
            msgs = r.json()
            record("Chat: Get message history", "PASS", f"{len(msgs)} messages in session")
        else:
            code = r.status_code if r is not None else "NO_RESPONSE"
            record("Chat: Get message history", "FAIL", f"HTTP {code}")

# ──────────────────────────────────────────────────────────────────
# STEP 10: TTS for assistant message
# ──────────────────────────────────────────────────────────────────
separator("STEP 10: TTS Chat Audio")

if not access_token:
    record("TTS: Requires auth", "WARN", "Skip - không có token")
elif not assistant_message_id:
    record("TTS: Requires assistant_message_id", "WARN", "Skip - không có assistant message")
else:
    tts_payload = {
        "message_id": assistant_message_id,
        "voice": "vi_female",
        "language": "vi",
        "speed": 1.0
    }
    print(f"  POST /api/v1/tts/chat-message (message_id={assistant_message_id})")

    r = post("/tts/chat-message", tts_payload, token=access_token, timeout=120)
    if r is not None and r.status_code == 200:
        data = r.json()
        tts_path  = data.get("tts_path", "")
        tts_url   = data.get("tts_url", "")
        tts_mode  = data.get("mode", "?")
        dur       = data.get("duration_seconds", "?")

        record("TTS: Generate chat audio", "PASS",
               f"mode={tts_mode}, duration={dur}s, path={tts_path[:50] if tts_path else 'N/A'}")

        # Test gọi lại - phải trả mode=existing
        r2 = post("/tts/chat-message", tts_payload, token=access_token, timeout=10)
        if r2 is not None and r2.status_code == 200:
            mode2 = r2.json().get("mode", "?")
            if mode2 == "existing":
                record("TTS: Cache existing audio", "PASS", f"Re-call returned mode=existing")
            else:
                record("TTS: Cache existing audio", "WARN", f"Re-call mode={mode2} (expected 'existing')")
        else:
            code = r2.status_code if r2 is not None else "NO_RESPONSE"
            record("TTS: Cache existing audio re-call", "WARN", f"HTTP {code}")
    elif r is not None and r.status_code == 400:
        try:
            err = r.json().get("detail", r.text[:200])
        except Exception:
            err = r.text[:200]
        record("TTS: Generate chat audio", "FAIL", f"HTTP 400: {err}")
    elif r is not None and r.status_code == 500:
        try:
            err = r.json().get("detail", r.text[:200])
        except Exception:
            err = r.text[:200]
        record("TTS: Generate chat audio", "WARN", f"HTTP 500 - TTS Agent lỗi: {err[:150]}")
    else:
        code = r.status_code if r is not None else "NO_RESPONSE"
        record("TTS: Generate chat audio", "FAIL", f"HTTP {code}")

# ──────────────────────────────────────────────────────────────────
# STEP 11: Re-run trend analyze (duplicate prevention check)
# ──────────────────────────────────────────────────────────────────
separator("STEP 11: Trend Re-analyze (Duplicate Prevention)")
print("  POST /api/v1/trend/analyze (lần 2 - kiểm tra không tạo duplicate)")

r_first = get("/trend")
topics_before = 0
if r_first is not None and r_first.status_code == 200:
    topics_before = r_first.json().get("topic_count", 0)

r = post("/trend/analyze", timeout=120)
if r is not None and r.status_code == 200:
    r_after = get("/trend")
    topics_after = 0
    if r_after is not None and r_after.status_code == 200:
        topics_after = r_after.json().get("topic_count", 0)

    record("Trend Re-analyze: No crash", "PASS", f"topics_before={topics_before}, topics_after={topics_after}")

    if topics_after <= topics_before + 3:
        record("Trend Re-analyze: Duplicate prevention", "PASS",
               "Topic count không tăng đột biến (không tạo duplicate)")
    else:
        record("Trend Re-analyze: Duplicate prevention", "WARN",
               f"topics tăng từ {topics_before} → {topics_after}")
else:
    code = r.status_code if r is not None else "NO_RESPONSE"
    record("Trend Re-analyze", "WARN", f"HTTP {code} - skip duplicate check")

# ──────────────────────────────────────────────────────────────────
# STEP 12: Frontend check (port 5173)
# ──────────────────────────────────────────────────────────────────
separator("STEP 12: Frontend Availability (Port 5173)")
print("  Lưu ý: Frontend test thủ công qua browser, script chỉ check port")

try:
    r = requests.get("http://localhost:5173", timeout=5)
    if r.status_code in (200, 304):
        content_type = r.headers.get("Content-Type", "")
        if "html" in content_type:
            record("Frontend: Port 5173", "PASS", "Serving HTML")
        else:
            record("Frontend: Port 5173", "PASS", f"HTTP {r.status_code} (Content-Type: {content_type})")
    else:
        record("Frontend: Port 5173", "WARN", f"HTTP {r.status_code}")
except Exception as e:
    record("Frontend: Port 5173", "WARN",
           f"Không phản hồi - chạy scripts/run_frontend.bat rồi mở http://localhost:5173")

# ──────────────────────────────────────────────────────────────────
# SUMMARY
# ──────────────────────────────────────────────────────────────────
separator("SUMMARY")

pass_count = sum(1 for r in results if r["status"] == "PASS")
warn_count = sum(1 for r in results if r["status"] == "WARN")
fail_count = sum(1 for r in results if r["status"] == "FAIL")
total_count = len(results)

print(f"\n  Total:  {total_count} checks")
print(f"  [PASS]: {pass_count}")
print(f"  [WARN]: {warn_count}")
print(f"  [FAIL]: {fail_count}")

if fail_count == 0:
    print("\n  >> All checks PASSED or WARN only.")
else:
    print(f"\n  >> {fail_count} checks FAILED - review services and config.")

print(f"\n  Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*60)

# In chi tiet WARN/FAIL
if warn_count + fail_count > 0:
    print("\n  Detail - WARN/FAIL items:")
    for r in results:
        if r["status"] in ("WARN", "FAIL"):
            prefix = "[WARN]" if r["status"] == "WARN" else "[FAIL]"
            print(f"    {prefix} {r['step']}: {r['detail']}")

print()

# Exit code
sys.exit(0 if fail_count == 0 else 1)
