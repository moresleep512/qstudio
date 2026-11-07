"""Global application settings and environment configuration for Qlib Studio."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal


@dataclass
class AppSettings:
    """User preferences and Qlib runtime environment configuration."""

    provider_uri_cn: str = str(Path.home() / ".qlib" / "qlib_data" / "cn_data")
    provider_uri_us: str = str(Path.home() / ".qlib" / "qlib_data" / "us_data")
    active_region: Literal["cn", "us"] = "cn"
    mlruns_uri: str = str(Path.cwd() / "mlruns")
    # Color scheme for financial returns: "cn" = Red Up / Green Down, "global" = Green Up / Red Down
    color_scheme: Literal["cn", "global"] = "cn"
    auto_init_qlib: bool = True
    kernels_num: int = 4
    default_market: str = "csi300"
    default_benchmark: str = "SH000300"
    recent_workflows: list[str] = field(default_factory=list)

    @property
    def active_provider_uri(self) -> str:
        return self.provider_uri_cn if self.active_region == "cn" else self.provider_uri_us

    @property
    def up_color(self) -> str:
        return "#FF4D4F" if self.color_scheme == "cn" else "#00C087"

    @property
    def down_color(self) -> str:
        return "#00C087" if self.color_scheme == "cn" else "#FF4D4F"

    def save(self, path: Path | None = None) -> None:
        target = path or (Path.home() / ".qlib" / "QStudio_settings.json")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(asdict(self), indent=2, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def load(cls, path: Path | None = None) -> AppSettings:
        target = path or (Path.home() / ".qlib" / "QStudio_settings.json")
        if target.exists():
            try:
                data = json.loads(target.read_text(encoding="utf-8"))
                valid_keys = {f.name for f in cls.__dataclass_fields__.values()}
                filtered = {k: v for k, v in data.items() if k in valid_keys}
                return cls(**filtered)
            except Exception:
                return cls()
        return cls()
