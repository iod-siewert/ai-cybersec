from pydantic import BaseModel
from typing import List, Dict, Any

class ScanRequest(BaseModel):
    repo_url: str
    max_files: int = 30

class ScanResponse(BaseModel):
    findings: List[Dict[str, Any]]
    count: int
