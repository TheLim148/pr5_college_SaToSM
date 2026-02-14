from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


class ArtifactProcessor:
    """Система обработки магических артефактов.

    Хранит артефакты в виде словарей:
      {"name": str, "power": int|float, "type": "magical"|"normal"}
    """

    def __init__(self):
        self.artifacts: List[Dict[str, Any]] = []

    def add_artifact(self, name, power_level, is_magical):
        """Добавляет артефакт в хранилище.

        Требования (по смыслу ТЗ в задании):
        - name: непустая строка
        - power_level: число > 0
        - type зависит от is_magical
        """
        if name is None or not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")

        if not isinstance(power_level, (int, float)):
            raise TypeError("power_level must be a number")

        if power_level <= 0:
            raise ValueError("power_level must be > 0")

        artifact = {
            "name": name,
            "power": power_level,
            "type": "magical" if bool(is_magical) else "normal",
        }
        self.artifacts.append(artifact)
        return artifact

    def calculate_total_power(self):
        """Считает суммарную магическую силу ТОЛЬКО magical-артефактов."""
        return sum(art["power"] for art in self.artifacts if art.get("type") == "magical")

    def get_most_powerful(self):
        """Возвращает самый сильный артефакт.

        - Если список пуст: возвращает None.
        - При равной силе: возвращает ПЕРВЫЙ добавленный (стабильность).
        """
        if not self.artifacts:
            return None

        max_art = self.artifacts[0]
        for art in self.artifacts[1:]:
            if art["power"] > max_art["power"]:
                max_art = art
        return max_art

    def remove_artifact(self, name):
        """Удаляет ВСЕ артефакты с данным именем.

        Возвращает количество удалённых артефактов (0, если не найдено).
        """
        if name is None:
            raise ValueError("name must not be None")

        before = len(self.artifacts)
        self.artifacts = [a for a in self.artifacts if a.get("name") != name]
        return before - len(self.artifacts)

    def get_artifacts_by_type(self, artifact_type):
        """Фильтрует артефакты по типу, без чувствительности к регистру.

        Если тип неизвестен/не найден — возвращает [].
        """
        if artifact_type is None or not isinstance(artifact_type, str):
            raise ValueError("artifact_type must be a string")

        key = artifact_type.strip().lower()
        if not key:
            raise ValueError("artifact_type must be non-empty")

        return [a for a in self.artifacts if str(a.get("type", "")).lower() == key]
