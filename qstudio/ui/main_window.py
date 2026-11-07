"""Main Application Window for Qlib Studio Pro."""

from __future__ import annotations

from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from qstudio import __app_name__, __version__
from qstudio.config.settings import AppSettings
from qstudio.config.workflow_schema import MODEL_CATALOG, QlibWorkflowConfig
from qstudio.engine.qlib_bridge import BacktestResultBundle, QlibBridge
from qstudio.engine.worker import QlibWorkflowWorker
from qstudio.ui.pages.backtest_page import BacktestPage
from qstudio.ui.pages.dashboard_page import DashboardPage
from qstudio.ui.pages.data_hub_page import DataHubPage
from qstudio.ui.pages.experiments_page import ExperimentsPage
from qstudio.ui.pages.factor_lab_page import FactorLabPage
from qstudio.ui.pages.model_studio_page import ModelStudioPage
from qstudio.ui.pages.tearsheet_page import TearSheetPage
from qstudio.ui.theme import QUANT_DARK_QSS
from qstudio.ui.widgets.log_console import LogConsoleDrawer


class QlibStudioMainWindow(QMainWindow):
    """Commercial-grade Quantitative Research IDE Window for Microsoft Qlib."""

    def __init__(self) -> None:
        super().__init__()
        self.settings = AppSettings.load()
        self.workflow_config = QlibWorkflowConfig(
            provider_uri=self.settings.active_provider_uri,
            region=self.settings.active_region,
        )
        self.bridge = QlibBridge(
            provider_uri=self.settings.active_provider_uri,
            region=self.settings.active_region,
        )
        self.active_worker: QlibWorkflowWorker | None = None

        self.setWindowTitle(f"{__app_name__} v{__version__} — Microsoft Qlib AI Quantitative Workstation")
        icon_file = Path(__file__).resolve().parents[2] / "assets" / "icons" / "app_icon.png"
        if icon_file.exists():
            self.setWindowIcon(QIcon(str(icon_file)))
        self.resize(1520, 920)
        self.setMinimumSize(1240, 760)
        self.setStyleSheet(QUANT_DARK_QSS)

        self._build_layout()
        self._startup_logs()

    def _build_layout(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root_v = QVBoxLayout(central)
        root_v.setContentsMargins(0, 0, 0, 0)
        root_v.setSpacing(0)

        # 1. Top Header Bar
        top_bar = QFrame()
        top_bar.setObjectName("TopHeaderBar")
        top_bar.setFixedHeight(50)
        top_h = QHBoxLayout(top_bar)
        top_h.setContentsMargins(16, 0, 16, 0)
        top_h.setSpacing(10)

        icon_file = Path(__file__).resolve().parents[2] / "assets" / "icons" / "app_icon.png"
        if icon_file.exists():
            logo_icon_lbl = QLabel()
            pix = QPixmap(str(icon_file)).scaled(
                28, 28, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            logo_icon_lbl.setPixmap(pix)
            top_h.addWidget(logo_icon_lbl)

        brand_lbl = QLabel(
            f"<span style='color:#FFFFFF;font-size:16px;font-weight:800;'>QLIB STUDIO</span> "
            f"<span style='color:#00E5FF;font-size:11px;font-weight:700;'>v{__version__}</span>"
        )
        top_h.addWidget(brand_lbl)

        sep = QLabel("|")
        sep.setStyleSheet("color: #283147;")
        top_h.addWidget(sep)

        env_info = self.bridge.detect_environment()
        mode_tag = "LOCAL BIN READY" if env_info["data_ready"] else "SMART QUANT SIMULATOR"
        mode_color = "#00C087" if env_info["data_ready"] else "#00E5FF"
        self.env_badge = QLabel(
            f"● 引擎: {env_info['qlib_version']}  |  区域: REG_{self.settings.active_region.upper()}  |  状态: {mode_tag}"
        )
        self.env_badge.setStyleSheet(
            f"background-color: #141B2D; color: {mode_color}; border: 1px solid #263354; "
            "border-radius: 5px; padding: 4px 10px; font-size: 11px; font-weight: 600;"
        )
        top_h.addWidget(self.env_badge)
        top_h.addStretch()

        quick_train_btn = QPushButton("▶ 一键运行当前 Qlib 工作流")
        quick_train_btn.setObjectName("SuccessButton")
        quick_train_btn.setFixedHeight(30)
        quick_train_btn.clicked.connect(lambda: self.start_workflow_execution(self.workflow_config))
        top_h.addWidget(quick_train_btn)

        root_v.addWidget(top_bar)

        # 2. Body Area: Left Sidebar Navigation + Center Workspace Stack
        body_h = QHBoxLayout()
        body_h.setContentsMargins(0, 0, 0, 0)
        body_h.setSpacing(0)

        # Left Navigation Bar
        nav_frame = QFrame()
        nav_frame.setObjectName("LeftNavigationBar")
        nav_frame.setFixedWidth(210)
        nav_v = QVBoxLayout(nav_frame)
        nav_v.setContentsMargins(0, 10, 0, 12)
        nav_v.setSpacing(2)

        nav_items = [
            ("📊  投研总览  Dashboard", 0),
            ("🗄️  数据中心  Data Hub", 1),
            ("🧪  因子实验室 Factor Lab", 2),
            ("🧠  模型工坊  Model Studio", 3),
            ("⚡  策略回测  Backtest", 4),
            ("📈  绩效归因  TearSheet", 5),
            ("🗂️  实验记录  Recorder (R)", 6),
        ]
        self.nav_buttons: list[QPushButton] = []
        for label, idx in nav_items:
            btn = QPushButton(label)
            btn.setObjectName("NavButton")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, i=idx: self.switch_page(i))
            nav_v.addWidget(btn)
            self.nav_buttons.append(btn)

        nav_v.addStretch()

        # Sidebar Footer Card
        footer_box = QFrame()
        footer_box.setStyleSheet(
            "background-color: #121724; border: 1px solid #1E263B; border-radius: 6px; margin: 8px;"
        )
        fl = QVBoxLayout(footer_box)
        fl.setContentsMargins(10, 8, 10, 8)
        fl.setSpacing(3)
        fl.addWidget(QLabel("<b style='color:#79C0FF;font-size:11px;'>Microsoft Qlib Pipeline</b>"))
        fl.addWidget(
            QLabel(
                "<span style='color:#8B949E;font-size:10px;'>"
                "DataHandlerLP → DatasetH → Model.fit → SignalRecord → PortAnaRecord"
                "</span>"
            )
        )
        nav_v.addWidget(footer_box)
        body_h.addWidget(nav_frame)

        # Center Stacked Pages + Bottom Collapsible Log Console
        center_v = QVBoxLayout()
        center_v.setContentsMargins(0, 0, 0, 0)
        center_v.setSpacing(0)

        self.stack = QStackedWidget()
        self.page_dashboard = DashboardPage(self.bridge)
        self.page_data_hub = DataHubPage(self.bridge)
        self.page_factor_lab = FactorLabPage(self.bridge)
        self.page_model_studio = ModelStudioPage(self.workflow_config)
        self.page_model_studio.loss_chart.set_history(self.bridge.latest_experiment.loss_history)
        self.page_backtest = BacktestPage(self.workflow_config, self.bridge.latest_experiment)
        self.page_tearsheet = TearSheetPage(self.bridge)
        self.page_experiments = ExperimentsPage(self.bridge)

        for page in [
            self.page_dashboard,
            self.page_data_hub,
            self.page_factor_lab,
            self.page_model_studio,
            self.page_backtest,
            self.page_tearsheet,
            self.page_experiments,
        ]:
            self.stack.addWidget(page)

        center_v.addWidget(self.stack, 1)

        # Bottom Log Console Drawer
        self.log_drawer = LogConsoleDrawer()
        self.log_drawer.abort_clicked.connect(self.abort_active_workflow)
        center_v.addWidget(self.log_drawer)

        body_h.addLayout(center_v, 1)
        root_v.addLayout(body_h, 1)

        # Wire Cross-Page Signals
        self.page_dashboard.template_launched.connect(self._on_template_launched)
        self.page_dashboard.inspect_experiment_requested.connect(self._open_bundle_in_tearsheet)
        self.page_data_hub.log_requested.connect(self.log_drawer.append_log)
        self.page_factor_lab.log_requested.connect(self.log_drawer.append_log)
        self.page_model_studio.log_requested.connect(self.log_drawer.append_log)
        self.page_model_studio.run_workflow_requested.connect(self.start_workflow_execution)
        self.page_backtest.run_backtest_requested.connect(self.start_workflow_execution)
        self.page_experiments.open_in_tearsheet_requested.connect(self._open_bundle_in_tearsheet)

        self.switch_page(0)

    def switch_page(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setProperty("active", "true" if i == index else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _startup_logs(self) -> None:
        ok, msg = self.bridge.init_qlib()
        self.log_drawer.append_log("INFO", f"{__app_name__} v{__version__} initialized.")
        self.log_drawer.append_log("SUCCESS" if ok else "INFO", f"[qlib.init] {msg}")
        self.log_drawer.append_log(
            "INFO",
            f"[QlibRecorder] Loaded {len(self.bridge.experiments)} benchmark experiments into memory.",
        )

    def _on_template_launched(self, tpl: dict) -> None:
        model_key = tpl["model_key"]
        meta = MODEL_CATALOG.get(model_key, MODEL_CATALOG["LightGBM (GBDT)"])
        self.workflow_config.experiment_name = f"{tpl['market']}_{meta['class'].lower()}_{tpl['handler'].lower()}"
        self.workflow_config.model_key = model_key
        self.workflow_config.model_kwargs = dict(meta["default_kwargs"])
        self.workflow_config.handler_class = tpl["handler"]
        self.workflow_config.market = tpl["market"]
        self.workflow_config.benchmark = tpl["benchmark"]

        self.page_model_studio.load_config_into_ui(self.workflow_config)
        self.page_backtest.load_config(self.workflow_config)
        self.switch_page(3)  # Switch to Model Studio to watch live loss curve & YAML
        self.start_workflow_execution(self.workflow_config)

    def start_workflow_execution(self, config: QlibWorkflowConfig) -> None:
        if self.active_worker is not None and self.active_worker.isRunning():
            self.log_drawer.append_log("WARN", "A Qlib workflow is already running. Please wait or abort it first.")
            return

        self.page_model_studio.loss_chart.reset_chart()
        self.log_drawer.set_running_state(True)

        self.active_worker = QlibWorkflowWorker(self.bridge, config, self)
        self.active_worker.log_emitted.connect(self.log_drawer.append_log)
        self.active_worker.progress_changed.connect(self.log_drawer.set_progress)
        self.active_worker.epoch_metric_emitted.connect(self.page_model_studio.loss_chart.append_point)
        self.active_worker.workflow_completed.connect(self._on_workflow_completed)
        self.active_worker.workflow_failed.connect(self._on_workflow_failed)
        self.active_worker. finished.connect(lambda: self.log_drawer.set_running_state(False))
        self.active_worker.start()

    def abort_active_workflow(self) -> None:
        if self.active_worker is not None and self.active_worker.isRunning():
            self.active_worker.request_abort()

    def _on_workflow_completed(self, bundle: BacktestResultBundle) -> None:
        self.page_dashboard.refresh_from_bundle(bundle)
        self.page_backtest.update_backtest_view(bundle)
        self.page_tearsheet.refresh_experiment_selector(select_bundle=bundle)
        self.page_experiments.refresh_experiments()

    def _on_workflow_failed(self, err_msg: str) -> None:
        self.log_drawer.set_progress(0, f"Workflow failed: {err_msg}")

    def _open_bundle_in_tearsheet(self, bundle: BacktestResultBundle) -> None:
        self.page_tearsheet.refresh_experiment_selector(select_bundle=bundle)
        self.switch_page(5)
