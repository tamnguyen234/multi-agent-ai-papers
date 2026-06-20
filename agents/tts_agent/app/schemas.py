from pydantic import BaseModel, Field
from typing import Optional, List, Any

class TTSRequest(BaseModel):
    text: str = Field(..., description="Văn bản cần đọc")
    voice: Optional[str] = Field("default", description="Giọng đọc")
    language: Optional[str] = Field("vi", description="Ngôn ngữ")
    speed: Optional[float] = Field(1.0, description="Tốc độ đọc")
    mode: Optional[str] = Field(None, description="Chế độ chạy (mock, real, mock_fallback)")

class TTSResponse(BaseModel):
    audio_base64: str = Field(..., description="Dữ liệu âm thanh dạng base64")
    mime_type: str = Field("audio/wav", description="Định dạng MIME")
    file_extension: str = Field(".wav", description="Phần mở rộng file (có dấu chấm)")
    duration_seconds: float = Field(..., description="Độ dài âm thanh tính theo giây")
    timestamps: Optional[List[Any]] = Field(None, description="Mốc thời gian từ")
    mode: str = Field(..., description="Chế độ thực tế chạy")
    fallback_reason: Optional[str] = Field(None, description="Lý do fallback nếu có")
