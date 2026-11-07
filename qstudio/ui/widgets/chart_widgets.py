"""High-Performance Financial & Quantitative Chart Widgets powered by PyQtGraph."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pyqtgraph as pg
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPen, QPicture
from PySide6.QtWidgets import QVBoxLayout, QWidget

# Configure global PyQtGraph aesthetics
pg.setConfigOptions(antialias=True, background="#131722", foreground="#8B949E")


class DateAxisItem(pg.AxisItem):
    """Custom X-axis mapping integer bar indices to formatted date strings."""

    def __init__(self, orientation: str = "bottom", **kwargs) -> None:
        super().__init__(orientation=orientation, **kwargs)
        self.date_strings: list[str] = []

    def set_dates(self, dates) -> None:
        self.date_strings = [str(d)[:10] for d in dates]

    def tickStrings(self, values, scale, spacing):
        n = len(self.date_strings)
        if n == 0:
            return [str(int(v)) for v in values]
        out = []
        for v in values:
            idx = int(round(v))
            if 0 <= idx < n:
                out.append(self.date_strings[idx])
            else:
                out.append("")
        return out


class CandlestickItem(pg.GraphicsObject):
    """High-speed QPicture-cached OHLC Candlestick renderer."""

    def __init__(self, up_color: str = "#FF4D4F", down_color: str = "#00C087") -> None:
        super().__init__()
        self.up_color = up_color
        self.down_color = down_color
        self.picture = QPicture()
        self._data: np.ndarray | None = None

    def set_data(self, ohlc: np.ndarray, up_color: str = "#FF4D4F", down_color: str = "#00C087") -> None:
        """ohlc shape: (N, 4) -> [open, high, low, close]."""
        self._data = ohlc
        self.up_color = up_color
        self.down_color = down_color
        self._generate_picture()
        self.informViewBoundsChanged()
        self.update()

    def _generate_picture(self) -> None:
        self.picture = QPicture()
        if self._data is None or len(self._data) == 0:
            return
        painter = QPainter(self.picture)
        up_q = QColor(self.up_color)
        dn_q = QColor(self.down_color)
        pen_up = QPen(up_q, 1.1)
        pen_dn = QPen(dn_q, 1.1)
        brush_up = QBrush(up_q)
        brush_dn = QBrush(dn_q)
        w = 0.34

        for idx, (o, h, l, c) in enumerate(self._data):
            x = float(idx)
            if c >= o:
                painter.setPen(pen_up)
                painter.setBrush(brush_up)
                top = c
                bottom = o
            else:
                painter.setPen(pen_dn)
                painter.setBrush(brush_dn)
                top = o
                bottom = c

            painter.drawLine(QPointF(x, float(l)), QPointF(x, float(h)))
            body_h = max(float(top - bottom), 0.01)
            painter.drawRect(QRectF(x - w, float(bottom), w * 2.0, body_h))
        painter.end()

    def paint(self, painter: QPainter, *args) -> None:
        painter.drawPicture(0, 0, self.picture)

    def boundingRect(self) -> QRectF:
        return QRectF(self.picture.boundingRect())


class KLineFeatureChartWidget(QWidget):
    """3-pane linked chart: Candlestick + Moving Averages (Top), Volume (Middle), Qlib Expression Factor (Bottom)."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.glw = pg.GraphicsLayoutWidget()
        self.glw.setBackground("#131722")
        layout.addWidget(self.glw)

        self.date_axis_top = DateAxisItem("bottom")
        self.date_axis_mid = DateAxisItem("bottom")
        self.date_axis_bot = DateAxisItem("bottom")

        # Pane 1: K-Line + MA5/20/60
        self.p_kline = self.glw.addPlot(row=0, col=0, axisItems={"bottom": self.date_axis_top})
        self.p_kline.showGrid(x=True, y=True, alpha=0.18)
        self.p_kline.setLabel("left", "Price")
        self.p_kline.addLegend(offset=(12, 8), labelTextSize="9pt")

        # Pane 2: Volume
        self.p_vol = self.glw.addPlot(row=1, col=0, axisItems={"bottom": self.date_axis_mid})
        self.p_vol.showGrid(x=True, y=True, alpha=0.18)
        self.p_vol.setLabel("left", "Volume")
        self.p_vol.setXLink(self.p_kline)

        # Pane 3: Custom Qlib Expression Factor
        self.p_factor = self.glw.addPlot(row=2, col=0, axisItems={"bottom": self.date_axis_bot})
        self.p_factor.showGrid(x=True, y=True, alpha=0.18)
        self.p_factor.setLabel("left", "Factor")
        self.p_factor.setXLink(self.p_kline)

        self.glw.ci.layout.setRowStretchFactor(0, 5)
        self.glw.ci.layout.setRowStretchFactor(1, 2)
        self.glw.ci.layout.setRowStretchFactor(2, 2)

        self.candle_item = CandlestickItem()
        self.p_kline.addItem(self.candle_item)
        self.ma5_curve = self.p_kline.plot(pen=pg.mkPen("#F5A623", width=1.4), name="MA5")
        self.ma20_curve = self.p_kline.plot(pen=pg.mkPen("#00E5FF", width=1.5), name="MA20")
        self.ma60_curve = self.p_kline.plot(pen=pg.mkPen("#B388FF", width=1.5), name="MA60")

        self.vol_bars: pg.BarGraphItem | None = None
        self.factor_curve = self.p_factor.plot(
            pen=pg.mkPen("#2962FF", width=1.8),
            fillLevel=0,
            brush=(41, 98, 255, 45),
        )

    def update_chart(
        self,
        df: pd.DataFrame,
        instrument: str,
        expr_label: str,
        up_color: str = "#FF4D4F",
        down_color: str = "#00C087",
    ) -> None:
        if df.empty:
            return
        dates = df["date"].tolist()
        self.date_axis_top.set_dates(dates)
        self.date_axis_mid.set_dates(dates)
        self.date_axis_bot.set_dates(dates)

        x = np.arange(len(df), dtype=float)
        ohlc = df[["open", "high", "low", "close"]].to_numpy(dtype=float)
        self.candle_item.set_data(ohlc, up_color=up_color, down_color=down_color)

        self.ma5_curve.setData(x, df["ma5"].to_numpy(dtype=float))
        self.ma20_curve.setData(x, df["ma20"].to_numpy(dtype=float))
        self.ma60_curve.setData(x, df["ma60"].to_numpy(dtype=float))
        self.p_kline.setTitle(f"{instrument} — Daily K-Line & Moving Averages", color="#E6EDF3", size="10pt")

        if self.vol_bars is not None:
            self.p_vol.removeItem(self.vol_bars)
        brushes = [
            pg.mkBrush(up_color if c >= o else down_color)
            for o, c in zip(df["open"], df["close"])
        ]
        self.vol_bars = pg.BarGraphItem(x=x, height=df["volume"].to_numpy(dtype=float), width=0.6, brushes=brushes, pen=None)
        self.p_vol.addItem(self.vol_bars)

        self.factor_curve.setData(x, df["custom_factor"].to_numpy(dtype=float))
        self.p_factor.setTitle(f"Qlib Expression: {expr_label}", color="#79C0FF", size="9.5pt")
        self.p_kline.enableAutoRange()
        self.p_vol.enableAutoRange()
        self.p_factor.enableAutoRange()


