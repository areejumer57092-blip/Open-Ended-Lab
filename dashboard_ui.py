from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                             QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QFrame)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPalette, QFont, QLinearGradient, QPainter
import pyqtgraph as pg

# Theme Colors (Muted Dark aesthetic)
BG_COLOR = "#0a0c10"
PANEL_BG = "#12151c"
PANEL_BORDER = "#1e2230"
TEXT_COLOR = "#7b8ca5"
TEXT_PRIMARY = "#e4eaf2"
ACCENT_BLUE = "#00b8d4"
ACCENT_GREEN = "#00e676"
ACCENT_YELLOW = "#ffc947"
ACCENT_RED = "#ff2e6c"
ACCENT_PURPLE = "#b388ff"

pg.setConfigOption('background', PANEL_BG)
pg.setConfigOption('foreground', TEXT_COLOR)
pg.setConfigOptions(antialias=True)

GLOBAL_STYLESHEET = f"""
    QWidget {{
        background-color: {BG_COLOR};
        color: {TEXT_PRIMARY};
        font-family: 'Segoe UI', Inter, Arial, sans-serif;
    }}
    QLabel#HeaderTitle {{
        font-size: 22px;
        font-weight: 700;
        color: {TEXT_PRIMARY};
        background: transparent;
        letter-spacing: 0.5px;
    }}
    QLabel#HeaderSubtitle {{
        font-size: 12px;
        color: {TEXT_COLOR};
        background: transparent;
        letter-spacing: 0.3px;
    }}
    QLabel.panel-title {{
        font-size: 11px;
        text-transform: uppercase;
        color: {TEXT_COLOR};
        font-weight: 700;
        letter-spacing: 1.2px;
        background-color: transparent;
        padding: 4px 0px;
    }}
    QLabel#SectionLabel {{
        font-size: 10px;
        text-transform: uppercase;
        font-weight: 800;
        letter-spacing: 1.5px;
        padding: 6px 8px 3px 8px;
        background: transparent;
    }}
    QTableWidget {{
        background-color: transparent;
        border: none;
        font-size: 12px;
        gridline-color: transparent;
        outline: none;
    }}
    QTableWidget::item {{
        border-bottom: 1px solid rgba(255,255,255,0.04);
        padding: 5px 8px;
    }}
    QHeaderView::section {{
        background-color: transparent;
        border: none;
        color: {TEXT_COLOR};
        font-size: 11px;
    }}
    QPushButton#BtnPrimary {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #00b8d4, stop:1 #0091ea);
        color: #ffffff;
        border: none;
        padding: 8px 22px;
        border-radius: 6px;
        font-size: 13px;
        font-weight: 600;
        letter-spacing: 0.3px;
    }}
    QPushButton#BtnPrimary:hover {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #00e5ff, stop:1 #00b0ff);
    }}
    QPushButton#BtnSecondary {{
        background-color: transparent;
        border: 1px solid {ACCENT_BLUE};
        color: {ACCENT_BLUE};
        padding: 7px 18px;
        border-radius: 6px;
        font-size: 13px;
        font-weight: 500;
    }}
    QPushButton#BtnSecondary:hover {{
        background-color: rgba(0, 184, 212, 0.1);
        border-color: #00e5ff;
        color: #00e5ff;
    }}
    QWidget#Panel {{
        background-color: {PANEL_BG};
        border: 1px solid {PANEL_BORDER};
        border-radius: 10px;
    }}
    QWidget#GlassPanel {{
        background-color: rgba(18, 21, 28, 0.85);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 10px;
    }}
    QScrollArea {{
        background-color: {BG_COLOR};
        border: none;
    }}
"""


