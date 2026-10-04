from datetime import datetime
from typing import Literal

from app.core.schemas import CamelModel


class HealthResponse(CamelModel):
    status: Literal["ok"] = "ok"
    service: Literal["backend"] = "backend"
    timestamp: datetime
    database: Literal["up", "down"]
