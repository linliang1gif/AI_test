from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


# ── Model Presets ────────────────────────────────────────────────────────────

MODEL_PRESETS: Dict[str, Dict[str, str]] = {
    "DeepSeek-Chat": {
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-chat",
        "env_key": "DEEPSEEK_API_KEY",
    },
    "DeepSeek-Reasoner": {
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-reasoner",
        "env_key": "DEEPSEEK_API_KEY",
    },
    "OpenAI GPT-4o": {
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o",
        "env_key": "OPENAI_API_KEY",
    },
    "OpenAI GPT-4o-mini": {
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o-mini",
        "env_key": "OPENAI_API_KEY",
    },
    "通义千问-Plus": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen-plus",
        "env_key": "DASHSCOPE_API_KEY",
    },
    "通义千问-Turbo": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen-turbo",
        "env_key": "DASHSCOPE_API_KEY",
    },
    "自定义": {
        "base_url": "",
        "model": "",
        "env_key": "",
    },
}

DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-chat"
DEFAULT_CHUNK_SIZE = 3000
DEFAULT_TEMPERATURE = 0.2
DEFAULT_OCR_LANG = "ch"


@dataclass
class Config:
    """Runtime configuration for the AI test case generator."""

    api_key: str = ""
    base_url: str = DEFAULT_BASE_URL
    model: str = DEFAULT_MODEL
    chunk_size: int = DEFAULT_CHUNK_SIZE
    temperature: float = DEFAULT_TEMPERATURE
    output_dir: Path = field(default_factory=lambda: Path("output"))
    single_workbook: bool = True
    enable_ocr: bool = False
    ocr_lang: str = DEFAULT_OCR_LANG
    project_name: str = ""
    module_name: str = ""
    submodule_name: str = ""
    model_preset: str = "DeepSeek-Chat"

    def ensure_output_dir(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def to_dict(self) -> dict:
        """Serialize for persistence (exclude api_key for security)."""
        d = asdict(self)
        d.pop("api_key", None)
        d["output_dir"] = str(self.output_dir)
        return d

    @classmethod
    def from_dict(cls, d: dict, api_key: str = "") -> "Config":
        d = d.copy()
        d["api_key"] = api_key
        if "output_dir" in d:
            d["output_dir"] = Path(d["output_dir"])
        # Remove unknown keys
        valid = {f.name for f in cls.__dataclass_fields__.values()}
        d = {k: v for k, v in d.items() if k in valid}
        return cls(**d)


# ── Settings persistence ─────────────────────────────────────────────────────

_SETTINGS_DIR = Path.home() / ".ai_testgen"
_SETTINGS_FILE = _SETTINGS_DIR / "settings.json"


def save_settings(config: Config) -> None:
    """Save config to user home directory (api_key excluded)."""
    _SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    _SETTINGS_FILE.write_text(
        json.dumps(config.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_settings() -> Optional[dict]:
    """Load saved settings from user home directory."""
    if not _SETTINGS_FILE.exists():
        return None
    try:
        return json.loads(_SETTINGS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return None


# ── .env loader ──────────────────────────────────────────────────────────────

def _load_env_file(env_path: Path) -> Dict[str, str]:
    data: Dict[str, str] = {}
    if not env_path.exists():
        return data
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip().strip('"').strip("'")
    return data


def load_config(root: Path | None = None) -> Config:
    """Load configuration: saved settings -> .env -> defaults."""
    root = root or Path(__file__).resolve().parent.parent
    env_file = root / ".env"
    env_values = _load_env_file(env_file)

    def _get(key: str, default: str = "") -> str:
        return os.getenv(key, env_values.get(key, default))

    # Try loading saved settings first
    saved = load_settings()

    api_key = _get("DEEPSEEK_API_KEY") or _get("OPENAI_API_KEY") or _get("DASHSCOPE_API_KEY")

    if saved:
        config = Config.from_dict(saved, api_key=api_key)
        # Override output_dir to be relative to project root
        if not config.output_dir.is_absolute():
            config.output_dir = (root / str(config.output_dir)).resolve()
    else:
        base_url = _get("DEEPSEEK_BASE_URL", DEFAULT_BASE_URL)
        model = _get("DEEPSEEK_MODEL", DEFAULT_MODEL)
        chunk_size = int(_get("CHUNK_SIZE", str(DEFAULT_CHUNK_SIZE)))
        temperature = float(_get("MODEL_TEMPERATURE", str(DEFAULT_TEMPERATURE)))
        enable_ocr = _get("ENABLE_OCR", "false").lower() in {"1", "true", "yes"}
        ocr_lang = _get("OCR_LANG", DEFAULT_OCR_LANG)
        single_workbook = _get("SINGLE_WORKBOOK", "true").lower() in {"1", "true", "yes"}
        project_name = _get("PROJECT_NAME", "")
        module_name = _get("MODULE_NAME", "")
        submodule_name = _get("SUBMODULE_NAME", "")
        output_dir_value = _get("OUTPUT_DIR", "output")
        output_dir = (root / output_dir_value).resolve()

        config = Config(
            api_key=api_key,
            base_url=base_url,
            model=model,
            chunk_size=chunk_size,
            temperature=temperature,
            output_dir=output_dir,
            single_workbook=single_workbook,
            enable_ocr=enable_ocr,
            ocr_lang=ocr_lang,
            project_name=project_name,
            module_name=module_name,
            submodule_name=submodule_name,
        )

    return config
