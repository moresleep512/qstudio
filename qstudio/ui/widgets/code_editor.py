"""Syntax-highlighted YAML & Qlib Expression Editor Widget."""

from __future__ import annotations

import re
from PySide6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat
from PySide6.QtWidgets import QPlainTextEdit


class QlibYamlHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for Qlib YAML configs and Qlib formulaic expressions."""

    def __init__(self, document) -> None:
        super().__init__(document)
        self.rules: list[tuple[re.Pattern[str], QTextCharFormat]] = []

        # YAML keys
        key_fmt = QTextCharFormat()
        key_fmt.setForeground(QColor("#79C0FF"))
        key_fmt.setFontWeight(QFont.Weight.Bold)
        self.rules.append((re.compile(r"^\s*[\w_]+(?=\s*:)"), key_fmt))

        # Qlib fields ($close, $open, $volume, $factor, etc.)
        field_fmt = QTextCharFormat()
        field_fmt.setForeground(QColor("#FF7B72"))
        field_fmt.setFontWeight(QFont.Weight.Bold)
        self.rules.append((re.compile(r"\$[a-zA-Z_]\w*"), field_fmt))

        # Qlib operators (Ref, Mean, Std, Corr, Rank, Greater, Less, Slope, Rsquare, etc.)
        op_fmt = QTextCharFormat()
        op_fmt.setForeground(QColor("#D2A8FF"))
        op_fmt.setFontWeight(QFont.Weight.Bold)
        ops = (
            r"\b(Ref|Mean|Std|Var|Skew|Kurt|Max|Min|Quantile|Med|Mad|Rank|Count|"
            r"Sum|Slope|Rsquare|Resi|Corr|Cov|Delta|WMA|EMA|Greater|Less|Abs|Log|Sign|"
            r"If|Alpha158|Alpha360|DatasetH|DataHandlerLP|LGBModel|XGBModel|CatBoostModel|"
            r"DNNModelPytorch|LSTM|ALSTM|TransformerModel|HIST|TopkDropoutStrategy|"
            r"SimulatorExecutor|SignalRecord|SigAnaRecord|PortAnaRecord)\b"
        )
        self.rules.append((re.compile(ops), op_fmt))

        # Numbers & booleans
        num_fmt = QTextCharFormat()
        num_fmt.setForeground(QColor("#FFA657"))
        self.rules.append((re.compile(r"\b-?\d+(\.\d+)?([eE][+-]?\d+)?\b"), num_fmt))
        self.rules.append((re.compile(r"\b(true|false|True|False|null|None)\b"), num_fmt))

        # Strings
        str_fmt = QTextCharFormat()
        str_fmt.setForeground(QColor("#A5D6FF"))
        self.rules.append((re.compile(r"'[^']*'"), str_fmt))
        self.rules.append((re.compile(r'"[^"]*"'), str_fmt))

        # Comments
        comment_fmt = QTextCharFormat()
        comment_fmt.setForeground(QColor("#6E7681"))
        comment_fmt.setFontItalic(True)
        self.rules.append((re.compile(r"#.*$"), comment_fmt))

    def highlightBlock(self, text: str) -> None:
        for pattern, fmt in self.rules:
            for match in pattern.finditer(text):
                start, end = match.span()
                self.setFormat(start, end - start, fmt)


class QlibCodeEditor(QPlainTextEdit):
    """Monospace code editor with Qlib YAML & Expression syntax highlighting."""

    def __init__(self, initial_text: str = "", read_only: bool = False, parent=None) -> None:
        super().__init__(parent)
        self.setReadOnly(read_only)
        font = QFont("JetBrains Mono", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)
        self.setStyleSheet(
            """
            QPlainTextEdit {
                background-color: #0B0E14;
                color: #E6EDF3;
                border: 1px solid #21283B;
                border-radius: 6px;
                padding: 8px;
                font-family: "JetBrains Mono", "Consolas", monospace;
                font-size: 12px;
                line-height: 1.45;
            }
            """
        )
        self.highlighter = QlibYamlHighlighter(self.document())
        if initial_text:
            self.setPlainText(initial_text)
