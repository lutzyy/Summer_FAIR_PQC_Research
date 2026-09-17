from datetime import datetime, timezone
from typing import Any
import uuid
from pydantic import BaseModel, Field

TOOL_OUTPUT_KEYS = ["attack_name", "crypto_detected", "attack_params", "outcome_notes"]

class RunRecord(BaseModel):
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    target:str
    crypto_detected:str | None = None
    attack_name: str
    attack_params: dict[str, Any] = {}
    outcome_notes: str = ""
