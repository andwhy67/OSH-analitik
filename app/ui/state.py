from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import pandas as pd
from PySide6.QtCore import QObject, Signal

from app.modules.core.matrix import BinaryMatrix
from app.modules.core.optimization import OptimizationConfig, OptimizationResult


@dataclass
class ExpertSession:
    """Сессия экспертного анализа. Хранит ранжирования и/или бинарные матрицы."""

    rankings: Optional[pd.DataFrame] = None
    binary_matrices: dict[str, BinaryMatrix] = field(default_factory=dict)


class AppState(QObject):
    """Глобальное состояние приложения. Pages подписываются на сигналы."""

    matrix_changed = Signal(object)
    optimization_changed = Signal(object)
    experts_changed = Signal(object)
    config_changed = Signal(object)
    status_message = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._matrix: Optional[BinaryMatrix] = None
        self._optimization: Optional[OptimizationResult] = None
        self._experts: ExpertSession = ExpertSession()
        self._config: OptimizationConfig = OptimizationConfig()
        self._source_path: Optional[str] = None

    @property
    def matrix(self) -> Optional[BinaryMatrix]:
        return self._matrix

    def set_matrix(
        self,
        matrix: BinaryMatrix,
        source: str | None = None,
        *,
        preserve_optimization: bool = False,
    ) -> None:
        self._matrix = matrix
        self._source_path = source
        if not preserve_optimization:
            self._optimization = None
            self.optimization_changed.emit(None)
        self.matrix_changed.emit(matrix)

    @property
    def optimization(self) -> Optional[OptimizationResult]:
        return self._optimization

    def set_optimization(self, result: OptimizationResult | None) -> None:
        self._optimization = result
        self.optimization_changed.emit(result)

    @property
    def experts(self) -> ExpertSession:
        return self._experts

    def set_experts(self, session: ExpertSession) -> None:
        self._experts = session
        self.experts_changed.emit(session)

    @property
    def config(self) -> OptimizationConfig:
        return self._config

    def update_config(self, config: OptimizationConfig) -> None:
        self._config = config
        self.config_changed.emit(config)

    @property
    def source_path(self) -> Optional[str]:
        return self._source_path
