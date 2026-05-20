"""Поиск каталога с демонстрационными данными.

При запуске из исходников samples/ лежит в корне репозитория.
При запуске собранного exe PyInstaller кладёт ресурсы в `_internal/samples/`
(onedir-режим). Дополнительно workflow копирует samples/ в корень
дистрибутива рядом с exe — это самое удобное место для пользователя.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable, Optional


def candidate_dirs() -> Iterable[Path]:
    here = Path(__file__).resolve()

    # 1. собранное приложение: рядом с exe (post-build copy)
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        yield exe_dir / "samples"
        # 2. внутри _internal (стандартная папка ресурсов PyInstaller)
        meipass = Path(getattr(sys, "_MEIPASS", exe_dir))
        yield meipass / "samples"

    # 3. запуск из исходников: корень репозитория
    yield here.parent.parent.parent.parent / "samples"

    # 4. текущая рабочая директория (на случай ручного запуска)
    yield Path.cwd() / "samples"


def samples_dir() -> Optional[Path]:
    for c in candidate_dirs():
        if c.is_dir():
            return c
    return None


def sample_file(name: str) -> Optional[Path]:
    d = samples_dir()
    if d is None:
        return None
    p = d / name
    return p if p.exists() else None
