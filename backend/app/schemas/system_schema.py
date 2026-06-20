from pydantic import BaseModel
from typing import Optional

class DBHealthResponse(BaseModel):
    status: str
    database: str
    detail: Optional[str] = None
