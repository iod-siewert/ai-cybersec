from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"

class Finding(BaseModel):
    file: str = Field(..., description="Ścieżka względna pliku")
    line: int = Field(..., ge=1)
    type: str = Field(..., description="Typ podatności, np. sqli, rce, ssrf")
    severity: Severity
    desc: str
    snippet: str
    exploit: str
    fix: str
    cwe: List[str] = Field(default_factory=list)
    owasp: Optional[str] = None

class ScanResult(BaseModel):
    findings: List[Finding] = Field(default_factory=list)