class PerformanceChartWidget(QWidget):
    """Linked Cumulative Return & Underwater Drawdown Chart (PortAnaRecord visualization)."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.glw = pg.GraphicsLayoutWidget()
        self.glw.setBackground("#131722")
        layout.addWidget(self.glw)

        self.axis_top = DateAxisItem("bottom")
        self.axis_bot = DateAxisItem("bottom")

        self.p_nav = self.glw.addPlot(row=0, col=0, axisItems={"bottom": self.axis_top})
        self.p_nav.showGrid(x=True, y=True, alpha=0.2)
        self.p_nav.setLabel("left", "Cumulative Return (%)")
        self.p_nav.addLegend(offset=(12, 10), labelTextSize="9pt")

        self.p_dd = self.glw.addPlot(row=1, col=0, axisItems={"bottom": self.axis_bot})
        self.p_dd.showGrid(x=True, y=True, alpha=0.2)
        self.p_dd.setLabel("left", "Drawdown (%)")
        self.p_dd.setXLink(self.p_nav)

        self.glw.ci.layout.setRowStretchFactor(0, 7)
        self.glw.ci.layout.setRowStretchFactor(1, 3)

        self.c_excess_net = self.p_nav.plot(
            pen=pg.mkPen("#2962FF", width=2.4), name="Excess Return (With Cost)"
        )
        self.c_excess_gross = self.p_nav.plot(
            pen=pg.mkPen("#00E5FF", width=1.6, style=Qt.PenStyle.DashLine),
            name="Excess Return (No Cost)",
        )
        self.c_port = self.p_nav.plot(
            pen=pg.mkPen("#00C087", width=1.8), name="Portfolio Total Return"
        )
        self.c_bench = self.p_nav.plot(
            pen=pg.mkPen("#F5A623", width=1.6), name="Benchmark (SH000300)"
        )

        self.c_dd = self.p_dd.plot(
            pen=pg.mkPen("#FF4D4F", width=1.6),
            fillLevel=0,
            brush=(255, 77, 79, 55),
            name="Underwater Drawdown",
        )

    def update_performance(self, daily_df: pd.DataFrame, title: str = "") -> None:
        if daily_df.empty:
            return
        dates = daily_df["date"].tolist()
        self.axis_top.set_dates(dates)
        self.axis_bot.set_dates(dates)

        x = np.arange(len(daily_df), dtype=float)
        self.c_excess_net.setData(x, daily_df["excess_return_with_cost"].to_numpy(dtype=float) * 100.0)
        self.c_excess_gross.setData(x, daily_df["excess_return_no_cost"].to_numpy(dtype=float) * 100.0)
        self.c_port.setData(x, daily_df["cum_return"].to_numpy(dtype=float) * 100.0)
        self.c_bench.setData(x, daily_df["benchmark_return"].to_numpy(dtype=float) * 100.0)
        self.c_dd.setData(x, daily_df["drawdown"].to_numpy(dtype=float) * 100.0)

        if title:
            self.p_nav.setTitle(title, color="#E6EDF3", size="10pt")
        self.p_nav.enableAutoRange()
        self.p_dd.enableAutoRange()


class ICAnalysisChartWidget(QWidget):
    """Dual-pane chart for Factor IC daily bars + Cumulative IC / RankIC curves."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.glw = pg.GraphicsLayoutWidget()
        self.glw.setBackground("#131722")
        layout.addWidget(self.glw)

        self.axis_top = DateAxisItem("bottom")
        self.axis_bot = DateAxisItem("bottom")

        self.p_daily = self.glw.addPlot(row=0, col=0, axisItems={"bottom": self.axis_top})
        self.p_daily.showGrid(x=True, y=True, alpha=0.18)
        self.p_daily.setLabel("left", "Daily IC")
        self.p_daily.addLegend(offset=(12, 8), labelTextSize="9pt")

        self.p_cum = self.glw.addPlot(row=1, col=0, axisItems={"bottom": self.axis_bot})
        self.p_cum.showGrid(x=True, y=True, alpha=0.18)
        self.p_cum.setLabel("left", "Cumulative IC")
        self.p_cum.addLegend(offset=(12, 8), labelTextSize="9pt")
        self.p_cum.setXLink(self.p_daily)

        self.ic_bars: pg.BarGraphItem | None = None
        self.ic_ma_curve = self.p_daily.plot(pen=pg.mkPen("#F5A623", width=2.0), name="20D Moving Avg IC")
        self.cum_ic_curve = self.p_cum.plot(pen=pg.mkPen("#2962FF", width=2.2), name="Cumulative IC")
        self.cum_ric_curve = self.p_cum.plot(pen=pg.mkPen("#00E5FF", width=2.0), name="Cumulative RankIC")

    def update_ic(self, ic_df: pd.DataFrame) -> None:
        if ic_df.empty:
            return
        dates = ic_df["date"].tolist()
        self.axis_top.set_dates(dates)
        self.axis_bot.set_dates(dates)
        x = np.arange(len(ic_df), dtype=float)
        ic_vals = ic_df["ic"].to_numpy(dtype=float)

        if self.ic_bars is not None:
            self.p_daily.removeItem(self.ic_bars)
        brushes = [pg.mkBrush("#2962FFAA" if v >= 0 else "#FF4D4FAA") for v in ic_vals]
        self.ic_bars = pg.BarGraphItem(x=x, height=ic_vals, width=0.65, brushes=brushes, pen=None)
        self.p_daily.addItem(self.ic_bars)

        if "ic_ma20" in ic_df.columns:
            ma20 = ic_df["ic_ma20"].to_numpy(dtype=float)
        else:
            ma20 = pd.Series(ic_vals).rolling(20, min_periods=1).mean().to_numpy(dtype=float)
        self.ic_ma_curve.setData(x, ma20)

        cum_ic = np.cumsum(ic_vals)
        cum_ric = np.cumsum(ic_df["rank_ic"].to_numpy(dtype=float))
        self.cum_ic_curve.setData(x, cum_ic)
        self.cum_ric_curve.setData(x, cum_ric)
        self.p_daily.enableAutoRange()
        self.p_cum.enableAutoRange()


