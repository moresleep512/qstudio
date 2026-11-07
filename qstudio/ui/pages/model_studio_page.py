"""4. Model Studio Page — Model Zoo Hyperparameter Configurator, Live Loss Curve & Bidirectional YAML Studio."""

from __future__ import annotations

from typing import Any
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from qstudio.config.workflow_schema import MODEL_CATALOG, QlibWorkflowConfig
from qstudio.ui.widgets.chart_widgets import TrainingLossChartWidget
from qstudio.ui.widgets.code_editor import QlibCodeEditor


class ModelStudioPage(QWidget):
    """Visual configurator for `qlib.contrib.model.*`, `DatasetH` segments, and live YAML synchronization."""

    run_workflow_requested = Signal(object)  # emits QlibWorkflowConfig
    log_requested = Signal(str, str)

    def __init__(self, config: QlibWorkflowConfig, parent=None) -> None:
        super().__init__(parent)
        self.config = config
        self._updating_ui = False
        self._build_ui()
        self.load_config_into_ui(self.config)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 14)
        root.setSpacing(12)

        # Header
        hdr = QHBoxLayout()
        t_col = QVBoxLayout()
        t_col.setSpacing(2)
        title = QLabel("模型训练工坊与 YAML 编排器 (Model Zoo & Workflow Builder)")
        title.setObjectName("PageTitle")
        sub = QLabel(
            "对接 qlib.contrib.model.* 与 DatasetH — 可视化超参数表单 ⇄ 标准 qrun YAML 双向实时同步，实时监控训练收敛"
        )
        sub.setObjectName("PageSubtitle")
        t_col.addWidget(title)
        t_col.addWidget(sub)
        hdr.addLayout(t_col)
        hdr.addStretch()

        import_btn = QPushButton("📂 导入 YAML")
        import_btn.clicked.connect(self._import_yaml)
        hdr.addWidget(import_btn)

        export_btn = QPushButton("💾 导出 qrun YAML")
        export_btn.clicked.connect(self._export_yaml)
        hdr.addWidget(export_btn)

        self.train_btn = QPushButton("🚀 启动 Qlib 模型训练与回测流水线")
        self.train_btn.setObjectName("PrimaryButton")
        self.train_btn.setMinimumHeight(34)
        self.train_btn.clicked.connect(self._trigger_run)
        hdr.addWidget(self.train_btn)
        root.addLayout(hdr)

        # 3-Column Splitter: Left Config Form (35%) | Center Hyperparams & Loss Curve (33%) | Right Live YAML (32%)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Column 1: DatasetH & Model Selection
        left_card = QFrame()
        left_card.setObjectName("CardFrame")
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(14, 12, 14, 12)
        left_layout.setSpacing(10)

        sec1 = QLabel("1️⃣ 实验与数据集切分 (DatasetH & DataHandlerLP)")
        sec1.setObjectName("SectionTitle")
        left_layout.addWidget(sec1)

        form = QFormLayout()
        form.setSpacing(8)
        self.exp_name_edit = QLineEdit()
        self.exp_name_edit.textChanged.connect(self._sync_ui_to_config)
        form.addRow("实验名称 (R.start):", self.exp_name_edit)

        self.market_combo = QComboBox()
        self.market_combo.addItems(["csi300", "csi500", "csi100", "all"])
        self.market_combo.currentTextChanged.connect(self._sync_ui_to_config)
        form.addRow("股票池 (instruments):", self.market_combo)

        self.handler_combo = QComboBox()
        self.handler_combo.addItems(["Alpha158", "Alpha360"])
        self.handler_combo.currentTextChanged.connect(self._sync_ui_to_config)
        form.addRow("特征库 (DataHandler):", self.handler_combo)

        self.label_edit = QLineEdit()
        self.label_edit.textChanged.connect(self._sync_ui_to_config)
        form.addRow("预测目标 (Label Expr):", self.label_edit)

        self.train_seg_edit = QLineEdit()
        self.train_seg_edit.textChanged.connect(self._sync_ui_to_config)
        form.addRow("训练集 (segments.train):", self.train_seg_edit)

        self.valid_seg_edit = QLineEdit()
        self.valid_seg_edit.textChanged.connect(self._sync_ui_to_config)
        form.addRow("验证集 (segments.valid):", self.valid_seg_edit)

        self.test_seg_edit = QLineEdit()
        self.test_seg_edit.textChanged.connect(self._sync_ui_to_config)
        form.addRow("测试集 (segments.test):", self.test_seg_edit)

        left_layout.addLayout(form)

        sec2 = QLabel("2️⃣ 选择模型架构 (qlib.contrib.model)")
        sec2.setObjectName("SectionTitle")
        left_layout.addWidget(sec2)

        self.model_combo = QComboBox()
        self.model_combo.addItems(list(MODEL_CATALOG.keys()))
        self.model_combo.currentTextChanged.connect(self._on_model_changed)
        left_layout.addWidget(self.model_combo)

        self.model_desc_lbl = QLabel()
        self.model_desc_lbl.setWordWrap(True)
        self.model_desc_lbl.setStyleSheet(
            "background-color: #0E131D; border: 1px solid #1E2638; border-radius: 6px; "
            "padding: 8px; color: #8B949E; font-size: 12px;"
        )
        left_layout.addWidget(self.model_desc_lbl)
        left_layout.addStretch()
        splitter.addWidget(left_card)

        # Column 2: Dynamic Hyperparameters Table + Live Training Loss Plot
        mid_card = QFrame()
        mid_card.setObjectName("CardFrame")
        mid_layout = QVBoxLayout(mid_card)
        mid_layout.setContentsMargins(14, 12, 14, 12)
        mid_layout.setSpacing(8)

        hp_hdr = QHBoxLayout()
        hp_title = QLabel("3️⃣ 模型超参数矩阵 (model.kwargs)")
        hp_title.setObjectName("SectionTitle")
        hp_hdr.addWidget(hp_title)
        hp_hdr.addStretch()
        reset_hp_btn = QPushButton("重置默认超参")
        reset_hp_btn.setFixedHeight(24)
        reset_hp_btn.clicked.connect(self._reset_model_hyperparams)
        hp_hdr.addWidget(reset_hp_btn)
        mid_layout.addLayout(hp_hdr)

        self.hp_table = QTableWidget(0, 2)
        self.hp_table.setHorizontalHeaderLabels(["超参数名 (Parameter)", "参数值 (Value - 双击可编辑)"])
        self.hp_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.hp_table.verticalHeader().setVisible(False)
        self.hp_table.setAlternatingRowColors(True)
        self.hp_table.itemChanged.connect(self._on_hp_table_edited)
        mid_layout.addWidget(self.hp_table, 45)

        loss_title = QLabel("📉 训练与验证集实时收敛曲线 (Model.fit Epoch Loss)")
        loss_title.setObjectName("SectionTitle")
        mid_layout.addWidget(loss_title)

        self.loss_chart = TrainingLossChartWidget()
        mid_layout.addWidget(self.loss_chart, 55)
        splitter.addWidget(mid_card)

        # Column 3: Bidirectional YAML Editor
        right_card = QFrame()
        right_card.setObjectName("CardFrame")
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(14, 12, 14, 12)
        right_layout.setSpacing(8)

        yaml_hdr = QHBoxLayout()
        yaml_title = QLabel("4️⃣ 标准 qrun YAML 配置文件 (双向实时同步)")
        yaml_title.setObjectName("SectionTitle")
        yaml_hdr.addWidget(yaml_title)
        yaml_hdr.addStretch()

        apply_yaml_btn = QPushButton("◀ 解析 YAML 到左侧表单")
        apply_yaml_btn.setFixedHeight(24)
        apply_yaml_btn.clicked.connect(self._parse_yaml_to_ui)
        yaml_hdr.addWidget(apply_yaml_btn)
        right_layout.addLayout(yaml_hdr)

        self.yaml_editor = QlibCodeEditor()
        right_layout.addWidget(self.yaml_editor, 1)
        splitter.addWidget(right_card)

        splitter.setSizes([380, 420, 400])
        root.addWidget(splitter, 1)

    def load_config_into_ui(self, cfg: QlibWorkflowConfig) -> None:
        self._updating_ui = True
        self.config = cfg
        self.exp_name_edit.setText(cfg.experiment_name)
        self.market_combo.setCurrentText(cfg.market)
        self.handler_combo.setCurrentText(cfg.handler_class)
        self.label_edit.setText(cfg.label_expr)
        self.label_edit.setCursorPosition(0)
        self.train_seg_edit.setText(f"{cfg.train_start} ~ {cfg.train_end}")
        self.train_seg_edit.setCursorPosition(0)
        self.valid_seg_edit.setText(f"{cfg.valid_start} ~ {cfg.valid_end}")
        self.valid_seg_edit.setCursorPosition(0)
        self.test_seg_edit.setText(f"{cfg.test_start} ~ {cfg.test_end}")
        self.test_seg_edit.setCursorPosition(0)
        self.model_combo.setCurrentText(cfg.model_key)
        self._update_model_meta_and_table(cfg.model_key, cfg.model_kwargs)
        self.yaml_editor.setPlainText(cfg.to_yaml())
        self._updating_ui = False

    def _update_model_meta_and_table(self, model_key: str, kwargs_dict: dict[str, Any]) -> None:
        meta = MODEL_CATALOG.get(model_key, MODEL_CATALOG["LightGBM (GBDT)"])
        self.model_desc_lbl.setText(
            f"<b>Class:</b> <code>{meta['module_path']}.{meta['class']}</code><br>"
            f"<b>Category:</b> {meta['category']}<br>"
            f"<b>简介:</b> {meta['description']}"
        )
        self.hp_table.blockSignals(True)
        self.hp_table.setRowCount(len(kwargs_dict))
        for r_idx, (k, v) in enumerate(kwargs_dict.items()):
            key_item = QTableWidgetItem(str(k))
            key_item.setFlags(key_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            val_item = QTableWidgetItem(str(v))
            self.hp_table.setItem(r_idx, 0, key_item)
            self.hp_table.setItem(r_idx, 1, val_item)
        self.hp_table.blockSignals(False)

    def _on_model_changed(self, model_key: str) -> None:
        if self._updating_ui:
            return
        meta = MODEL_CATALOG.get(model_key, MODEL_CATALOG["LightGBM (GBDT)"])
        self.config.model_key = model_key
        self.config.model_kwargs = dict(meta["default_kwargs"])
        self._update_model_meta_and_table(model_key, self.config.model_kwargs)
        self.yaml_editor.setPlainText(self.config.to_yaml())

    def _reset_model_hyperparams(self) -> None:
        self._on_model_changed(self.model_combo.currentText())

    def _on_hp_table_edited(self, _item: QTableWidgetItem) -> None:
        if self._updating_ui:
            return
        new_kwargs: dict[str, Any] = {}
        for r in range(self.hp_table.rowCount()):
            k_item = self.hp_table.item(r, 0)
            v_item = self.hp_table.item(r, 1)
            if not k_item or not v_item:
                continue
            k = k_item.text()
            raw_v = v_item.text().strip()
            # Smart scalar type coercion
            if raw_v.lower() in ("true", "false"):
                val: Any = raw_v.lower() == "true"
            else:
                try:
                    val = int(raw_v) if "." not in raw_v else float(raw_v)
                except ValueError:
                    val = raw_v
            new_kwargs[k] = val
        self.config.model_kwargs = new_kwargs
        self.yaml_editor.setPlainText(self.config.to_yaml())

    @staticmethod
    def _parse_seg(text: str, default_s: str, default_e: str) -> tuple[str, str]:
        parts = [p.strip() for p in text.replace("to", "~").split("~")]
        if len(parts) == 2 and parts[0] and parts[1]:
            return parts[0], parts[1]
        return default_s, default_e

    def _sync_ui_to_config(self) -> None:
        if self._updating_ui:
            return
        cfg = self.config
        cfg.experiment_name = self.exp_name_edit.text().strip() or "qlib_exp"
        cfg.market = self.market_combo.currentText()
        cfg.benchmark = "SH000905" if cfg.market == "csi500" else "SH000300"
        cfg.handler_class = self.handler_combo.currentText()
        cfg.label_expr = self.label_edit.text().strip() or "Ref($close, -2) / Ref($close, -1) - 1"
        cfg.train_start, cfg.train_end = self._parse_seg(self.train_seg_edit.text(), cfg.train_start, cfg.train_end)
        cfg.valid_start, cfg.valid_end = self._parse_seg(self.valid_seg_edit.text(), cfg.valid_start, cfg.valid_end)
        cfg.test_start, cfg.test_end = self._parse_seg(self.test_seg_edit.text(), cfg.test_start, cfg.test_end)
        self.yaml_editor.setPlainText(cfg.to_yaml())

    def _parse_yaml_to_ui(self) -> None:
        try:
            parsed = QlibWorkflowConfig.from_yaml(self.yaml_editor.toPlainText())
            parsed.experiment_name = self.exp_name_edit.text().strip() or parsed.experiment_name
            self.load_config_into_ui(parsed)
            self.log_requested.emit("SUCCESS", "[WorkflowYAML] Successfully parsed YAML into GUI form controls.")
        except Exception as exc:
            QMessageBox.warning(self, "YAML 解析错误", f"无法解析 YAML 配置：\n{exc}")

    def _import_yaml(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "导入 Qlib Workflow YAML", "", "YAML Files (*.yaml *.yml);;All Files (*)"
        )
        if path:
            from pathlib import Path

            text = Path(path).read_text(encoding="utf-8")
            self.yaml_editor.setPlainText(text)
            self._parse_yaml_to_ui()

    def _export_yaml(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "导出标准 qrun YAML 配置文件",
            f"{self.config.experiment_name}.yaml",
            "YAML Files (*.yaml *.yml)",
        )
        if path:
            from pathlib import Path

            Path(path).write_text(self.yaml_editor.toPlainText(), encoding="utf-8")
            self.log_requested.emit("SUCCESS", f"[WorkflowYAML] Saved qrun workflow config to {path}")

    def _trigger_run(self) -> None:
        self._sync_ui_to_config()
        self.loss_chart.reset_chart()
        self.run_workflow_requested.emit(self.config)
