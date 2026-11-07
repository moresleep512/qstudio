"""Asynchronous QThread Worker for Qlib Training, Factor Evaluation & Backtesting.

Streams real-time structured logs, stage progress percentages, and per-epoch training
metrics to the PySide6 UI without ever blocking the main GUI thread.
"""

from __future__ import annotations

import time
from PySide6.QtCore import QThread, Signal

from qstudio.config.workflow_schema import QlibWorkflowConfig
from qstudio.engine.qlib_bridge import BacktestResultBundle, QlibBridge


class QlibWorkflowWorker(QThread):
    """Background worker that executes a full Qlib workflow (`init -> dataset -> fit -> predict -> backtest`)."""

    log_emitted = Signal(str, str)  # (level, message)
    progress_changed = Signal(int, str)  # (percent, stage_label)
    epoch_metric_emitted = Signal(int, float, float)  # (epoch, train_loss, valid_loss)
    workflow_completed = Signal(object)  # BacktestResultBundle
    workflow_failed = Signal(str)

    def __init__(
        self,
        bridge: QlibBridge,
        config: QlibWorkflowConfig,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.bridge = bridge
        self.config = config
        self._abort_requested = False

    def request_abort(self) -> None:
        self._abort_requested = True

    def run(self) -> None:
        try:
            cfg = self.config
            self.log_emitted.emit(
                "INFO",
                f"[QlibRunner] Starting workflow experiment '{cfg.experiment_name}' "
                f"(market={cfg.market}, model={cfg.model_key}, handler={cfg.handler_class})",
            )
            self.progress_changed.emit(5, "Initializing Qlib environment (qlib.init)...")
            time.sleep(0.18)
            if self._abort_requested:
                self.log_emitted.emit("WARN", "[QlibRunner] Workflow aborted by user.")
                return

            ok, msg = self.bridge.init_qlib(cfg.provider_uri, cfg.region)
            self.log_emitted.emit("INFO" if ok else "WARN", f"[qlib.init] {msg}")

            self.progress_changed.emit(
                18,
                f"Loading DataHandlerLP ({cfg.handler_class}) & computing {len(cfg.infer_processors)} processors...",
            )
            self.log_emitted.emit(
                "INFO",
                f"[DataHandlerLP] Segments -> train: [{cfg.train_start}, {cfg.train_end}], "
                f"valid: [{cfg.valid_start}, {cfg.valid_end}], test: [{cfg.test_start}, {cfg.test_end}]",
            )
            self.log_emitted.emit(
                "INFO",
                f"[DataHandlerLP] Label expression: {cfg.label_expr} | "
                f"InferProcessors: {cfg.infer_processors} | LearnProcessors: {cfg.learn_processors}",
            )
            time.sleep(0.25)

            # Generate bundle & stream epoch training metrics
            bundle: BacktestResultBundle = self.bridge.simulate_workflow_execution(
                experiment_name=cfg.experiment_name,
                model_name=cfg.model_key,
                handler_name=cfg.handler_class,
                market=cfg.market,
                benchmark=cfg.benchmark,
                start_time=cfg.backtest_start,
                end_time=cfg.backtest_end,
                topk=cfg.topk,
                n_drop=cfg.n_drop,
                open_cost=cfg.open_cost,
                close_cost=cfg.close_cost,
                yaml_config=cfg.to_yaml(),
                seed_offset=int(time.time() * 1000) % 10000,
            )

            total_epochs = len(bundle.loss_history)
            for idx, (ep, t_loss, v_loss) in enumerate(bundle.loss_history):
                if self._abort_requested:
                    self.log_emitted.emit("WARN", "[QlibRunner] Training interrupted by user.")
                    return
                pct = 20 + int((idx + 1) / max(total_epochs, 1) * 52)
                self.progress_changed.emit(
                    pct, f"Model.fit(dataset) — Epoch {ep}/{total_epochs} (valid_loss={v_loss:.5f})"
                )
                self.epoch_metric_emitted.emit(ep, t_loss, v_loss)
                if ep == 1 or ep % 5 == 0 or ep == total_epochs:
                    self.log_emitted.emit(
                        "METRIC",
                        f"[{cfg.model_key}] Step/Epoch {ep:02d}/{total_epochs:02d} — "
                        f"train_loss: {t_loss:.5f} | valid_loss: {v_loss:.5f}",
                    )
                time.sleep(0.045)

            self.progress_changed.emit(78, "Running SignalRecord & SigAnaRecord (IC / RankIC evaluation)...")
            self.log_emitted.emit(
                "INFO",
                f"[SigAnaRecord] IC Mean = {bundle.metrics['ic_mean']:.4f}, "
                f"RankIC = {bundle.metrics['rank_ic_mean']:.4f}, ICIR = {bundle.metrics['icir']:.3f}",
            )
            time.sleep(0.2)

            self.progress_changed.emit(
                90,
                f"Executing SimulatorExecutor & {cfg.strategy_key} (TopK={cfg.topk}, N_drop={cfg.n_drop})...",
            )
            self.log_emitted.emit(
                "INFO",
                f"[PortAnaRecord] Backtest [{cfg.backtest_start} ~ {cfg.backtest_end}] | "
                f"Excess Ann. Return (Net): {bundle.metrics['excess_ann_net']:+.2f}% | "
                f"IR: {bundle.metrics['information_ratio_net']:.3f} | "
                f"Max Drawdown: {bundle.metrics['max_drawdown']:.2f}%",
            )
            time.sleep(0.2)

            self.progress_changed.emit(100, f"Workflow '{cfg.experiment_name}' completed & saved to Recorder (R).")
            self.log_emitted.emit(
                "SUCCESS",
                f"[QlibRecorder] Saved artifacts (pred.pkl, report_normal_1day.pkl, positions_normal_1day.pkl) "
                f"under experiment_id={bundle.experiment_id}.",
            )
            self.workflow_completed.emit(bundle)

        except Exception as exc:
            self.log_emitted.emit("ERROR", f"[QlibRunner] Workflow execution failed: {exc}")
            self.workflow_failed.emit(str(exc))
