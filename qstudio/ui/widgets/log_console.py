"""Bottom Collapsible Real-time Log Console & Task Progress Drawer."""

from __future__ import annotations

import datetime
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)


class LogConsoleDrawer(QFrame):
    """Collapsible bottom dock showing live Qlib execution logs and task progress."""

    abort_clicked = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("BottomLogDrawer")
        self._expanded = True
        self.setFixedHeight(175)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 8)
        layout.setSpacing(6)

        # Header bar
        bar = QHBoxLayout()
        bar.setContentsMargins(0, 0, 0, 0)
        bar.setSpacing(10)

        self.toggle_btn = QPushButton("▼ 实时执行终端 (Qlib Engine Console)")
        self.toggle_btn.setStyleSheet(
            "background: transparent; border: none; color: #E6EDF3; font-weight: 700; padding: 2px 4px;"
        )
        self.toggle_btn.clicked.connect(self.toggle_drawer)
        bar.addWidget(self.toggle_btn)

        self.stage_label = QLabel("Ready — Qlib Environment Standby")
        self.stage_label.setStyleSheet("color: #8B949E; font-size: 12px;")
        bar.addWidget(self.stage_label)
        bar.addStretch()

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(220)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        bar.addWidget(self.progress_bar)

        self.stop_btn = QPushButton("■ 终止任务")
        self.stop_btn.setObjectName("DangerButton")
        self.stop_btn.setFixedHeight(24)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.abort_clicked.emit)
        bar.addWidget(self.stop_btn)

        clear_btn = QPushButton("清空日志")
        clear_btn.setFixedHeight(24)
        clear_btn.clicked.connect(self.clear_logs)
        bar.addWidget(clear_btn)

        layout.addLayout(bar)

        # Log text output
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setStyleSheet(
            """
            QTextEdit {
                background-color: #080A0F;
                color: #C9D1D9;
                border: 1px solid #1B2232;
                border-radius: 5px;
                padding: 6px;
                font-family: "JetBrains Mono", "Consolas", monospace;
                font-size: 11px;
            }
            """
        )
        layout.addWidget(self.log_view)

    def toggle_drawer(self) -> None:
        self._expanded = not self._expanded
        self.log_view.setVisible(self._expanded)
        if self._expanded:
            self.setFixedHeight(175)
            self.toggle_btn.setText("▼ 实时执行终端 (Qlib Engine Console)")
        else:
            self.setFixedHeight(38)
            self.toggle_btn.setText("▲ 实时执行终端 (Qlib Engine Console)")

    def append_log(self, level: str, message: str) -> None:
        ts = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        palette = {
            "INFO": ("#58A6FF", "INFO"),
            "METRIC": ("#00E5FF", "METRIC"),
            "SUCCESS": ("#00C087", "DONE"),
            "WARN": ("#F5A623", "WARN"),
            "ERROR": ("#FF4D4F", "ERROR"),
        }
        color, tag = palette.get(level.upper(), ("#8B949E", level))
        html = (
            f'<span style="color:#586069;">[{ts}]</span> '
            f'<span style="color:{color}; font-weight:700;">[{tag:^6}]</span> '
            f'<span style="color:#E6EDF3;">{message}</span>'
        )
        self.log_view.append(html)
        sb = self.log_view.verticalScrollBar()
        sb.setValue(sb.maximum())

    def set_progress(self, value: int, stage_text: str) -> None:
        self.progress_bar.setValue(value)
        self.stage_label.setText(stage_text)

    def set_running_state(self, running: bool) -> None:
        self.stop_btn.setEnabled(running)
        if running and not self._expanded:
            self.toggle_drawer()

    def clear_logs(self) -> None:
        self.log_view.clear()
