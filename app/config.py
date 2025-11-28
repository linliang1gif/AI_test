from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict


DEFAULT_BASE_URL = "https://api.deepseek.com/v1"
DEFAULT_MODEL = "deepseek-chat"
DEFAULT_CHUNK_SIZE = 3000
DEFAULT_TEMPERATURE = 0.2
DEFAULT_OCR_LANG = "ch"
DEFAULT_PROJECT_NAME = ""
DEFAULT_MODULE_NAME = ""
DEFAULT_SUBMODULE_NAME = ""


@dataclass
class Config:
    """Runtime configuration for the AI test case generator."""

    api_key: str
    base_url: str = DEFAULT_BASE_URL
    model: str = DEFAULT_MODEL
    chunk_size: int = DEFAULT_CHUNK_SIZE
    temperature: float = DEFAULT_TEMPERATURE
    output_dir: Path = Path("output")
    single_workbook: bool = True
    enable_ocr: bool = False
    ocr_lang: str = DEFAULT_OCR_LANG
    project_name: str = DEFAULT_PROJECT_NAME
    module_name: str = DEFAULT_MODULE_NAME
    submodule_name: str = DEFAULT_SUBMODULE_NAME

    def ensure_output_dir(self) -> None:
        """Create the output directory if it does not exist."""
        self.output_dir.mkdir(parents=True, exist_ok=True)


def _load_env_file(env_path: Path) -> Dict[str, str]:
    """A lightweight .env parser to avoid mandatory external deps."""
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
    """Load configuration from environment variables or .env file."""
    root = root or Path(__file__).resolve().parent.parent
    env_file = root / ".env"
    env_values = _load_env_file(env_file)

    def _get(key: str, default: str | None = None) -> str:
        return os.getenv(key, env_values.get(key, default or ""))

    api_key = _get("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("请在环境变量或 .env 中设置 DEEPSEEK_API_KEY")

    base_url = _get("DEEPSEEK_BASE_URL", DEFAULT_BASE_URL)
    model = _get("DEEPSEEK_MODEL", DEFAULT_MODEL)
    chunk_size = int(_get("CHUNK_SIZE", str(DEFAULT_CHUNK_SIZE)))
    temperature = float(_get("MODEL_TEMPERATURE", str(DEFAULT_TEMPERATURE)))
    enable_ocr = _get("ENABLE_OCR", "false").lower() in {"1", "true", "yes"}
    ocr_lang = _get("OCR_LANG", DEFAULT_OCR_LANG)
    single_workbook = _get("SINGLE_WORKBOOK", "true").lower() in {"1", "true", "yes"}
    project_name = _get("PROJECT_NAME", DEFAULT_PROJECT_NAME)
    module_name = _get("MODULE_NAME", DEFAULT_MODULE_NAME)
    submodule_name = _get("SUBMODULE_NAME", DEFAULT_SUBMODULE_NAME)

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
    config.ensure_output_dir()
    return config


