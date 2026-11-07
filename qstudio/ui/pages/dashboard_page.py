"""1. Dashboard Page — Quantitative Research Overview & Quick-Start Benchmark Templates."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from qstudio.engine.qlib_bridge import BacktestResultBundle, QlibBridge
from qstudio.ui.widgets.chart_widgets import PerformanceChartWidget
from qstudio.ui.widgets.metric_card import MetricCard


BENCHMARK_TEMPLATES = [
    {
        "title": "Alpha158 + LightGBM (CSI300 官方基线)",
        "model_key": "LightGBM (GBDT)",
        "handler": "Alpha158",
        "market": "csi300",
        "benchmark": "SH000300",
        "tag": "GBDT · 极速推荐",
        "desc": "微软 Qlib 最经典的树模型截面多因子基线，包含 158 个量价技术指标与 Top50 轮动策略。",
    },
    {
        "title": "Alpha360 + ALSTM (时序注意力深度学习)",
        "model_key": "ALSTM (Attention LSTM)",
        "handler": "Alpha360",
        "market": "csi300",
        "benchmark": "SH000300",
        "tag": "PyTorch · Sequence",
        "desc": "利用过去 60 日原始标准化量价序列与时间注意力机制捕捉个股中短期动量反转规律。",
    },
    {
        "title": "Alpha360 + HIST (概念图共享神经网络)",
        "model_key": "HIST (Graph Concept Shared)",
        "handler": "Alpha360",
        "market": "csi300",
        "benchmark": "SH000300",
        "tag": "SOTA · Graph AI",
        "desc": "建模行业概念与隐含关联图结构，挖掘板块联动效应下的超额 Alpha。",
    },
    {
        "title": "Alpha158 + DoubleEnsemble (CSI500 中证500指增)",
        "model_key": "DoubleEnsemble",
        "handler": "Alpha158",
        "market": "csi500",
        "benchmark": "SH000905",
        "tag": "Ensemble · 抗回撤",
        "desc": "样本重加权 + 特征重采样双重集成算法，在中证 500 股票池中具备高信息比率。",
    },
]


class DashboardPage(QWidget):
    """Executive overview with KPI cards, active equity curve, and 1-click Qlib workflow templates."""

    template_launched = Signal(dict)  # emits template dict to launch or configure workflow
    inspect_experiment_requested = Signal(object)  # emits BacktestResultBundle

    def __init__(self, bridge: QlibBridge, parent=None) -> None:
        super().__init__(parent)
        self.bridge = bridge
        self._build_ui()
        self.refresh_from_bundle(self.bridge.latest_experiment)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 14)
        root.setSpacing(12)

        # Page Header
        hdr = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title = QLabel("投研工作台总览 (Quant Research Dashboard)")
        title.setObjectName("PageTitle")
        sub = QLabel(
            "Microsoft Qlib 全流程 AI 量化投研中枢 — 实时监控最新实验超额净值、风险归因与官方 Benchmark 模板库"
        )
        sub.setObjectName("PageSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(sub)
        hdr.addLayout(title_box)
        hdr.addStretch()

        run_default_btn = QPushButton("⚡ 立即运行默认工作流 (qrun)")
        run_default_btn.setObjectName("PrimaryButton")
        run_default_btn.setMinimumHeight(34)
        run_default_btn.clicked.connect(lambda: self.template_launched.emit(BENCHMARK_TEMPLATES[0]))
        hdr.addWidget(run_default_btn)
        root.addLayout(hdr)

        # Row 1: 6 Financial KPI Cards
        kpi_grid = QGridLayout()
        kpi_grid.setSpacing(10)
        self.card_excess = MetricCard("扣费后年化超额", "+18.42%", "vs Benchmark", "NET ALPHA", "#FF4D4F")
        self.card_ir = MetricCard("信息比率 (IR)", "1.92", "Risk-Adjusted Alpha", "IR (NET)", "#2962FF")
        self.card_mdd = MetricCard("超额最大回撤", "-6.45%", "Peak-to-Trough", "DRAWDOWN", "#00C087")
        self.card_ic = MetricCard("截面 IC 均值", "0.0524", "RankIC: 0.0581", "Alpha158", "#00E5FF")
        self.card_icir = MetricCard("因子信息比 (ICIR)", "0.642", "IC Mean / IC Std", "SIGNAL", "#8B5CF6")
        self.card_win = MetricCard("日度超额胜率", "57.8%", "Avg Turnover: 18.2%", "WIN RATE", "#F5A623")

        cards = [self.card_excess, self.card_ir, self.card_mdd, self.card_ic, self.card_icir, self.card_win]
        for idx, card in enumerate(cards):
            kpi_grid.addWidget(card, 0, idx)
        root.addLayout(kpi_grid)

        # Row 2: Main Equity Chart (Left 62%) + Quick Start Templates & Leaderboard (Right 38%)
        mid_row = QHBoxLayout()
        mid_row.setSpacing(12)

        # Left Chart Card
        chart_card = QFrame()
        chart_card.setObjectName("CardFrame")
        chart_layout = QVBoxLayout(chart_card)
        chart_layout.setContentsMargins(12, 10, 12, 10)
        chart_hdr = QHBoxLayout()
        self.chart_title_lbl = QLabel("📈 最新策略累积超额收益与水下回撤 (PortAnaRecord)")
        self.chart_title_lbl.setObjectName("SectionTitle")
        chart_hdr.addWidget(self.chart_title_lbl)
        chart_hdr.addStretch()
        chart_layout.addLayout(chart_hdr)

        self.perf_chart = PerformanceChartWidget()
        chart_layout.addWidget(self.perf_chart, 1)
        mid_row.addWidget(chart_card, 62)

        # Right Column: Official Qlib Templates + Recent Recorder Runs
        right_col = QVBoxLayout()
        right_col.setSpacing(10)

        tpl_card = QFrame()
        tpl_card.setObjectName("CardFrame")
        tpl_layout = QVBoxLayout(tpl_card)
        tpl_layout.setContentsMargins(12, 10, 12, 10)
        tpl_layout.setSpacing(8)
        tpl_title = QLabel("🚀 Qlib 官方经典 Benchmark 模板 (一键加载/运行)")
        tpl_title.setObjectName("SectionTitle")
        tpl_layout.addWidget(tpl_title)

        for tpl in BENCHMARK_TEMPLATES:
            item_frame = QFrame()
            item_frame.setObjectName("CardFrameHover")
            item_frame.setStyleSheet(
                "QFrame { background-color: #0E131D; border: 1px solid #1E2638; border-radius: 6px; }"
                "QFrame:hover { border-color: #2962FF; background-color: #141B2D; }"
            )
            il = QHBoxLayout(item_frame)
            il.setContentsMargins(10, 7, 10, 7)
            txt_col = QVBoxLayout()
            txt_col.setSpacing(2)
            t_lbl = QLabel(f"<b>{tpl['title']}</b>  <span style='color:#00E5FF;font-size:11px;'>[{tpl['tag']}]</span>")
            d_lbl = QLabel(tpl["desc"])
            d_lbl.setStyleSheet("color: #8B949E; font-size: 11px;")
            d_lbl.setWordWrap(True)
            txt_col.addWidget(t_lbl)
            txt_col.addWidget(d_lbl)
            il.addLayout(txt_col, 1)

            launch_btn = QPushButton("加载并训练")
            launch_btn.setObjectName("PrimaryButton")
            launch_btn.setFixedWidth(88)
            launch_btn.clicked.connect(lambda checked=False, t=tpl: self.template_launched.emit(t))
            il.addWidget(launch_btn)
            tpl_layout.addWidget(item_frame)

        right_col.addWidget(tpl_card)

        # Mini Leaderboard Table
        rec_card = QFrame()
        rec_card.setObjectName("CardFrame")
        rec_layout = QVBoxLayout(rec_card)
        rec_layout.setContentsMargins(12, 10, 12, 10)
        rec_title = QLabel("🗂️ 实验记录排行榜 (qlib.workflow.R / MLflow)")
        rec_title.setObjectName("SectionTitle")
        rec_layout.addWidget(rec_title)

        self.exp_table = QTableWidget(0, 5)
        self.exp_table.setHorizontalHeaderLabels(["实验名称", "模型", "年化超额", "IR", "最大回撤"])
        self.exp_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.exp_table.verticalHeader().setVisible(False)
        self.exp_table.setAlternatingRowColors(True)
        self.exp_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.exp_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.exp_table.cellDoubleClicked.connect(self._on_exp_double_clicked)
        rec_layout.addWidget(self.exp_table)

        right_col.addWidget(rec_card, 1)
        mid_row.addLayout(right_col, 38)
        root.addLayout(mid_row, 1)

    def refresh_from_bundle(self, bundle: BacktestResultBundle) -> None:
        m = bundle.metrics
        ex_net = m["excess_ann_net"]
        self.card_excess.update_metric(
            f"{ex_net:+.2f}%",
            subtitle=f"Gross: {m['excess_ann_gross']:+.2f}% | Bench: {m['bench_ann_return']:+.2f}%",
            badge_text=bundle.market.upper(),
            value_color="#FF4D4F" if ex_net >= 0 else "#00C087",
        )
        self.card_ir.update_metric(
            f"{m['information_ratio_net']:.3f}",
            subtitle=f"Gross IR: {m['information_ratio_gross']:.3f} | Calmar: {m['calmar_ratio']:.2f}",
            badge_text="IR (NET)",
            value_color="#00E5FF",
        )
        self.card_mdd.update_metric(
            f"{m['max_drawdown']:.2f}%",
            subtitle=f"Model: {bundle.model_name[:18]}",
            badge_text="DRAWDOWN",
            value_color="#00C087",
        )
        self.card_ic.update_metric(
            f"{m['ic_mean']:.4f}",
            subtitle=f"RankIC Mean: {m['rank_ic_mean']:.4f}",
            badge_text=bundle.handler_name,
            value_color="#FFFFFF",
        )
        self.card_icir.update_metric(
            f"{m['icir']:.3f}",
            subtitle=f"Experiment: {bundle.experiment_name}",
            badge_text="SIGNAL",
            value_color="#B388FF",
        )
        self.card_win.update_metric(
            f"{m['win_rate']:.1f}%",
            subtitle=f"Daily Turnover: {m['avg_turnover']:.1f}%",
            badge_text="WIN RATE",
            value_color="#F5A623",
        )

        self.chart_title_lbl.setText(
            f"📈 策略净值归因: {bundle.experiment_name} ({bundle.model_name} · {bundle.handler_name} · {bundle.market.upper()})"
        )
        self.perf_chart.update_performance(bundle.daily_df)
        self._refresh_leaderboard()

    def _refresh_leaderboard(self) -> None:
        exps = self.bridge.experiments
        self.exp_table.setRowCount(len(exps))
        for row_idx, exp in enumerate(exps):
            m = exp.metrics
            items = [
                exp.experiment_name,
                exp.model_name.split(" ")[0],
                f"{m['excess_ann_net']:+.2f}%",
                f"{m['information_ratio_net']:.2f}",
                f"{m['max_drawdown']:.2f}%",
            ]
            for col_idx, text in enumerate(items):
                item = QTableWidgetItem(text)
                if col_idx >= 2:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                if col_idx == 2:
                    item.setForeground(QColor("#FF4D4F" if m["excess_ann_net"] >= 0 else "#00C087"))
                self.exp_table.setItem(row_idx, col_idx, item)

    def _on_exp_double_clicked(self, row: int, _col: int) -> None:
        if 0 <= row < len(self.bridge.experiments):
            bundle = self.bridge.experiments[row]
            self.refresh_from_bundle(bundle)
            self.inspect_experiment_requested.emit(bundle)
