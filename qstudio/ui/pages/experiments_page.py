"""7. Experiment Tracker Page — Multi-Experiment Leaderboard & Equity Curve Overlay Comparison (`qlib.workflow.R`)."""

from __future__ import annotations

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from qstudio.engine.qlib_bridge import BacktestResultBundle, QlibBridge
from qstudio.ui.widgets.chart_widgets import DateAxisItem
from qstudio.ui.widgets.code_editor import QlibCodeEditor


class ExperimentsPage(QWidget):
    """Visual experiment manager for `qlib.workflow.R` (QlibRecorder / MLflow backend)."""

    open_in_tearsheet_requested = Signal(object)  # BacktestResultBundle

    OVERLAY_COLORS = ["#2962FF", "#00C087", "#F5A623", "#FF4D4F", "#00E5FF", "#B388FF"]

    def __init__(self, bridge: QlibBridge, parent=None) -> None:
        super().__init__(parent)
        self.bridge = bridge
        self._build_ui()
        self.refresh_experiments()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 14)
        root.setSpacing(12)

        # Header
        hdr = QHBoxLayout()
        t_col = QVBoxLayout()
        t_col.setSpacing(2)
        title = QLabel("实验记录管理与多模型同屏 PK (QlibRecorder / MLflow Center)")
        title.setObjectName("PageTitle")
        sub = QLabel(
            "对接 qlib.workflow.R — 勾选多个实验同屏叠加对比扣费后超额净值曲线、risk_analysis 核心指标与 YAML 快照"
        )
        sub.setObjectName("PageSubtitle")
        t_col.addWidget(title)
        t_col.addWidget(sub)
        hdr.addLayout(t_col)
        hdr.addStretch()

        select_all_btn = QPushButton("☑️ 全选对比")
        select_all_btn.clicked.connect(self._select_all_experiments)
        hdr.addWidget(select_all_btn)

        inspect_btn = QPushButton("🔍 在归因看板中打开选中实验")
        inspect_btn.setObjectName("PrimaryButton")
        inspect_btn.clicked.connect(self._open_selected_in_tearsheet)
        hdr.addWidget(inspect_btn)
        root.addLayout(hdr)

        # Top Table: All Recorder Runs with Checkboxes
        table_card = QFrame()
        table_card.setObjectName("CardFrame")
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(12, 10, 12, 10)

        self.exp_table = QTableWidget(0, 11)
        self.exp_table.setHorizontalHeaderLabels(
            [
                "同屏对比",
                "实验 ID",
                "实验名称 (R)",
                "模型架构",
                "DataHandler",
                "股票池",
                "扣费后年化超额",
                "信息比率 IR",
                "最大回撤 MDD",
                "IC Mean",
                "ICIR",
            ]
        )
        self.exp_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.exp_table.verticalHeader().setVisible(False)
        self.exp_table.setAlternatingRowColors(True)
        self.exp_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.exp_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.exp_table.itemChanged.connect(self._update_overlay_chart)
        self.exp_table.cellClicked.connect(self._on_row_clicked)
        table_layout.addWidget(self.exp_table)
        root.addWidget(table_card, 38)

        # Bottom Splitter: Multi-Experiment Equity Overlay Chart (65%) | Experiment YAML Snapshot (35%)
        bot_split = QSplitter(Qt.Orientation.Horizontal)

        chart_card = QFrame()
        chart_card.setObjectName("CardFrame")
        chart_layout = QVBoxLayout(chart_card)
        chart_layout.setContentsMargins(12, 10, 12, 10)
        chart_title = QLabel("📈 多实验扣费后累积超额收益同屏 PK (Excess Return With Cost Overlay)")
        chart_title.setObjectName("SectionTitle")
        chart_layout.addWidget(chart_title)

        self.glw = pg.GraphicsLayoutWidget()
        self.glw.setBackground("#131722")
        self.date_axis = DateAxisItem("bottom")
        self.overlay_plot = self.glw.addPlot(row=0, col=0, axisItems={"bottom": self.date_axis})
        self.overlay_plot.showGrid(x=True, y=True, alpha=0.2)
        self.overlay_plot.setLabel("left", "Net Excess Return (%)")
        self.overlay_plot.addLegend(offset=(12, 10), labelTextSize="9pt")
        chart_layout.addWidget(self.glw, 1)
        bot_split.addWidget(chart_card)

        yaml_card = QFrame()
        yaml_card.setObjectName("CardFrame")
        yaml_layout = QVBoxLayout(yaml_card)
        yaml_layout.setContentsMargins(12, 10, 12, 10)
        yaml_title = QLabel("📄 选中实验的 YAML 配置与指标快照")
        yaml_title.setObjectName("SectionTitle")
        yaml_layout.addWidget(yaml_title)

        self.snapshot_editor = QlibCodeEditor(read_only=True)
        yaml_layout.addWidget(self.snapshot_editor, 1)
        bot_split.addWidget(yaml_card)

        bot_split.setSizes([780, 420])
        root.addWidget(bot_split, 62)

    def refresh_experiments(self) -> None:
        exps = self.bridge.experiments
        self.exp_table.blockSignals(True)
        self.exp_table.setRowCount(len(exps))

        for r_idx, exp in enumerate(exps):
            m = exp.metrics
            chk_item = QTableWidgetItem()
            chk_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            chk_item.setCheckState(Qt.CheckState.Checked if r_idx < 4 else Qt.CheckState.Unchecked)
            self.exp_table.setItem(r_idx, 0, chk_item)

            vals = [
                exp.experiment_id,
                exp.experiment_name,
                exp.model_name,
                exp.handler_name,
                exp.market.upper(),
                f"{m['excess_ann_net']:+.2f}%",
                f"{m['information_ratio_net']:.3f}",
                f"{m['max_drawdown']:.2f}%",
                f"{m['ic_mean']:+.4f}",
                f"{m['icir']:.3f}",
            ]
            for c_idx, txt in enumerate(vals, start=1):
                item = QTableWidgetItem(txt)
                if c_idx >= 6:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                if c_idx == 6:
                    item.setForeground(QColor("#FF4D4F" if m["excess_ann_net"] >= 0 else "#00C087"))
                self.exp_table.setItem(r_idx, c_idx, item)

        self.exp_table.blockSignals(False)
        self._update_overlay_chart()
        if exps:
            self._show_snapshot(exps[0])

    def _select_all_experiments(self) -> None:
        self.exp_table.blockSignals(True)
        for r in range(self.exp_table.rowCount()):
            item = self.exp_table.item(r, 0)
            if item:
                item.setCheckState(Qt.CheckState.Checked)
        self.exp_table.blockSignals(False)
        self._update_overlay_chart()

    def _update_overlay_chart(self) -> None:
        self.overlay_plot.clear()
        exps = self.bridge.experiments
        first_dates_set = False
        for r_idx in range(self.exp_table.rowCount()):
            chk = self.exp_table.item(r_idx, 0)
            if not chk or chk.checkState() != Qt.CheckState.Checked:
                continue
            if r_idx >= len(exps):
                continue
            exp = exps[r_idx]
            df = exp.daily_df
            if not first_dates_set and not df.empty:
                self.date_axis.set_dates(df["date"].tolist())
                first_dates_set = True
            x = np.arange(len(df), dtype=float)
            y = df["excess_return_with_cost"].to_numpy(dtype=float) * 100.0
            color = self.OVERLAY_COLORS[r_idx % len(self.OVERLAY_COLORS)]
            self.overlay_plot.plot(
                x,
                y,
                pen=pg.mkPen(color, width=2.2),
                name=f"{exp.experiment_name} ({exp.metrics['excess_ann_net']:+.1f}%, IR={exp.metrics['information_ratio_net']:.2f})",
            )
        self.overlay_plot.enableAutoRange()

    def _on_row_clicked(self, row: int, _col: int) -> None:
        if 0 <= row < len(self.bridge.experiments):
            self._show_snapshot(self.bridge.experiments[row])

    def _show_snapshot(self, exp: BacktestResultBundle) -> None:
        m = exp.metrics
        summary = (
            f"# Experiment ID: {exp.experiment_id} | Timestamp: {exp.timestamp}\n"
            f"# Experiment Name: {exp.experiment_name}\n"
            f"# Model: {exp.model_name} | Handler: {exp.handler_name}\n"
            f"risk_analysis_metrics:\n"
            f"  excess_return_without_cost_annualized: {m['excess_ann_gross']}%\n"
            f"  excess_return_with_cost_annualized: {m['excess_ann_net']}%\n"
            f"  information_ratio_with_cost: {m['information_ratio_net']}\n"
            f"  max_drawdown: {m['max_drawdown']}%\n"
            f"  ic_mean: {m['ic_mean']}\n"
            f"  rank_ic_mean: {m['rank_ic_mean']}\n"
            f"  icir: {m['icir']}\n\n"
        )
        self.snapshot_editor.setPlainText(summary + (exp.yaml_config or "# Built-in Qlib Benchmark Preset"))

    def _open_selected_in_tearsheet(self) -> None:
        row = self.exp_table.currentRow()
        if row < 0:
            row = 0
        if 0 <= row < len(self.bridge.experiments):
            self.open_in_tearsheet_requested.emit(self.bridge.experiments[row])
