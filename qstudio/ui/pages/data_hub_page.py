"""2. Data Hub Page — Qlib Binary Data Manager, Instrument Universe & K-Line Feature Browser."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from qstudio.engine.qlib_bridge import QlibBridge
from qstudio.ui.widgets.chart_widgets import KLineFeatureChartWidget


class DataHubPage(QWidget):
    """Visual interface for `qlib.init()`, `D.instruments()`, `D.features()`, and dataset management."""

    log_requested = Signal(str, str)

    def __init__(self, bridge: QlibBridge, parent=None) -> None:
        super().__init__(parent)
        self.bridge = bridge
        self._current_instrument = "SH600519"
        self._build_ui()
        self.reload_universe()
        self.refresh_kline()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 14)
        root.setSpacing(12)

        # Top Title + Data URI Configuration Bar
        hdr = QHBoxLayout()
        t_col = QVBoxLayout()
        t_col.setSpacing(2)
        title = QLabel("数据中心与特征行情浏览器 (Data Hub & D.features Explorer)")
        title.setObjectName("PageTitle")
        sub = QLabel(
            "对接 qlib.init()、D.calendar()、D.instruments() 与 D.features() — 管理本地 .bin 高性能二进制数据库与复权因子"
        )
        sub.setObjectName("PageSubtitle")
        t_col.addWidget(title)
        t_col.addWidget(sub)
        hdr.addLayout(t_col)
        hdr.addStretch()
        root.addLayout(hdr)

        # Provider URI Control Strip
        env_card = QFrame()
        env_card.setObjectName("CardFrame")
        env_bar = QHBoxLayout(env_card)
        env_bar.setContentsMargins(12, 8, 12, 8)
        env_bar.setSpacing(10)

        env_bar.addWidget(QLabel("区域 (Region):"))
        self.region_combo = QComboBox()
        self.region_combo.addItems(["REG_CN (A股市场)", "REG_US (美股市场)"])
        self.region_combo.setFixedWidth(155)
        env_bar.addWidget(self.region_combo)

        env_bar.addWidget(QLabel("provider_uri:"))
        self.uri_edit = QLineEdit(self.bridge.provider_uri)
        env_bar.addWidget(self.uri_edit, 1)

        browse_btn = QPushButton("📂 选择目录")
        browse_btn.clicked.connect(self._browse_uri)
        env_bar.addWidget(browse_btn)

        init_btn = QPushButton("🔄 重新初始化 qlib.init()")
        init_btn.setObjectName("PrimaryButton")
        init_btn.clicked.connect(self._reinit_qlib)
        env_bar.addWidget(init_btn)

        dl_btn = QPushButton("⬇️ 下载官方数据包向导")
        dl_btn.clicked.connect(self._show_download_wizard)
        env_bar.addWidget(dl_btn)

        root.addWidget(env_card)

        # Main Splitter: Left Universe Table (32%) | Right K-Line & D.features DataFrame (68%)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left Panel: Stock Universe
        left_card = QFrame()
        left_card.setObjectName("CardFrame")
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(12, 10, 12, 10)
        left_layout.setSpacing(8)

        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("股票池:"))
        self.market_combo = QComboBox()
        self.market_combo.addItems(["csi300 (沪深300)", "csi500 (中证500)", "csi100 (中证100)", "all (全市场A股)"])
        self.market_combo.currentIndexChanged.connect(self.reload_universe)
        filter_row.addWidget(self.market_combo)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 搜索代码/名称/行业...")
        self.search_edit.textChanged.connect(self._filter_universe_table)
        filter_row.addWidget(self.search_edit, 1)
        left_layout.addLayout(filter_row)

        self.inst_table = QTableWidget(0, 5)
        self.inst_table.setHorizontalHeaderLabels(["代码", "名称", "行业", "最新价", "涨跌幅"])
        self.inst_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.inst_table.verticalHeader().setVisible(False)
        self.inst_table.setAlternatingRowColors(True)
        self.inst_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.inst_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.inst_table.cellClicked.connect(self._on_instrument_selected)
        left_layout.addWidget(self.inst_table, 1)

        splitter.addWidget(left_card)

        # Right Panel: K-Line + Custom Expression Bar + Raw Features Table
        right_card = QFrame()
        right_card.setObjectName("CardFrame")
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(12, 10, 12, 10)
        right_layout.setSpacing(8)

        query_bar = QHBoxLayout()
        query_bar.addWidget(QLabel("D.features 实时算子公式:"))
        self.expr_edit = QLineEdit("Mean($close, 20) / $close - 1")
        query_bar.addWidget(self.expr_edit, 1)

        preset_combo = QComboBox()
        preset_combo.addItems(
            [
                "Mean($close, 20) / $close - 1 (20日均线乖离)",
                "($close - $open) / $open (KMID K线实体)",
                "Std($close, 20) / $close (STD20 20日波动率)",
                "Corr($close, Log($volume + 1), 20) (CORR20 量价相关)",
                "Ref($close, -2) / Ref($close, -1) - 1 (T+1 预测标签 Label)",
            ]
        )
        preset_combo.currentTextChanged.connect(self._on_preset_expr_changed)
        query_bar.addWidget(preset_combo)

        eval_btn = QPushButton("⚡ 提取特征并绘图")
        eval_btn.setObjectName("PrimaryButton")
        eval_btn.clicked.connect(self.refresh_kline)
        query_bar.addWidget(eval_btn)
        right_layout.addLayout(query_bar)

        self.right_tabs = QTabWidget()
        self.kline_widget = KLineFeatureChartWidget()
        self.right_tabs.addTab(self.kline_widget, "📊 K线 · 均线 · 成交量 · 算子副图")

        self.feature_table = QTableWidget(0, 8)
        self.feature_table.setHorizontalHeaderLabels(
            ["日期 (datetime)", "$open", "$high", "$low", "$close", "$volume", "$factor (复权)", "Custom Expr"]
        )
        self.feature_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.feature_table.verticalHeader().setVisible(False)
        self.feature_table.setAlternatingRowColors(True)
        self.feature_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.right_tabs.addTab(self.feature_table, "📋 D.features() 原始张量数据表")

        right_layout.addWidget(self.right_tabs, 1)
        splitter.addWidget(right_card)
        splitter.setSizes([380, 820])
        root.addWidget(splitter, 1)

    def reload_universe(self) -> None:
        mkt = self.market_combo.currentText().split(" ")[0]
        self._universe_df = self.bridge.get_instruments_df(mkt)
        self._populate_universe_table(self._universe_df)

    def _populate_universe_table(self, df) -> None:
        self.inst_table.setRowCount(len(df))
        for r_idx, row in df.iterrows():
            code = str(row.get("code", ""))
            name = str(row.get("name", code))
            sector = str(row.get("sector", ""))
            close = f"{row.get('close', 0.0):.2f}"
            pct = float(row.get("pct_chg", 0.0))
            pct_str = f"{pct:+.2f}%"

            vals = [code, name, sector, close, pct_str]
            for c_idx, val in enumerate(vals):
                item = QTableWidgetItem(val)
                if c_idx >= 3:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                if c_idx == 4:
                    item.setForeground(QColor("#FF4D4F" if pct >= 0 else "#00C087"))
                self.inst_table.setItem(r_idx, c_idx, item)

    def _filter_universe_table(self, keyword: str) -> None:
        kw = keyword.strip().lower()
        if not kw:
            self._populate_universe_table(self._universe_df)
            return
        mask = (
            self._universe_df["code"].str.lower().str.contains(kw)
            | self._universe_df["name"].str.lower().str.contains(kw)
            | self._universe_df["sector"].str.lower().str.contains(kw)
        )
        self._populate_universe_table(self._universe_df[mask].reset_index(drop=True))

    def _on_instrument_selected(self, row: int, _col: int) -> None:
        code_item = self.inst_table.item(row, 0)
        if code_item:
            self._current_instrument = code_item.text()
            self.refresh_kline()

    def _on_preset_expr_changed(self, text: str) -> None:
        expr = text.split(" (")[0].strip()
        self.expr_edit.setText(expr)
        self.refresh_kline()

    def refresh_kline(self) -> None:
        expr = self.expr_edit.text().strip() or "Mean($close, 20) / $close - 1"
        df = self.bridge.get_kline_and_features(
            instrument=self._current_instrument,
            custom_expr=expr,
        )
        self.kline_widget.update_chart(df, self._current_instrument, expr)

        # Populate raw feature dataframe view (latest 120 rows)
        tail_df = df.tail(120).iloc[::-1].reset_index(drop=True)
        self.feature_table.setRowCount(len(tail_df))
        cols = ["date", "open", "high", "low", "close", "volume", "factor", "custom_factor"]
        for r_idx, row in tail_df.iterrows():
            for c_idx, col_name in enumerate(cols):
                val = row[col_name]
                if col_name == "date":
                    txt = str(val)[:10]
                elif col_name == "volume":
                    txt = f"{float(val):,.0f}"
                elif col_name in ("factor", "custom_factor"):
                    txt = f"{float(val):.4f}"
                else:
                    txt = f"{float(val):.2f}"
                item = QTableWidgetItem(txt)
                if c_idx >= 1:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.feature_table.setItem(r_idx, c_idx, item)

        self.log_requested.emit(
            "INFO",
            f"[D.features] Extracted {len(df)} bars for {self._current_instrument} with expression `{expr}`.",
        )

    def _browse_uri(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "选择 Qlib 二进制数据目录 (provider_uri)", self.uri_edit.text())
        if folder:
            self.uri_edit.setText(folder)

    def _reinit_qlib(self) -> None:
        region = "cn" if self.region_combo.currentIndex() == 0 else "us"
        ok, msg = self.bridge.init_qlib(self.uri_edit.text().strip(), region)
        self.log_requested.emit("SUCCESS" if ok else "WARN", f"[qlib.init] {msg}")
        self.reload_universe()
        self.refresh_kline()

    def _show_download_wizard(self) -> None:
        uri = self.uri_edit.text().strip()
        cmd = f"python -m qlib.run.get_data qlib_data --target_dir {uri} --region cn"
        QMessageBox.information(
            self,
            "Qlib 官方数据集下载指引",
            f"<b>微软 Qlib 官方二进制行情包下载命令：</b><br><br>"
            f"<code>{cmd}</code><br><br>"
            f"或者使用社区高频更新数据源 (如 finhack / qlib_bin)：<br>"
            f"<code>wget https://github.com/chenditc/investment_data/releases/latest/download/qlib_bin.tar.gz</code><br><br>"
            f"下载解压至 <b>{uri}</b> 后点击【重新初始化 qlib.init()】即可自动切换至真实本地盘数据。",
        )