class QuantileReturnChartWidget(QWidget):
    """Multi-line chart displaying G1..G5 stratified quantile cumulative returns."""

    PALETTE = ["#FF4D4F", "#F5A623", "#8B949E", "#00E5FF", "#00C087", "#2962FF"]

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.glw = pg.GraphicsLayoutWidget()
        self.glw.setBackground("#131722")
        layout.addWidget(self.glw)

        self.date_axis = DateAxisItem("bottom")
        self.plot = self.glw.addPlot(row=0, col=0, axisItems={"bottom": self.date_axis})
        self.plot.showGrid(x=True, y=True, alpha=0.2)
        self.plot.setLabel("left", "Stratified Return (%)")
        self.plot.addLegend(offset=(12, 8), labelTextSize="9pt")
        self.curves: list[pg.PlotDataItem] = []

    def update_quantiles(self, group_df: pd.DataFrame) -> None:
        for c in self.curves:
            self.plot.removeItem(c)
        self.curves.clear()
        if group_df.empty:
            return

        if "date" in group_df.columns:
            self.date_axis.set_dates(group_df["date"].tolist())
            cols = [c for c in group_df.columns if c != "date"]
        else:
            self.date_axis.set_dates(group_df.index.tolist())
            cols = list(group_df.columns)

        x = np.arange(len(group_df), dtype=float)
        for idx, col in enumerate(cols):
            color = self.PALETTE[idx % len(self.PALETTE)]
            width = 2.4 if ("5" in col or "Long" in col) else 1.6
            curve = self.plot.plot(
                x,
                group_df[col].to_numpy(dtype=float) * 100.0,
                pen=pg.mkPen(color, width=width),
                name=col,
            )
            self.curves.append(curve)
        self.plot.enableAutoRange()


