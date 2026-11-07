"""3. Factor Lab Page — Alpha158/360 Formula Library, Expression Evaluator & Single-Factor IC Analysis."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from qstudio.engine.qlib_bridge import ALPHA158_CATALOG, QlibBridge
from qstudio.ui.widgets.chart_widgets import ICAnalysisChartWidget, QuantileReturnChartWidget
from qstudio.ui.widgets.metric_card import MetricCard


class FactorLabPage(QWidget):
    """Interactive Factor Mining & Single-Factor IC / Stratified Quantile Return Laboratory."""

    log_requested = Signal(str, str)

    def __init__(self, bridge: QlibBridge, parent=None) -> None:
        super().__init__(parent)
        self.bridge = bridge
        self._build_ui()
        self.evaluate_current_factor()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 14)
        root.setSpacing(12)

        # Header
        hdr = QHBoxLayout()
        t_col = QVBoxLayout()
        t_col.setSpacing(2)
        title = QLabel("因子挖掘实验室 (Factor Lab & Alpha158/360 Expression Engine)")
        title.setObjectName("PageTitle")
        sub = QLabel(
            "内置 Qlib Cython 算子公式库与 DataHandlerLP 预处理器流水线 — 实时检验单因子 IC / RankIC / ICIR 与五分位多空分层收益"
        )
        sub.setObjectName("PageSubtitle")
        t_col.addWidget(title)
        t_col.addWidget(sub)
        hdr.addLayout(t_col)
        hdr.addStretch()
        root.addLayout(hdr)

        # Expression Input & DataHandler Processors Bar
        expr_card = QFrame()
        expr_card.setObjectName("CardFrame")
        expr_layout = QVBoxLayout(expr_card)
        expr_layout.setContentsMargins(12, 10, 12, 10)
        expr_layout.setSpacing(8)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Qlib 因子表达式:"))
        self.expr_input = QLineEdit("Std($close, 20) / $close")
        self.expr_input.setStyleSheet(
            "font-family: 'JetBrains Mono', 'Consolas', monospace; font-size: 13px; color: #79C0FF;"
        )
        row1.addWidget(self.expr_input, 1)

        row1.addWidget(QLabel("评估股票池:"))
        self.market_combo = QComboBox()
        self.market_combo.addItems(["csi300", "csi500", "csi100"])
        row1.addWidget(self.market_combo)

        eval_btn = QPushButton("🧪 立即评估单因子 IC 与分层净值")
        eval_btn.setObjectName("PrimaryButton")
        eval_btn.setMinimumHeight(32)
        eval_btn.clicked.connect(self.evaluate_current_factor)
        row1.addWidget(eval_btn)
        expr_layout.addLayout(row1)

        # Quick operator insert buttons + DataHandlerLP processors
        row2 = QHBoxLayout()
        row2.setSpacing(6)
        row2.addWidget(QLabel("快捷算子:"))
        for op_snippet in ["Ref($close, 5)", "Mean($close, 20)", "Std($volume, 20)", "Corr($close, $volume, 10)", "Rank($close, 20)", "Slope($close, 20)"]:
            btn = QPushButton(op_snippet)
            btn.setFixedHeight(24)
            btn.clicked.connect(lambda checked=False, s=op_snippet: self.expr_input.setText(s))
            row2.addWidget(btn)

        row2.addStretch()
        row2.addWidget(QLabel("DataHandlerLP 预处理器:"))
        self.chk_robust = QCheckBox("RobustZScoreNorm")
        self.chk_robust.setChecked(True)
        self.chk_fillna = QCheckBox("Fillna")
        self.chk_fillna.setChecked(True)
        self.chk_cszscore = QCheckBox("CSZScoreNorm (截面标准化)")
        self.chk_cszscore.setChecked(True)
        self.chk_csrank = QCheckBox("CSRankNorm (截面秩标准化)")
        row2.addWidget(self.chk_robust)
        row2.addWidget(self.chk_fillna)
        row2.addWidget(self.chk_cszscore)
        row2.addWidget(self.chk_csrank)
        expr_layout.addLayout(row2)
        root.addWidget(expr_card)

        # KPI Row for Factor IC Metrics
        kpi_grid = QGridLayout()
        kpi_grid.setSpacing(10)
        self.c_ic_mean = MetricCard("IC Mean (截面均值)", "0.0482", "Pearson IC", "IC", "#2962FF")
        self.c_rank_ic = MetricCard("Rank IC Mean (秩相关)", "0.0546", "Spearman RankIC", "RANK IC", "#00E5FF")
        self.c_icir = MetricCard("ICIR (年化信息比)", "0.785", "IC Mean / Std * √252", "STABILITY", "#8B5CF6")
        self.c_pos_ratio = MetricCard("IC > 0 胜率占比", "64.2%", "Positive IC Days", "CONSISTENCY", "#00C087")
        self.c_ls_ret = MetricCard("多空对冲年化 (Q5-Q1)", "+21.4%", "Top 20% vs Bottom 20%", "LONG-SHORT", "#FF4D4F")
        for idx, card in enumerate([self.c_ic_mean, self.c_rank_ic, self.c_icir, self.c_pos_ratio, self.c_ls_ret]):
            kpi_grid.addWidget(card, 0, idx)
        root.addLayout(kpi_grid)

        # Main Splitter: Left Alpha158 Catalog Table (36%) | Right IC & Quantile Charts (64%)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        left_card = QFrame()
        left_card.setObjectName("CardFrame")
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(12, 10, 12, 10)
        left_title = QLabel("📚 Qlib Alpha158 官方因子算子库 (点击自动载入)")
        left_title.setObjectName("SectionTitle")
        left_layout.addWidget(left_title)

        self.factor_table = QTableWidget(len(ALPHA158_CATALOG), 4)
        self.factor_table.setHorizontalHeaderLabels(["因子名", "类别", "Qlib 算子表达式", "金融学含义"])
        self.factor_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.factor_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.factor_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.factor_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.factor_table.verticalHeader().setVisible(False)
        self.factor_table.setAlternatingRowColors(True)
        self.factor_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.factor_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        for r_idx, (fname, fexpr, fcat, fdesc) in enumerate(ALPHA158_CATALOG):
            self.factor_table.setItem(r_idx, 0, QTableWidgetItem(fname))
            self.factor_table.setItem(r_idx, 1, QTableWidgetItem(fcat))
            self.factor_table.setItem(r_idx, 2, QTableWidgetItem(fexpr))
            self.factor_table.setItem(r_idx, 3, QTableWidgetItem(fdesc))

        self.factor_table.cellClicked.connect(self._on_catalog_factor_clicked)
        left_layout.addWidget(self.factor_table, 1)
        splitter.addWidget(left_card)

        # Right Charts TabWidget
        right_card = QFrame()
        right_card.setObjectName("CardFrame")
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(12, 10, 12, 10)

        self.chart_tabs = QTabWidget()
        self.ic_chart = ICAnalysisChartWidget()
        self.quantile_chart = QuantileReturnChartWidget()
        self.chart_tabs.addTab(self.ic_chart, "📊 单因子每日 IC 序列 & 累积 RankIC 曲线")
        self.chart_tabs.addTab(self.quantile_chart, "📈 五分位分层回测净值 (Q1~Q5 & Long-Short)")
        right_layout.addWidget(self.chart_tabs, 1)

        splitter.addWidget(right_card)
        splitter.setSizes([430, 770])
        root.addWidget(splitter, 1)

    def _on_catalog_factor_clicked(self, row: int, _col: int) -> None:
        expr_item = self.factor_table.item(row, 2)
        if expr_item:
            self.expr_input.setText(expr_item.text())
            self.evaluate_current_factor()

    def evaluate_current_factor(self) -> None:
        expr = self.expr_input.text().strip() or "($close-$open)/$open"
        market = self.market_combo.currentText()
        res = self.bridge.evaluate_factor_ic(expr=expr, market=market)
        m = res["metrics"]

        self.c_ic_mean.update_metric(f"{m['IC Mean']:+.4f}", f"IC Std: {m['IC Std']:.4f}")
        self.c_rank_ic.update_metric(f"{m['Rank IC Mean']:+.4f}", f"Rank ICIR: {m['Rank ICIR']:.3f}", value_color="#00E5FF")
        self.c_icir.update_metric(f"{m['ICIR']:.3f}", f"Market: {market.upper()}", value_color="#B388FF")
        self.c_pos_ratio.update_metric(f"{m['IC > 0 Ratio']:.1f}%", "Daily IC > 0 Ratio", value_color="#00C087")
        self.c_ls_ret.update_metric(f"{m['Long-Short Ann. Ret']:+.2f}%", "Q5 minus Q1 Ann.", value_color="#FF4D4F")

        self.ic_chart.update_ic(res["ic_df"])
        self.quantile_chart.update_quantiles(res["quantile_df"])
        self.log_requested.emit(
            "METRIC",
            f"[FactorLab] Evaluated `{expr}` on {market.upper()} -> "
            f"IC={m['IC Mean']:+.4f}, RankIC={m['Rank IC Mean']:+.4f}, ICIR={m['ICIR']:.3f}",
        )
