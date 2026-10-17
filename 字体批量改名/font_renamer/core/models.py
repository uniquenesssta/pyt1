from __future__ import annotations
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class FontName:
    text: str
    name_id: int
    lang_id: int
    platform_id: int


@dataclass
class RenamePlan:
    old_path: str
    new_path: str
    font_name: str
    name_id: Optional[int]
    lang_id: Optional[int]
    status: str
    reason: str = ""

    @property
    def old_name(self) -> str:
        return os.path.basename(self.old_path)

    @property
    def new_name(self) -> str:
        return os.path.basename(self.new_path) if self.new_path else ""


