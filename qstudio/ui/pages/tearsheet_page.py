"""6. TearSheet & Portfolio Attribution Page — PortAnaRecord, Monthly Heatmap & Holdings Inspector."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from qstudio.engine.qlib_bridge import BacktestResultBundle, QlibBridge
from qstudio.ui.widgets.chart_widgets import (
    ICAnalysisChartWidget,
    PerformanceChartWidget,
    QuantileReturnChartWidget,
)


class TearSheetPage(QWidget):
    """Comprehensive post-trade analytics matching `qlib.contrib.report.analysis_position` & `analysis_model`."""

    def __init__(self, bridge: QlibBridge, parent=None) -> None:
        super().__init__(parent)
        self.bridge = bridge
        self._build_ui()
        self.refresh_experiment_selector()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 14)
        root.setSpacing(12)

        # Header
        hdr = QHBoxLayout()
        t_col = QVBoxLayout()
        t_col.setSpacing(2)
        title = QLabel("绩效归因与组合持仓看板 (Portfolio TearSheet & Attribution)")
        title.setObjectName("PageTitle")
        sub = QLabel(
            "全面替代 Jupyter Notebook 静态分析 — 交互式检视 PortAnaRecord 超额净值、月度收益热力矩阵、分层回测与持仓明细"
        )
        sub.setObjectName("PageSubtitle")
        t_col.addWidget(title)
        t_col.addWidget(sub)
        hdr.addLayout(t_col)
        hdr.addStretch()

        hdr.addWidget(QLabel("当前检视实验:"))
        self.exp_combo = QComboBox()
        self.exp_combo.setMinimumWidth(260)
        self.exp_combo.currentIndexChanged.connect(self._on_exp_combo_changed)
        hdr.addWidget(self.exp_combo)
        root.addLayout(hdr)

        # Top & Bottom Vertical Splitter
        v_split = QSplitter(Qt.Orientation.Vertical)

        # Top Section: Multi-tab Interactive Charts
        chart_frame = QFrame()
        chart_frame.setObjectName("CardFrame")
        chart_layout = QVBoxLayout(chart_frame)
        chart_layout.setContentsMargins(12, 10, 12, 10)

        self.tabs = QTabWidget()
        self.perf_chart = PerformanceChartWidget()
        self.group_chart = QuantileReturnChartWidget()
        self.ic_chart = ICAnalysisChartWidget()

        self.tabs.addTab(self.perf_chart, "📈 累积超额净值与水下回撤 (report_normal_1day.pkl)")
        self.tabs.addTab(self.group_chart, "📊 预测分五分位分层收益 (Group 1 ~ Group 5)")
        self.tabs.addTab(self.ic_chart, "🧪 模型预测分截面 IC / RankIC 时序 (pred.pkl)")
        chart_layout.addWidget(self.tabs)
        v_split.addWidget(chart_frame)

        # Bottom Section: Left Monthly Excess Heatmap (48%) | Right TopK Holdings Table (52%)
        bot_split = QSplitter(Qt.Orientation.Horizontal)

        # Monthly Return Heatmap Card
        heat_card = QFrame()
        heat_card.setObjectName("CardFrame")
        heat_layout = QVBoxLayout(heat_card)
        heat_layout.setContentsMargins(12, 10, 12, 10)
        heat_title = QLabel("🗓️ 月度超额收益热力矩阵 (单位: % | Monthly Net Excess Return)")
        heat_title.setObjectName("SectionTitle")
        heat_layout.addWidget(heat_title)

        self.monthly_table = QTableWidget(0, 13)
        headers = [f"{m}月" for m in range(1, 13)] + ["YTD"]
        self.monthly_table.setHorizontalHeaderLabels(headers)
        self.monthly_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.monthly_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        heat_layout.addWidget(self.monthly_table, 1)
        bot_split.addWidget(heat_card)

        # Holdings Table Card
        pos_card = QFrame()
        pos_card.setObjectName("CardFrame")
        pos_layout = QVBoxLayout(pos_card)
        pos_layout.setContentsMargins(12, 10, 12, 10)
        pos_title = QLabel("💼 最新截面 TopK 组合持仓与调仓信号明细 (positions_normal_1day.pkl)")
        pos_title.setObjectName("SectionTitle")
        pos_layout.addWidget(pos_title)

        self.holdings_table = QTableWidget(0, 8)
        self.holdings_table.setHorizontalHeaderLabels(
            ["排名", "代码", "名称", "行业", "模型预测分 (Score)", "目标权重", "持仓天数", "调仓动作"]
        )
        self.holdings_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.holdings_table.verticalHeader().setVisible(False)
        self.holdings_table.setAlternatingRowColors(True)
        self.holdings_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        pos_layout.addWidget(self.holdings_table, 1)
        bot_split.addWidget(pos_card)

        bot_split.setSizes([580, 620])
        v_split.addWidget(bot_split)
        v_split.setSizes([410, 290])
        root.addWidget(v_split, 1)

    def refresh_experiment_selector(self, select_bundle: BacktestResultBundle | None = None) -> None:
        self.exp_combo.blockSignals(True)
        self.exp_combo.clear()
        for exp in self.bridge.experiments:
            self.exp_combo.addItem(f"{exp.experiment_name} ({exp.model_name} · {exp.market.upper()})")
        self.exp_combo.blockSignals(False)

        if select_bundle is not None:
            for idx, exp in enumerate(self.bridge.experiments):
                if exp.experiment_id == select_bundle.experiment_id:
                    self.exp_combo.setCurrentIndex(idx)
                    self.display_bundle(select_bundle)
                    return
        if self.bridge.experiments:
            self.display_bundle(self.bridge.experiments[0])

    def _on_exp_combo_changed(self, index: int) -> None:
        if 0 <= index < len(self.bridge.experiments):
            self.display_bundle(self.bridge.experiments[index])

    def display_bundle(self, bundle: BacktestResultBundle) -> None:
        self.perf_chart.update_performance(
            bundle.daily_df,
            title=f"{bundle.experiment_name} — Net Ann. Excess: {bundle.metrics['excess_ann_net']:+.2f}% | IR: {bundle.metrics['information_ratio_net']:.3f}",
        )
        self.group_chart.update_quantiles(bundle.group_df)
        self.ic_chart.update_ic(bundle.daily_df[["date", "ic", "rank_ic"]])

        # Populate Monthly Heatmap
        mat = bundle.monthly_matrix
        self.monthly_table.setRowCount(len(mat.index))
        self.monthly_table.setVerticalHeaderLabels([str(y) for y in mat.index])
        for r_idx, year in enumerate(mat.index):
            for c_idx, col in enumerate(mat.columns):
                val = float(mat.loc[year, col])
                item = QTableWidgetItem(f"{val:+.1f}")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if val > 0.05:
                    alpha = min(int(abs(val) * 22 + 35), 170)
                    item.setBackground(QBrush(QColor(255, 77, 79, alpha)))
                    item.setForeground(QBrush(QColor("#FFFFFF")))
                elif val < -0.05:
                    alpha = min(int(abs(val) * 22 + 35), 170)
                    item.setBackground(QBrush(QColor(0, 192, 135, alpha)))
                    item.setForeground(QBrush(QColor("#FFFFFF")))
                self.monthly_table.setItem(r_idx, c_idx, item)

        # Populate Holdings Table
        hdf = bundle.holdings_df
        self.holdings_table.setRowCount(len(hdf))
        for r_idx, row in hdf.iterrows():
            action = str(row["action"])
            cells = [
                f"#{int(row['rank'])}",
                str(row["instrument"]),
                str(row["name"]),
                str(row["sector"]),
                f"{float(row['pred_score']):+.4f}",
                f"{float(row['weight_pct']):.2f}%",
                f"{int(row['holding_days'])} 天",
                action,
            ]
            for c_idx, txt in enumerate(cells):
                item = QTableWidgetItem(txt)
                if c_idx in (0, 4, 5, 6):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                elif c_idx == 7:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    item.setForeground(QColor("#00E5FF" if action == "NEW BUY" else "#00C087"))
                self.holdings_table.setItem(r_idx, c_idx, item)
