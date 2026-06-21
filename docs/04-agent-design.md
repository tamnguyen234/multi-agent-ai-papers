# 04. Thiết kế các AI Agents (Agent Design)

> **Tài liệu phiên bản**: Task 20 – Final Report  
> **Ngày cập nhật**: 2026-06-20

---

## Tổng quan

Hệ thống có 4 AI Agent chạy độc lập như microservice FastAPI. Backend Gateway orchestrate (điều phối) tất cả – Frontend **không** bao giờ gọi trực tiếp Agent.

```
Frontend → Backend Gateway → [Summarizer | Trend | Q&A | TTS] Agent
```

Mỗi Agent:
- Có endpoint `/health` trả về `{"status": "ok"}`
- Có biến môi trường `MODE` để chuyển đổi giữa `real` và `mock_fallback`
- Chạy venv riêng với requirements.txt riêng

---

## 1. Summarizer Agent (Port 8101)

### Nhiệm vụ

Thu thập các bài báo AI nổi bật từ **arXiv RSS** hàng ngày, lọc và sinh tóm tắt học thuật.

### Cấu hình

| Biến môi trường | Mô tả | Giá trị mẫu |
|---|---|---|
| `SUMMARIZER_MODE` | `real` hoặc `mock_fallback` | `mock_fallback` |
| `ARXIV_CATEGORIES` | Danh mục arXiv cần theo dõi | `cs.AI,cs.CL,cs.LG,cs.CV` |
| `ARXIV_MAX_RESULTS` | Số bài tối đa cào/ngày | `50` |
| `ARXIV_DAYS_BACK` | Số ngày nhìn lại | `2` |
| `SUMMARY_MAX_SENTENCES` | Số câu tóm tắt tối đa | `3` |
| `SUMMARY_MAX_CHARS` | Ký tự tóm tắt tối đa | `700` |

### API Endpoints nội bộ

| Method | Path | Mô tả |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/summarize` | Lấy top papers từ arXiv và tóm tắt |

### Luồng xử lý (real mode)

```
Backend POST /summarize
  ↓
Agent: feedparser → arXiv RSS Feed
  ↓
Lọc theo ARXIV_CATEGORIES, sắp xếp theo score (citations/relevance)
  ↓
Chọn top 5 papers nổi bật
  ↓
Với mỗi paper: dùng transformers (BART/T5) sinh summary
  ↓
Trả về: [{ arxiv_id, title, authors, abstract, summary, score, pdf_url }]
  ↓
Backend lưu vào DB (papers table) + tạo digest ngày hôm nay
```

### Luồng xử lý (mock_fallback mode)

```
Backend POST /summarize
  ↓
Agent trả về dữ liệu mock cố định (không gọi arXiv)
  ↓
Backend lưu mock data vào DB
```

### Ghi chú quan trọng

- Timeout gọi Summarizer: **120 giây** (vì download model nặng lần đầu)
- Mode `mock_fallback` dùng cho demo nhanh không cần model AI

---

## 2. Trend Agent (Port 8102)

### Nhiệm vụ

Phân tích cụm chủ đề (Topic Modeling) từ các abstracts bài báo đã lưu trong DB.

### Cấu hình

| Biến môi trường | Mô tả | Giá trị mẫu |
|---|---|---|
| `TREND_MODE` | `bertopic` hoặc `rule_based_fallback` | `rule_based_fallback` |
| `TREND_EMBEDDING_MODEL` | Model sentence-transformers | `all-MiniLM-L6-v2` |
| `TREND_MIN_TOPIC_SIZE` | Số paper tối thiểu mỗi topic | `2` |
| `TREND_TOP_N_WORDS` | Số từ khóa đại diện mỗi topic | `8` |
| `TREND_UMAP_N_NEIGHBORS` | UMAP neighbors | `5` |
| `TREND_HDBSCAN_MIN_CLUSTER_SIZE` | HDBSCAN min cluster | `2` |

### API Endpoints nội bộ

| Method | Path | Mô tả |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/analyze` | Nhận abstracts, trả về topic clusters |

### Luồng xử lý (bertopic mode)

```
Backend POST /analyze  (body: [{ paper_id, abstract }])
  ↓
Agent: Sentence-Transformers → vector embeddings cho mỗi abstract
  ↓
UMAP: Giảm số chiều vector (high-dim → 5D)
  ↓
HDBSCAN: Phân cụm mật độ tự động
  ↓
BERTopic: Trích xuất từ khóa đại diện mỗi cụm
  ↓
Trả về: [{ topic_name, keywords, paper_ids, confidence_scores }]
  ↓
Backend: lưu topics + paper_topics vào DB
```

### Luồng xử lý (rule_based_fallback mode)

```
Backend POST /analyze
  ↓
Agent: dùng danh sách từ khóa cố định (LLM, Vision, NLP...)
Khớp từ khóa với abstract → phân loại topic thủ công
  ↓
Trả về topic assignments (không cần model AI nặng)
```

---

## 3. Q&A Agent (Port 8103)

### Nhiệm vụ

Trả lời câu hỏi của người dùng về nội dung bài báo bằng kỹ thuật **RAG (Retrieval-Augmented Generation)**.

### Cấu hình

