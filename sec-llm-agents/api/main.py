from fastapi import FastAPI
from cli.repo_scan import scan_repo
from api.models import ScanRequest, ScanResponse

app = FastAPI(title="sec-llm-agents API")

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}

@app.post("/scan", response_model=ScanResponse)
def scan(req: ScanRequest) -> ScanResponse:
    findings = scan_repo(req.repo_url, req.max_files)
    return ScanResponse(findings=findings, count=len(findings))