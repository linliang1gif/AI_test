"""
P2-5 Visual Regression - pixel-level visual diff service.

Directories:
  data/artifacts/visual/baselines/
  data/artifacts/visual/current/
  data/artifacts/visual/diff/
"""
import os
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

BASE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "artifacts", "visual",
)
BASELINE_DIR = os.path.join(BASE_DIR, "baselines")
CURRENT_DIR = os.path.join(BASE_DIR, "current")
DIFF_DIR = os.path.join(BASE_DIR, "diff")
DEFAULT_THRESHOLD = 0.05


@dataclass
class VisualResult:
    type: str = "screenshot_match"
    name: str = ""
    status: str = "pending"
    baseline_created: bool = False
    baseline_path: str = ""
    current_path: str = ""
    diff_path: str = ""
    diff_ratio: float = 0.0
    threshold: float = DEFAULT_THRESHOLD
    error_message: str = ""
    reason: str = ""


def _ensure_dirs():
    for d in (BASELINE_DIR, CURRENT_DIR, DIFF_DIR):
        os.makedirs(d, exist_ok=True)


def _pixel_diff(baseline_path: str, current_path: str, diff_path: str):
    """Return diff_ratio float. Generates diff image at diff_path."""
    from PIL import Image, ImageChops
    base_img = Image.open(baseline_path).convert("RGB")
    curr_img = Image.open(current_path).convert("RGB")
    if base_img.size != curr_img.size:
        curr_img = curr_img.resize(base_img.size, Image.LANCZOS)
    diff_img = ImageChops.difference(base_img, curr_img)
    diff_img.save(diff_path)
    pixels = list(diff_img.getdata())
    total = len(pixels)
    if total == 0:
        return 0.0
    changed = sum(1 for r, g, b in pixels if r + g + b > 30)
    return round(changed / total, 6)


def compare_screenshot(
    current_png_bytes: bytes,
    case_id: str,
    run_id: str,
    name: str,
    threshold: float = DEFAULT_THRESHOLD,
) -> VisualResult:
    """Core compare function called by PlaywrightEngine."""
    _ensure_dirs()
    vr = VisualResult(name=name, threshold=threshold)

    safe_name = name.replace("/", "_").replace("\\", "_")
    baseline_file = f"{case_id}_{safe_name}.png"
    baseline_path = os.path.join(BASELINE_DIR, baseline_file)
    current_file = f"{case_id}_{run_id}_{safe_name}.png"
    current_path = os.path.join(CURRENT_DIR, current_file)

    with open(current_path, "wb") as f:
        f.write(current_png_bytes)
    vr.current_path = current_path

    if not os.path.exists(baseline_path):
        import shutil
        shutil.copy2(current_path, baseline_path)
        vr.baseline_created = True
        vr.baseline_path = baseline_path
        vr.status = "baseline_created"
        vr.reason = "Baseline did not exist; created from current screenshot."
        logger.info("Baseline created: %s", baseline_path)
        return vr

    vr.baseline_path = baseline_path
    diff_file = f"{case_id}_{run_id}_{safe_name}_diff.png"
    diff_path = os.path.join(DIFF_DIR, diff_file)

    try:
        ratio = _pixel_diff(baseline_path, current_path, diff_path)
    except Exception as e:
        vr.status = "failed"
        vr.error_message = f"Diff error: {e}"
        return vr

    vr.diff_path = diff_path
    vr.diff_ratio = ratio

    if ratio <= threshold:
        vr.status = "passed"
        vr.reason = f"diff_ratio={ratio} <= threshold={threshold}"
    else:
        vr.status = "failed"
        vr.reason = f"diff_ratio={ratio} > threshold={threshold}"
        vr.error_message = (
            f"Visual diff {ratio:.4f} exceeds threshold {threshold}"
        )

    return vr