| Biến môi trường | Mô tả | Giá trị mẫu |
|---|---|---|
| `QA_MODE` | `real` hoặc `mock_fallback` | `mock_fallback` |
| `OLLAMA_BASE_URL` | URL Ollama LLM server | `http://localhost:11434` |
| `OLLAMA_MODEL` | Tên model Ollama sinh câu trả lời | `qwen3.5:4b` |
| `QA_EMBEDDING_MODEL` | Model embedding Ollama | `nomic-embed-text` |
| `QA_CHUNK_SIZE` | Kích thước chunk | `4000` |
| `QA_CHUNK_OVERLAP` | Độ chồng lấn chunk | `800` |
| `QA_INITIAL_K` | Số chunk lấy từ FAISS trước rerank | `6` |
| `QA_TOP_K` | Số chunk giữ lại sau rerank | `3` |
| `QA_CONTEXT_MAX_CHARS` | Giới hạn context đưa vào prompt | `5000` |
| `QA_AGENT_URL` | URL của chính agent (set trong backend) | `http://127.0.0.1:8103` |

### API Endpoints nội bộ

| Method | Path | Mô tả |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/qa/ask` | Nhận câu hỏi + paper info, trả lời RAG |

### Luồng xử lý (real mode)

```
Backend POST /qa/ask
  body: { paper_id, pdf_path, title, abstract, summary, question, arxiv_id, history }
  ↓
Q&A Agent: kiểm tra FAISS index (data/indices_v2/paper_<paper_id>/)
  │
  ├── Nếu chưa có index:
  │     pymupdf4llm: đọc PDF → extract text (Markdown)
  │     LangChain: chunk 4000/800 → Ollama nomic-embed-text → lưu FAISS index
  │
  └── Nếu đã có index: load FAISS index
  ↓
LangChain RetrievalQA:
  - Vector similarity search lấy 6 chunks
  - Rerank bằng BAAI/bge-reranker-base, chọn 3 chunks
  - Build /api/chat prompt: system prompt + context 5000 ký tự + 3 lượt history + question
  - Gọi Ollama LLM qwen3.5:4b
  ↓
Trả về: { answer, mode, sources: [{ page, content }] }
  ↓
Backend: lưu user_message + assistant_message vào DB
```

### Luồng xử lý (mock_fallback mode)

```
Backend POST /qa/ask
  ↓
Agent: trả về câu trả lời mock với mode="mock_fallback"
Không đọc PDF, không cần Ollama
```

### Lưu ý quan trọng

- FAISS index được tạo lần đầu khi user hỏi → **có thể chậm** lần đầu cho mỗi paper
- PDF phải đã được tải về `data/paper_pdf/` trước khi Q&A
- Index được cache tại `data/indices_v2/paper_<paper_id>/`
- Ollama phải chạy riêng ở cổng 11434

---

## 4. TTS Agent (Port 8104)

### Nhiệm vụ

Chuyển đổi văn bản (tóm tắt bài báo / câu trả lời chat) thành file **audio `.wav`**.

### Cấu hình

| Biến môi trường | Mô tả | Giá trị mẫu |
|---|---|---|
| `TTS_MODE` | `real` hoặc `mock_fallback` | `mock_fallback` |
| `TTS_MODEL` | Model TTS (SpeechT5/Bark/VITS) | `microsoft/speecht5_tts` |

### API Endpoints nội bộ

| Method | Path | Mô tả |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/synthesize` | Nhận text, trả về audio base64 |

### Luồng xử lý (real mode)

```
Backend POST /synthesize
  body: { text, voice, language, speed }
  ↓
TTS Agent: transformers pipeline (SpeechT5/Bark)
  text → audio waveform → .wav bytes
  ↓
Encode audio → base64 string
  ↓
Trả về: { audio_base64, file_extension, timestamps, duration_seconds, mode }
  ↓
Backend: decode base64 → lưu file .wav vào data/audio_chat_message/
Backend: cập nhật tts_path + tts_timestamps trong chat_messages DB
```

### Luồng xử lý (mock_fallback mode)

```
Backend POST /synthesize
  ↓
Agent: tạo file .wav tối giản (silence/beep) làm placeholder
Trả về base64 mock audio (không cần GPU/model nặng)
```

### Ghi chú

- Audio abstract cho bài báo: lưu tại `data/audio_abstract/`
- Audio chat message: lưu tại `data/audio_chat_message/`
- File `.wav` không commit lên Git

---

## 5. Tổng hợp Modes & Trade-offs

| Agent | Mode Real | Mode Fallback | Trade-off |
|---|---|---|---|
| Summarizer | arXiv RSS + BART/T5 | Dữ liệu mock cố định | Real cần GPU + download model |
| Trend | BERTopic (ML) | Rule-based keyword matching | Real cần 4GB+ RAM |
| Q&A | RAG + Ollama LLM | Mock answer | Real cần Ollama server + 8GB+ RAM |
| TTS | SpeechT5/Bark | Silence placeholder | Real cần GPU hoặc CPU chậm |

**Khuyến nghị cho demo:** Dùng `mock_fallback` để demo nhanh, chuyển sang `real` khi có đủ phần cứng.

---

## 6. Khởi chạy Agent

### Khởi chạy độc lập (để phát triển/debug)

Các Agent có thể được chạy cùng nhau thông qua file batch:

```cmd
scripts\run_all.bat --agents
```

Hoặc chạy thủ công bằng cách kích hoạt môi trường ảo riêng biệt của từng Agent trong thư mục `agents/<agent_name>/.venv` và chạy lệnh khởi động tương ứng.

---

*Tham khảo: [docs/02-system-architecture.md](02-system-architecture.md) | [docs/05-api-design.md](05-api-design.md)*