class DashboardUI(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet(GLOBAL_STYLESHEET)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 0, 16, 16)
        main_layout.setSpacing(0)

        # ── Gradient Accent Bar ──────────────────────────────────────────
        accent_bar = QFrame()
        accent_bar.setFixedHeight(3)
        accent_bar.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #00b8d4, stop:0.3 #00e676, stop:0.6 #ffc947, stop:1 #ff2e6c);
            border: none;
            border-radius: 0px;
        """)
        main_layout.addWidget(accent_bar)

        # ── Header Region ────────────────────────────────────────────────
        header_widget = QWidget()
        header_widget.setStyleSheet(f"background-color: {BG_COLOR}; border: none;")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(4, 14, 4, 14)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        title = QLabel("⚡  Clinical Telemetry Dashboard")
        title.setObjectName("HeaderTitle")
        subtitle = QLabel("ECG Analysis  •  HRV Metrics  •  Spectral Density  •  Nonlinear Dynamics")
        subtitle.setObjectName("HeaderSubtitle")
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        header_layout.addLayout(title_layout)

        header_layout.addStretch()

        self.btn_export = QPushButton("⬇  Export Report")
        self.btn_export.setObjectName("BtnPrimary")
        self.btn_export.setCursor(Qt.PointingHandCursor)

        self.btn_load_sample = QPushButton("Load Sample Data")
        self.btn_load_sample.setObjectName("BtnSecondary")
        self.btn_load_sample.setCursor(Qt.PointingHandCursor)

        self.btn_upload = QPushButton("Upload File")
        self.btn_upload.setObjectName("BtnSecondary")
        self.btn_upload.setCursor(Qt.PointingHandCursor)

        header_layout.addWidget(self.btn_export)
        header_layout.addWidget(self.btn_load_sample)
        header_layout.addWidget(self.btn_upload)

        main_layout.addWidget(header_widget)

        # ── Separator ────────────────────────────────────────────────────
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {PANEL_BORDER}; border: none;")
        main_layout.addWidget(sep)
        main_layout.addSpacing(12)

        # Plot Grid Layout
        self.grid = QGridLayout()
        self.grid.setSpacing(14)

        # ── Row 0: Waveform (Span 3 cols) ────────────────────────────────
        self.plot_waveform = pg.PlotWidget(title="Filtered ECG Waveform (10s window)")
        self.grid.addWidget(self.create_panel(self.plot_waveform), 0, 0, 1, 3)

        # ── Row 1: HRV Table + PSD Spectrum ──────────────────────────────
        self.table_hrv = QTableWidget()
        self.table_hrv.setColumnCount(2)
        self.table_hrv.horizontalHeader().setVisible(False)
        self.table_hrv.verticalHeader().setVisible(False)
        self.table_hrv.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_hrv.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_hrv.setFocusPolicy(Qt.NoFocus)
        self.table_hrv.setSelectionMode(QTableWidget.NoSelection)
        self.table_hrv.setShowGrid(False)
        self.init_table()

        table_container = QVBoxLayout()
        table_container.setContentsMargins(12, 10, 12, 10)
        table_container.setSpacing(2)
        lbl = QLabel("HRV Measures")
        lbl.setProperty("class", "panel-title")
        table_container.addWidget(lbl)
        table_container.addWidget(self.table_hrv)
        table_widget = QWidget()
        table_widget.setObjectName("Panel")
        table_widget.setLayout(table_container)
        table_widget.setMinimumWidth(310)
        table_widget.setMinimumHeight(280)
        self.grid.addWidget(table_widget, 1, 0)

        # PSD Spectrum (Spans remaining cols)
        self.plot_psd = pg.PlotWidget(title="Spectrum of RR Tachogram")
        self.plot_psd.setLabel('bottom', "Frequency (Hz)")
        self.plot_psd.setLabel('left', "Spectral Density")
        self.grid.addWidget(self.create_panel(self.plot_psd), 1, 1, 1, 2)

        # ── Row 2: Segment View (Spans all cols) ─────────────────────────
        self.plot_segment = pg.PlotWidget(title="Segmentwise HRV analysis")
        self.plot_segment.setMinimumHeight(250)
        legend = self.plot_segment.addLegend()
        legend.anchor((1, 0), (1, 0), offset=(-10, 10))
        self.plot_segment.setLabel('bottom', "Beats")
        self.plot_segment.setLabel('left', "HRV parameters")
        self.grid.addWidget(self.create_panel(self.plot_segment), 2, 0, 1, 3)

        # ── Row 3: The Non-Linear Engine (Anatomy Map) ───────────────────
        engine_container = QWidget()
        engine_layout = QHBoxLayout(engine_container)
        engine_layout.setContentsMargins(0, 0, 0, 0)
        engine_layout.setSpacing(14)

        self.plot_poincare = pg.PlotWidget(title="The Non-Linear Engine: Poincaré Plot Anatomy")
        self.plot_poincare.setLabel('bottom', "RR_n (ms)")
        self.plot_poincare.setLabel('left', "RR_n+1 (ms)")
        engine_layout.addWidget(self.create_panel(self.plot_poincare), stretch=2)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(10)

        def make_block(title, desc, color):
            box = QWidget()
            box.setStyleSheet(f"""
                background-color: rgba(18, 21, 28, 0.9);
                border: 1px solid {color};
                border-left: 3px solid {color};
                border-radius: 6px;
            """)
            l = QVBoxLayout(box)
            l.setContentsMargins(12, 10, 12, 10)
            t = QLabel(title)
            t.setStyleSheet(f"color: {color}; font-weight: 700; font-size: 13px; border: none; background: transparent;")
            d = QLabel(desc)
            d.setStyleSheet("color: #7b8ca5; font-size: 11px; border: none; background: transparent; line-height: 1.4;")
            d.setWordWrap(True)
            l.addWidget(t)
            l.addWidget(d)
            return box

        b1 = make_block("The Geometry of Chaos", "Non-linear HRV does not require strict stationarity, making it highly robust against physiological noise.", ACCENT_YELLOW)
        b2 = make_block("SD1 (Minor Axis)", "Measures dispersion perpendicular to the line of identity. Quantifies short-term beat-to-beat variability (vagal tone / RSA).", ACCENT_BLUE)
        b3 = make_block("SD2 (Major Axis)", "Measures dispersion along the line of identity. Quantifies long-term, continuous variability.", ACCENT_GREEN)
        b4 = make_block("SD1/SD2 Ratio", "A powerful alternative metric for sympathovagal balance.", ACCENT_RED)

        info_layout.addWidget(b1)
        info_layout.addWidget(b2)
        info_layout.addWidget(b3)
        info_layout.addWidget(b4)
        info_layout.addStretch()

        info_container = QWidget()
        info_container.setLayout(info_layout)
        info_container.setMinimumWidth(350)
        engine_layout.addWidget(info_container, stretch=1)

        self.grid.addWidget(engine_container, 3, 0, 1, 3)

        # Wrap Grid in ScrollArea so UI expands beautifully
        grid_widget = QWidget()
        grid_widget.setLayout(self.grid)

        from PyQt5.QtWidgets import QScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(grid_widget)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setStyleSheet(f"background-color: {BG_COLOR};")

        main_layout.addWidget(scroll)

    def create_panel(self, widget):
        container = QWidget()
        container.setObjectName("Panel")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.addWidget(widget)
        return container

    def init_table(self):
        # Section headers + metrics with category colors
        rows = [
            ("section", "TIME DOMAIN", None),
            ("metric", "Mean RR", ACCENT_BLUE),
            ("metric", "HR", ACCENT_BLUE),
            ("metric", "SDNN", ACCENT_BLUE),
            ("metric", "RMSSD", ACCENT_BLUE),
            ("metric", "pNN50", ACCENT_BLUE),
            ("section", "NONLINEAR", None),
            ("metric", "SampEn", ACCENT_GREEN),
            ("metric", "SD1", ACCENT_GREEN),
            ("metric", "SD2", ACCENT_GREEN),
            ("metric", "SD1/SD2 ratio", ACCENT_GREEN),
            ("section", "FREQUENCY DOMAIN", None),
            ("metric", "LF Power", ACCENT_YELLOW),
            ("metric", "HF Power", ACCENT_YELLOW),
            ("metric", "LF/HF ratio", ACCENT_YELLOW),
        ]

        self.table_hrv.setRowCount(len(rows))
        self._metric_row_map = {}  # Maps metric name -> row index

        for i, (row_type, label, color) in enumerate(rows):
            if row_type == "section":
                item = QTableWidgetItem(label)
                item.setForeground(QColor(TEXT_COLOR))
                item.setFont(QFont("Segoe UI", 8, QFont.Bold))
                item.setFlags(Qt.ItemIsEnabled)
                self.table_hrv.setItem(i, 0, item)

                # Empty value cell for section header
                empty = QTableWidgetItem("")
                empty.setFlags(Qt.ItemIsEnabled)
                self.table_hrv.setItem(i, 1, empty)
                self.table_hrv.setRowHeight(i, 28)
            else:
                item = QTableWidgetItem("  " + label)
                item.setForeground(QColor("#9aa8bc"))
                self.table_hrv.setItem(i, 0, item)

                val = QTableWidgetItem("--")
                val.setForeground(QColor(color))
                val.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                val.setFont(QFont("Consolas", 11, QFont.Bold))
                self.table_hrv.setItem(i, 1, val)
                self.table_hrv.setRowHeight(i, 30)

                self._metric_row_map[label] = i

    def update_table(self, td, nl, fd, sampen):
        metric_values = {
            "Mean RR": f"{td.get('mean_rr', '--')} ms",
            "HR": f"{td.get('hr', '--')} bpm",
            "SDNN": f"{td.get('sdnn', '--')} ms",
            "RMSSD": f"{td.get('rmssd', '--')} ms",
            "pNN50": f"{td.get('pnn50', '--')} %",
            "SampEn": sampen,
            "SD1": nl.get('sd1', '--'),
            "SD2": nl.get('sd2', '--'),
            "SD1/SD2 ratio": nl.get('ratio', '--'),
            "LF Power": f"{fd.get('lf', '--')} ms²",
            "HF Power": f"{fd.get('hf', '--')} ms²",
            "LF/HF ratio": fd.get('lfhf', '--'),
        }

        for metric_name, value in metric_values.items():
            row = self._metric_row_map.get(metric_name)
            if row is not None:
                item = self.table_hrv.item(row, 1)
                if item:
                    item.setText(str(value))