class TrainingLossChartWidget(QWidget):
    """Real-time streaming Train & Validation Loss convergence plot."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.glw = pg.GraphicsLayoutWidget()
        self.glw.setBackground("#131722")
        layout.addWidget(self.glw)

        self.plot = self.glw.addPlot(row=0, col=0)
        self.plot.showGrid(x=True, y=True, alpha=0.2)
        self.plot.setLabel("left", "Loss (MSE / IC Loss)")
        self.plot.setLabel("bottom", "Epoch / Boosting Step")
        self.plot.addLegend(offset=(12, 8), labelTextSize="9pt")

        self.train_curve = self.plot.plot(
            pen=pg.mkPen("#2962FF", width=2.2), symbol="o", symbolSize=5, symbolBrush="#2962FF", name="Train Loss"
        )
        self.valid_curve = self.plot.plot(
            pen=pg.mkPen("#00C087", width=2.2), symbol="o", symbolSize=5, symbolBrush="#00C087", name="Valid Loss"
        )
        self._epochs: list[int] = []
        self._train_losses: list[float] = []
        self._valid_losses: list[float] = []

    def reset_chart(self) -> None:
        self._epochs.clear()
        self._train_losses.clear()
        self._valid_losses.clear()
        self.train_curve.setData([], [])
        self.valid_curve.setData([], [])

    def append_point(self, epoch: int, train_loss: float, valid_loss: float) -> None:
        self._epochs.append(epoch)
        self._train_losses.append(train_loss)
        self._valid_losses.append(valid_loss)
        self.train_curve.setData(self._epochs, self._train_losses)
        self.valid_curve.setData(self._epochs, self._valid_losses)

    def set_history(self, history: list[tuple[int, float, float]]) -> None:
        self.reset_chart()
        for ep, tl, vl in history:
            self._epochs.append(ep)
            self._train_losses.append(tl)
            self._valid_losses.append(vl)
        self.train_curve.setData(self._epochs, self._train_losses)
        self.valid_curve.setData(self._epochs, self._valid_losses)
