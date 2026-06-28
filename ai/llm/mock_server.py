"""Mock LLM inference service for development without GPU."""

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="ParsLex Mock LLM Inference", version="0.1.0")

MODEL_NAME = "parslex-stub-llm"


class CompletionRequest(BaseModel):
    prompt: str
    max_tokens: int = 512
    temperature: float = 0.7


class CompletionResponse(BaseModel):
    text: str
    model: str
    tokens_used: int


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "model": MODEL_NAME,
        "mode": "mock",
        "gpu_available": False,
        "note": "Replace with vLLM/TGI for production GPU inference",
    }


@app.post("/v1/completions", response_model=CompletionResponse)
def complete(req: CompletionRequest) -> CompletionResponse:
    stub = (
        f"[Mock LLM] This is a placeholder response. "
        f"In production, connect vLLM or TGI on GPU nodes. "
        f"Prompt length: {len(req.prompt)} chars."
    )
    return CompletionResponse(text=stub, model=MODEL_NAME, tokens_used=len(stub.split()))


@app.get("/v1/models")
def list_models() -> dict:
    return {"models": [{"id": MODEL_NAME, "object": "model"}]}
