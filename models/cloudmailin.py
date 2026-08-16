from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class CloudMailinEnvelope(BaseModel):
    to: str
    from_address: str = Field(alias="from")
    helo_domain: str
    remote_ip: str
    recipients: List[str]

class CloudMailinPayload(BaseModel):
    headers: Dict[str, Any]
    envelope: CloudMailinEnvelope
    plain: Optional[str] = None
    html: Optional[str] = None
    reply_plain: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = None

    def get_subject(self) -> str:
        return self.headers.get("Subject", self.headers.get("subject", ""))

    def get_sender(self) -> str:
        return self.headers.get("From", self.headers.get("from", self.envelope.from_address))
