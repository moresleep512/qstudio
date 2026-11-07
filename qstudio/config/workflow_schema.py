"""Bidirectional Qlib Workflow Configuration Schema & YAML Generator.

Maps GUI form state directly to 100% compatible `qrun` YAML configuration files
(`qlib.utils.init_instance_by_config`).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import yaml


# Model catalog matching qlib.contrib.model
MODEL_CATALOG: dict[str, dict[str, Any]] = {
    "LightGBM (GBDT)": {
        "class": "LGBModel",
        "module_path": "qlib.contrib.model.gbdt",
        "category": "GBDT / Tree",
        "description": "微软经典梯度提升决策树，Qlib 官方默认基线，训练极快，截面特征表现优异。",
        "default_kwargs": {
            "loss": "mse",
            "colsample_bytree": 0.8879,
            "learning_rate": 0.0421,
            "subsample": 0.8789,
            "lambda_l1": 205.6999,
            "lambda_l2": 580.9768,
            "max_depth": 8,
            "num_leaves": 210,
            "num_threads": 8,
        },
    },
    "XGBoost": {
        "class": "XGBModel",
        "module_path": "qlib.contrib.model.xgboost",
        "category": "GBDT / Tree",
        "description": "二阶泰勒展开 GBDT 模型，支持正则化与缺失值自动分裂。",
        "default_kwargs": {
            "eval_metric": "rmse",
            "colsample_bytree": 0.8879,
            "eta": 0.0421,
            "max_depth": 8,
            "n_estimators": 647,
            "subsample": 0.8789,
            "nthread": 8,
        },
    },
    "CatBoost": {
        "class": "CatBoostModel",
        "module_path": "qlib.contrib.model.catboost_model",
        "category": "GBDT / Tree",
        "description": "对称树结构 (Oblivious Trees)，抗过拟合能力极强，适合高噪金融截面特征。",
        "default_kwargs": {
            "loss_function": "RMSE",
            "learning_rate": 0.0421,
            "subsample": 0.8789,
            "max_depth": 6,
            "num_leaves": 64,
            "thread_count": 8,
        },
    },
    "DoubleEnsemble": {
        "class": "DEnsembleModel",
        "module_path": "qlib.contrib.model.double_ensemble",
        "category": "GBDT / Ensemble",
        "description": "Qlib 旗舰样本重加权 + 特征重采样双重集成模型，显著降低尾部回撤。",
        "default_kwargs": {
            "base_model": "gbm",
            "loss": "mse",
            "num_models": 6,
            "enable_sr": True,
            "enable_fs": True,
            "alpha1": 1.0,
            "alpha2": 1.0,
            "bins_sr": 10,
            "bins_fs": 5,
            "decay": 0.5,
        },
    },
    "MLP (Deep Neural Net)": {
        "class": "DNNModelPytorch",
        "module_path": "qlib.contrib.model.pytorch_nn",
        "category": "PyTorch Deep Learning",
        "description": "多层感知机深度神经网络，包含 BatchNorm 与 Dropout 层，支持 GPU 加速。",
        "default_kwargs": {
            "lr": 0.001,
            "max_steps": 4000,
            "batch_size": 2048,
            "weight_decay": 0.0002,
            "optimizer": "gd",
            "GPU": 0,
        },
    },
    "LSTM (Time Series)": {
        "class": "LSTM",
        "module_path": "qlib.contrib.model.pytorch_lstm",
        "category": "PyTorch Sequence",
        "description": "长短期记忆时序网络，捕捉个股量价序列长周期依赖，常配合 Alpha360 使用。",
        "default_kwargs": {
            "d_feat": 6,
            "hidden_size": 64,
            "num_layers": 2,
            "dropout": 0.0,
            "n_epochs": 100,
            "lr": 0.001,
            "batch_size": 800,
            "early_stop": 15,
            "loss": "mse",
            "optimizer": "adam",
            "GPU": 0,
        },
    },
    "ALSTM (Attention LSTM)": {
        "class": "ALSTM",
        "module_path": "qlib.contrib.model.pytorch_alstm",
        "category": "PyTorch Sequence",
        "description": "带时间注意力机制 (Temporal Attention) 的 LSTM，强化关键异动交易日权重。",
        "default_kwargs": {
            "d_feat": 6,
            "hidden_size": 64,
            "num_layers": 2,
            "dropout": 0.0,
            "n_epochs": 100,
            "lr": 0.001,
            "batch_size": 800,
            "early_stop": 15,
            "rnn_type": "GRU",
            "GPU": 0,
        },
    },
    "Transformer": {
        "class": "TransformerModel",
        "module_path": "qlib.contrib.model.pytorch_transformer",
        "category": "PyTorch Attention",
        "description": "自注意力架构量化模型，同时建模多维量价时序特征间的高阶交互。",
        "default_kwargs": {
            "d_feat": 6,
            "d_model": 64,
            "nhead": 4,
            "num_layers": 2,
            "dropout": 0.1,
            "n_epochs": 100,
            "lr": 0.0005,
            "batch_size": 800,
            "early_stop": 15,
            "GPU": 0,
        },
    },
    "HIST (Graph Concept Shared)": {
        "class": "HIST",
        "module_path": "qlib.contrib.model.pytorch_hist",
        "category": "PyTorch Graph/Concept",
        "description": "微软旗舰概念图网络模型，显式挖掘股票间预定义概念与隐含关联效应。",
        "default_kwargs": {
            "d_feat": 6,
            "hidden_size": 64,
            "num_layers": 2,
            "n_epochs": 100,
            "lr": 0.0002,
            "early_stop": 15,
            "GPU": 0,
        },
    },
}


STRATEGY_CATALOG: dict[str, dict[str, Any]] = {
    "TopkDropoutStrategy": {
        "class": "TopkDropoutStrategy",
        "module_path": "qlib.contrib.strategy",
        "description": "Qlib 最经典的等权轮动策略：持仓排名前 TopK 只股票，每期最多淘汰表现最差的 N_drop 只并换入新高分股。",
    },
    "EnhancedIndexingStrategy": {
        "class": "EnhancedIndexingStrategy",
        "module_path": "qlib.contrib.strategy.optimizer",
        "description": "指数增强组合优化策略：在控制行业偏离、风格暴露和跟踪误差约束下最大化 Alpha 预期收益。",
    },
}


@dataclass
class QlibWorkflowConfig:
    """Complete structured representation of a Qlib workflow (`qrun` config)."""

    experiment_name: str = "alpha158_lgbm_csi300"
    provider_uri: str = "~/.qlib/qlib_data/cn_data"
    region: str = "cn"
    market: str = "csi300"
    benchmark: str = "SH000300"

    # DataHandler configuration
    handler_class: str = "Alpha158"  # Alpha158 or Alpha360
    data_start_time: str = "2015-01-01"
    data_end_time: str = "2025-12-31"
    fit_start_time: str = "2015-01-01"
    fit_end_time: str = "2021-12-31"
    label_expr: str = "Ref($close, -2) / Ref($close, -1) - 1"
    infer_processors: list[str] = field(
        default_factory=lambda: ["RobustZScoreNorm", "Fillna"]
    )
    learn_processors: list[str] = field(
        default_factory=lambda: ["DropnaLabel", "CSZScoreNorm"]
    )

    # Dataset segments
    train_start: str = "2015-01-01"
    train_end: str = "2021-12-31"
    valid_start: str = "2022-01-01"
    valid_end: str = "2023-06-30"
    test_start: str = "2023-07-01"
    test_end: str = "2025-12-31"

    # Model configuration
    model_key: str = "LightGBM (GBDT)"
    model_kwargs: dict[str, Any] = field(
        default_factory=lambda: dict(MODEL_CATALOG["LightGBM (GBDT)"]["default_kwargs"])
    )

    # Strategy & Backtest configuration
    strategy_key: str = "TopkDropoutStrategy"
    topk: int = 50
    n_drop: int = 5
    hold_thresh: int = 1
    only_tradable: bool = True

    backtest_start: str = "2023-07-01"
    backtest_end: str = "2025-12-31"
    account_cash: float = 100_000_000.0
    limit_threshold: float = 0.095
    deal_price: str = "close"
    open_cost: float = 0.0005
    close_cost: float = 0.0015
    min_cost: float = 5.0

    def to_qlib_dict(self) -> dict[str, Any]:
        """Convert to a standard Qlib `qrun` dictionary structure."""
        model_meta = MODEL_CATALOG.get(self.model_key, MODEL_CATALOG["LightGBM (GBDT)"])
        strategy_meta = STRATEGY_CATALOG.get(
            self.strategy_key, STRATEGY_CATALOG["TopkDropoutStrategy"]
        )

        infer_proc_list: list[dict[str, Any]] = []
        for p in self.infer_processors:
            if p in ("RobustZScoreNorm", "ZScoreNorm", "MinMaxNorm"):
                infer_proc_list.append(
                    {
                        "class": p,
                        "kwargs": {
                            "fields_group": "feature",
                            "clip_outlier": True,
                            "fit_start_time": self.fit_start_time,
                            "fit_end_time": self.fit_end_time,
                        },
                    }
                )
            else:
                infer_proc_list.append({"class": p, "kwargs": {"fields_group": "feature"}})

        learn_proc_list: list[dict[str, Any]] = []
        for p in self.learn_processors:
            if p == "DropnaLabel":
                learn_proc_list.append({"class": "DropnaLabel"})
            else:
                learn_proc_list.append({"class": p, "kwargs": {"fields_group": "label"}})

        data_handler_config: dict[str, Any] = {
            "start_time": self.data_start_time,
            "end_time": self.data_end_time,
            "fit_start_time": self.fit_start_time,
            "fit_end_time": self.fit_end_time,
            "instruments": self.market,
            "infer_processors": infer_proc_list,
            "learn_processors": learn_proc_list,
            "label": [self.label_expr],
        }

        port_analysis_config: dict[str, Any] = {
            "executor": {
                "class": "SimulatorExecutor",
                "module_path": "qlib.backtest.executor",
                "kwargs": {
                    "time_per_step": "day",
                    "generate_portfolio_metrics": True,
                },
            },
            "strategy": {
                "class": strategy_meta["class"],
                "module_path": strategy_meta["module_path"],
                "kwargs": {
                    "signal": "<PRED>",
                    "topk": self.topk,
                    "n_drop": self.n_drop,
                    "hold_thresh": self.hold_thresh,
                    "only_tradable": self.only_tradable,
                },
            },
            "backtest": {
                "start_time": self.backtest_start,
                "end_time": self.backtest_end,
                "account": int(self.account_cash),
                "benchmark": self.benchmark,
                "exchange_kwargs": {
                    "freq": "day",
                    "limit_threshold": self.limit_threshold,
                    "deal_price": self.deal_price,
                    "open_cost": self.open_cost,
                    "close_cost": self.close_cost,
                    "min_cost": self.min_cost,
                },
            },
        }

        return {
            "qlib_init": {
                "provider_uri": self.provider_uri,
                "region": self.region,
            },
            "market": self.market,
            "benchmark": self.benchmark,
            "data_handler_config": data_handler_config,
            "port_analysis_config": port_analysis_config,
            "task": {
                "model": {
                    "class": model_meta["class"],
                    "module_path": model_meta["module_path"],
                    "kwargs": dict(self.model_kwargs),
                },
                "dataset": {
                    "class": "DatasetH",
                    "module_path": "qlib.data.dataset",
                    "kwargs": {
                        "handler": {
                            "class": self.handler_class,
                            "module_path": "qlib.contrib.data.handler",
                            "kwargs": data_handler_config,
                        },
                        "segments": {
                            "train": [self.train_start, self.train_end],
                            "valid": [self.valid_start, self.valid_end],
                            "test": [self.test_start, self.test_end],
                        },
                    },
                },
                "record": [
                    {
                        "class": "SignalRecord",
                        "module_path": "qlib.workflow.record_temp",
                        "kwargs": {"model": "<MODEL>", "dataset": "<DATASET>"},
                    },
                    {
                        "class": "SigAnaRecord",
                        "module_path": "qlib.workflow.record_temp",
                        "kwargs": {"ana_long_short": False, "ann_scaler": 252},
                    },
                    {
                        "class": "PortAnaRecord",
                        "module_path": "qlib.workflow.record_temp",
                        "kwargs": {"config": port_analysis_config},
                    },
                ],
            },
        }

    def to_yaml(self) -> str:
        """Serialize workflow configuration into clean Qlib YAML text."""
        header = (
            "# =====================================================================\n"
            f"# Generated by Qlib Studio Pro | Experiment: {self.experiment_name}\n"
            "# Compatible with Microsoft Qlib CLI: `qrun workflow.yaml`\n"
            "# =====================================================================\n\n"
        )
        body = yaml.safe_dump(
            self.to_qlib_dict(),
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False,
            indent=2,
        )
        return header + body

    @classmethod
    def from_yaml(cls, yaml_text: str) -> QlibWorkflowConfig:
        """Parse a Qlib YAML file back into QlibWorkflowConfig."""
        raw = yaml.safe_load(yaml_text) or {}
        cfg = cls()
        qinit = raw.get("qlib_init", {})
        if isinstance(qinit, dict):
            cfg.provider_uri = str(qinit.get("provider_uri", cfg.provider_uri))
            cfg.region = str(qinit.get("region", cfg.region))
        cfg.market = str(raw.get("market", cfg.market))
        cfg.benchmark = str(raw.get("benchmark", cfg.benchmark))

        dh = raw.get("data_handler_config", {})
        if isinstance(dh, dict):
            cfg.data_start_time = str(dh.get("start_time", cfg.data_start_time))
            cfg.data_end_time = str(dh.get("end_time", cfg.data_end_time))
            cfg.fit_start_time = str(dh.get("fit_start_time", cfg.fit_start_time))
            cfg.fit_end_time = str(dh.get("fit_end_time", cfg.fit_end_time))
            lbl = dh.get("label")
            if isinstance(lbl, list) and lbl:
                cfg.label_expr = str(lbl[0])

        task = raw.get("task", {})
        if isinstance(task, dict):
            model_cfg = task.get("model", {})
            if isinstance(model_cfg, dict):
                cls_name = model_cfg.get("class")
                for key, meta in MODEL_CATALOG.items():
                    if meta["class"] == cls_name:
                        cfg.model_key = key
                        break
                if isinstance(model_cfg.get("kwargs"), dict):
                    cfg.model_kwargs = dict(model_cfg["kwargs"])

            ds_cfg = task.get("dataset", {}).get("kwargs", {})
            if isinstance(ds_cfg, dict):
                handler = ds_cfg.get("handler", {})
                if isinstance(handler, dict) and handler.get("class"):
                    cfg.handler_class = str(handler["class"])
                segs = ds_cfg.get("segments", {})
                if isinstance(segs, dict):
                    if "train" in segs and len(segs["train"]) == 2:
                        cfg.train_start, cfg.train_end = map(str, segs["train"])
                    if "valid" in segs and len(segs["valid"]) == 2:
                        cfg.valid_start, cfg.valid_end = map(str, segs["valid"])
                    if "test" in segs and len(segs["test"]) == 2:
                        cfg.test_start, cfg.test_end = map(str, segs["test"])

        pa = raw.get("port_analysis_config", {})
        if isinstance(pa, dict):
            strat = pa.get("strategy", {}).get("kwargs", {})
            if isinstance(strat, dict):
                cfg.topk = int(strat.get("topk", cfg.topk))
                cfg.n_drop = int(strat.get("n_drop", cfg.n_drop))
            bt = pa.get("backtest", {})
            if isinstance(bt, dict):
                cfg.backtest_start = str(bt.get("start_time", cfg.backtest_start))
                cfg.backtest_end = str(bt.get("end_time", cfg.backtest_end))
                cfg.account_cash = float(bt.get("account", cfg.account_cash))
                ex = bt.get("exchange_kwargs", {})
                if isinstance(ex, dict):
                    cfg.limit_threshold = float(ex.get("limit_threshold", cfg.limit_threshold))
                    cfg.deal_price = str(ex.get("deal_price", cfg.deal_price))
                    cfg.open_cost = float(ex.get("open_cost", cfg.open_cost))
                    cfg.close_cost = float(ex.get("close_cost", cfg.close_cost))
                    cfg.min_cost = float(ex.get("min_cost", cfg.min_cost))

        return cfg
