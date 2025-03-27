from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class LoggerModel(BaseModel):
    service_type: str
    service_name: str
    request_id: str
    log_level: str
    status: Optional[str]
    status_code: Optional[str]
    created_ts: datetime = None
    message: Optional[str]
    message_detailed: Optional[dict]
