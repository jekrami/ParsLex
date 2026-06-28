"""Ollama LLM client — config-driven, provider-agnostic interface."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
import yaml

ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT_DIR / "config" / "ai" / "models.yaml"


@dataclass
class TaskProfile:
    model: str
    temperature: float = 0.7
    max_tokens: int = 2048
    system_prompt: str = ""


@dataclass
class ModelsConfig:
    provider: str
    base_url: str
    timeout_seconds: int
    tasks: dict[str, TaskProfile]
    default_model: str
    default_temperature: float
    default_max_tokens: int


def load_models_config(path: Path | None = None) -> ModelsConfig:
    config_path = path or DEFAULT_CONFIG
    if not config_path.exists():
        raise FileNotFoundError(f"AI models config not found: {config_path}")

    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    ollama = raw.get("ollama", {})
    defaults = raw.get("defaults", {})
    tasks: dict[str, TaskProfile] = {}

    for task_name, task_cfg in raw.get("tasks", {}).items():
        if not isinstance(task_cfg, dict):
            continue
        tasks[task_name] = TaskProfile(
            model=task_cfg.get("model", defaults.get("model", "llama3.2")),
            temperature=float(task_cfg.get("temperature", defaults.get("temperature", 0.7))),
            max_tokens=int(task_cfg.get("max_tokens", defaults.get("max_tokens", 2048))),
            system_prompt=task_cfg.get("system_prompt", "").strip(),
        )

    return ModelsConfig(
        provider=raw.get("provider", "ollama"),
        base_url=ollama.get("base_url", "http://localhost:11434").rstrip("/"),
        timeout_seconds=int(ollama.get("timeout_seconds", 120)),
        tasks=tasks,
        default_model=defaults.get("model", "llama3.2"),
        default_temperature=float(defaults.get("temperature", 0.7)),
        default_max_tokens=int(defaults.get("max_tokens", 2048)),
    )


class OllamaClient:
    def __init__(self, config: ModelsConfig | None = None) -> None:
        self.config = config or load_models_config()

    def get_task_profile(self, task: str) -> TaskProfile:
        if task in self.config.tasks:
            return self.config.tasks[task]
        return TaskProfile(
            model=self.config.default_model,
            temperature=self.config.default_temperature,
            max_tokens=self.config.default_max_tokens,
        )

    def chat(
        self,
        task: str,
        user_message: str,
        *,
        context: str | None = None,
        history: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        profile = self.get_task_profile(task)
        messages: list[dict[str, str]] = []

        if profile.system_prompt:
            messages.append({"role": "system", "content": profile.system_prompt})
        if context:
            messages.append({"role": "system", "content": f"Context:\n{context}"})
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_message})

        payload = {
            "model": profile.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": profile.temperature,
                "num_predict": profile.max_tokens,
            },
        }

        url = f"{self.config.base_url}/api/chat"
        with httpx.Client(timeout=self.config.timeout_seconds) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

        content = data.get("message", {}).get("content", "")
        return {
            "content": content,
            "model": profile.model,
            "provider": self.config.provider,
        }

    def health(self) -> dict[str, Any]:
        url = f"{self.config.base_url}/api/tags"
        try:
            with httpx.Client(timeout=10) as client:
                response = client.get(url)
                response.raise_for_status()
                models = [m.get("name") for m in response.json().get("models", [])]
            return {"status": "ok", "provider": "ollama", "models_available": models}
        except Exception as exc:
            return {"status": "unavailable", "provider": "ollama", "error": str(exc)}
