"""5. Backtest Center Page — Portfolio Strategy, Exchange Rules & Cost Sensitivity Simulator."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from qstudio.config.workflow_schema import STRATEGY_CATALOG, QlibWorkflowConfig
from qstudio.engine.qlib_bridge import BacktestResultBundle
from qstudio.ui.widgets.chart_widgets import PerformanceChartWidget
from qstudio.ui.widgets.metric_card import MetricCard


class BacktestPage(QWidget):
    """Visual configuration for `TopkDropoutStrategy`, `SimulatorExecutor`, and `exchange_kwargs`."""

    run_backtest_requested = Signal(object)  # emits QlibWorkflowConfig

    def __init__(self, config: QlibWorkflowConfig, initial_bundle: BacktestResultBundle, parent=None) -> None:
        super().__init__(parent)
        self.config = config
        self._build_ui()
        self.load_config(config)
        self.update_backtest_view(initial_bundle)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 14)
        root.setSpacing(12)

        # Header
        hdr = QHBoxLayout()
        t_col = QVBoxLayout()
        t_col.setSpacing(2)
        title = QLabel("组合策略与高频/日频回测中心 (Strategy & SimulatorExecutor)")
        title.setObjectName("PageTitle")
        sub = QLabel(
            "精细配置 TopkDropoutStrategy 选股换手规则、涨跌停限制 (limit_threshold)、开平仓佣金印花税与成交价格模式"
        )
        sub.setObjectName("PageSubtitle")
        t_col.addWidget(title)
        t_col.addWidget(sub)
        hdr.addLayout(t_col)
        hdr.addStretch()

        run_btn = QPushButton("⚡ 执行组合回测 (qlib.backtest)")
        run_btn.setObjectName("PrimaryButton")
        run_btn.setMinimumHeight(34)
        run_btn.clicked.connect(self._on_run_clicked)
        hdr.addWidget(run_btn)
        root.addLayout(hdr)

        # Splitter: Left Strategy & Exchange Form (35%) | Right Equity & Cost Comparison Chart (65%)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        left_card = QFrame()
        left_card.setObjectName("CardFrame")
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(14, 12, 14, 12)
        left_layout.setSpacing(12)

        s1 = QLabel("1️⃣ 组合选股策略配置 (qlib.contrib.strategy)")
        s1.setObjectName("SectionTitle")
        left_layout.addWidget(s1)

        f1 = QFormLayout()
        f1.setSpacing(8)
        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems(list(STRATEGY_CATALOG.keys()))
        f1.addRow("策略类名 (Strategy):", self.strategy_combo)

        self.topk_spin = QSpinBox()
        self.topk_spin.setRange(5, 300)
        self.topk_spin.setSingleStep(5)
        f1.addRow("持仓股票数量 (topk):", self.topk_spin)

        self.ndrop_spin = QSpinBox()
        self.ndrop_spin.setRange(1, 100)
        f1.addRow("每期最大调仓淘汰数 (n_drop):", self.ndrop_spin)

        self.hold_spin = QSpinBox()
        self.hold_spin.setRange(1, 60)
        f1.addRow("最短持仓天数 (hold_thresh):", self.hold_spin)

        self.tradable_chk = QCheckBox("仅交易非停牌且未涨跌停股票 (only_tradable)")
        self.tradable_chk.setChecked(True)
        f1.addRow("", self.tradable_chk)
        left_layout.addLayout(f1)

        s2 = QLabel("2️⃣ 交易所撮合与摩擦成本 (exchange_kwargs)")
        s2.setObjectName("SectionTitle")
        left_layout.addWidget(s2)

        f2 = QFormLayout()
        f2.setSpacing(8)
        self.bt_start_edit = QLineEdit()
        f2.addRow("回测开始日期 (start_time):", self.bt_start_edit)

        self.bt_end_edit = QLineEdit()
        f2.addRow("回测结束日期 (end_time):", self.bt_end_edit)

        self.bench_combo = QComboBox()
        self.bench_combo.addItems(["SH000300 (沪深300)", "SH000905 (中证500)", "SH000903 (中证100)"])
        f2.addRow("业绩基准 (benchmark):", self.bench_combo)

        self.account_spin = QDoubleSpinBox()
        self.account_spin.setRange(100_000, 10_000_000_000)
        self.account_spin.setDecimals(0)
        self.account_spin.setSingleStep(10_000_000)
        f2.addRow("初始资金 (account RMB):", self.account_spin)

        self.deal_combo = QComboBox()
        self.deal_combo.addItems(["close", "open", "vwap"])
        f2.addRow("撮合成交价 (deal_price):", self.deal_combo)

        self.limit_spin = QDoubleSpinBox()
        self.limit_spin.setRange(0.01, 0.30)
        self.limit_spin.setDecimals(3)
        self.limit_spin.setSingleStep(0.005)
        f2.addRow("涨跌停幅度限制 (limit_threshold):", self.limit_spin)

        self.open_cost_spin = QDoubleSpinBox()
        self.open_cost_spin.setRange(0.0, 0.02)
        self.open_cost_spin.setDecimals(4)
        self.open_cost_spin.setSingleStep(0.0001)
        f2.addRow("买入费率 (open_cost):", self.open_cost_spin)

        self.close_cost_spin = QDoubleSpinBox()
        self.close_cost_spin.setRange(0.0, 0.02)
        self.close_cost_spin.setDecimals(4)
        self.close_cost_spin.setSingleStep(0.0001)
        f2.addRow("卖出费率含印花税 (close_cost):", self.close_cost_spin)

        self.min_cost_spin = QDoubleSpinBox()
        self.min_cost_spin.setRange(0.0, 100.0)
        self.min_cost_spin.setDecimals(1)
        f2.addRow("最低单笔佣金 (min_cost):", self.min_cost_spin)

        left_layout.addLayout(f2)
        left_layout.addStretch()
        splitter.addWidget(left_card)

        # Right Panel: Gross vs Net Excess Comparison KPI + Chart
        right_card = QFrame()
        right_card.setObjectName("CardFrame")
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(14, 12, 14, 12)
        right_layout.setSpacing(10)

        kpi_row = QHBoxLayout()
        self.c_gross = MetricCard("扣费前年化超额 (No Cost)", "+22.8%", "Gross Alpha", "GROSS", "#00E5FF")
        self.c_net = MetricCard("扣费后年化超额 (With Cost)", "+18.4%", "Net Alpha", "NET", "#FF4D4F")
        self.c_ir = MetricCard("扣费后信息比率 (IR Net)", "1.92", "Risk-Adjusted", "SHARPE/IR", "#2962FF")
        self.c_turn = MetricCard("日均双边换手率 (Turnover)", "18.5%", "2 * n_drop / topk", "COST DRAG", "#F5A623")
        for c in [self.c_gross, self.c_net, self.c_ir, self.c_turn]:
            kpi_row.addWidget(c)
        right_layout.addLayout(kpi_row)

        self.bt_chart = PerformanceChartWidget()
        right_layout.addWidget(self.bt_chart, 1)

        splitter.addWidget(right_card)
        splitter.setSizes([410, 790])
        root.addWidget(splitter, 1)

    def load_config(self, cfg: QlibWorkflowConfig) -> None:
        self.config = cfg
        self.strategy_combo.setCurrentText(cfg.strategy_key)
        self.topk_spin.setValue(cfg.topk)
        self.ndrop_spin.setValue(cfg.n_drop)
        self.hold_spin.setValue(cfg.hold_thresh)
        self.tradable_chk.setChecked(cfg.only_tradable)
        self.bt_start_edit.setText(cfg.backtest_start)
        self.bt_end_edit.setText(cfg.backtest_end)
        self.account_spin.setValue(cfg.account_cash)
        self.deal_combo.setCurrentText(cfg.deal_price)
        self.limit_spin.setValue(cfg.limit_threshold)
        self.open_cost_spin.setValue(cfg.open_cost)
        self.close_cost_spin.setValue(cfg.close_cost)
        self.min_cost_spin.setValue(cfg.min_cost)

    def _on_run_clicked(self) -> None:
        cfg = self.config
        cfg.strategy_key = self.strategy_combo.currentText()
        cfg.topk = self.topk_spin.value()
        cfg.n_drop = self.ndrop_spin.value()
        cfg.hold_thresh = self.hold_spin.value()
        cfg.only_tradable = self.tradable_chk.isChecked()
        cfg.backtest_start = self.bt_start_edit.text().strip() or "2023-07-01"
        cfg.backtest_end = self.bt_end_edit.text().strip() or "2025-12-31"
        cfg.benchmark = self.bench_combo.currentText().split(" ")[0]
        cfg.account_cash = self.account_spin.value()
        cfg.deal_price = self.deal_combo.currentText()
        cfg.limit_threshold = self.limit_spin.value()
        cfg.open_cost = self.open_cost_spin.value()
        cfg.close_cost = self.close_cost_spin.value()
        cfg.min_cost = self.min_cost_spin.value()
        self.run_backtest_requested.emit(cfg)

    def update_backtest_view(self, bundle: BacktestResultBundle) -> None:
        m = bundle.metrics
        self.c_gross.update_metric(
            f"{m['excess_ann_gross']:+.2f}%",
            f"Gross IR: {m['information_ratio_gross']:.3f}",
            value_color="#00E5FF",
        )
        self.c_net.update_metric(
            f"{m['excess_ann_net']:+.2f}%",
            f"Max Drawdown: {m['max_drawdown']:.2f}%",
            value_color="#FF4D4F" if m["excess_ann_net"] >= 0 else "#00C087",
        )
        self.c_ir.update_metric(
            f"{m['information_ratio_net']:.3f}",
            f"Calmar Ratio: {m['calmar_ratio']:.2f}",
            value_color="#2962FF",
        )
        self.c_turn.update_metric(
            f"{m['avg_turnover']:.2f}%",
            f"Win Rate: {m['win_rate']:.1f}%",
            value_color="#F5A623",
        )
        self.bt_chart.update_performance(
            bundle.daily_df,
            title=f"Backtest Equity & Drawdown — {bundle.experiment_name} (TopK={self.config.topk}, Drop={self.config.n_drop})",
        )
