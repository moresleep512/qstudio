"""Financial KPI Metric Card Widget."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout


class MetricCard(QFrame):
    """Compact financial metric card with accent bar, primary value, badge, and subtitle."""

    def __init__(
        self,
        title: str,
        value: str = "--",
        subtitle: str = "",
        badge_text: str = "",
        accent_color: str = "#2962FF",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("CardFrame")
        self.setMinimumHeight(88)
        self._accent_color = accent_color

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 10, 14, 10)
        root.setSpacing(4)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("color: #8B949E; font-size: 11px; font-weight: 600;")
        top_row.addWidget(self.title_label)
        top_row.addStretch()

        self.badge_label = QLabel(badge_text)
        self.badge_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._apply_badge_style(accent_color, bool(badge_text))
        top_row.addWidget(self.badge_label)
        root.addLayout(top_row)

        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(
            "color: #FFFFFF; font-size: 21px; font-weight: 700; "
            "font-family: 'JetBrains Mono', 'Consolas', monospace;"
        )
        root.addWidget(self.value_label)

        self.sub_label = QLabel(subtitle)
        self.sub_label.setStyleSheet("color: #6E7681; font-size: 11px;")
        root.addWidget(self.sub_label)

    def _apply_badge_style(self, color: str, visible: bool) -> None:
        self.badge_label.setVisible(visible)
        if visible:
            self.badge_label.setStyleSheet(
                f"background-color: {color}22; color: {color}; "
                f"border: 1px solid {color}55; border-radius: 4px; "
                "padding: 1px 6px; font-size: 10px; font-weight: 700; "
                "font-family: 'JetBrains Mono', 'Consolas', monospace;"
            )

    def update_metric(
        self,
        value: str,
        subtitle: str | None = None,
        badge_text: str | None = None,
        value_color: str = "#FFFFFF",
        badge_color: str | None = None,
    ) -> None:
        self.value_label.setText(value)
        self.value_label.setStyleSheet(
            f"color: {value_color}; font-size: 21px; font-weight: 700; "
            "font-family: 'JetBrains Mono', 'Consolas', monospace;"
        )
        if subtitle is not None:
            self.sub_label.setText(subtitle)
        if badge_text is not None:
            self.badge_label.setText(badge_text)
            self._apply_badge_style(badge_color or self._accent_color, bool(badge_text))
