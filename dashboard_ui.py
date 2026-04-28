from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                             QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPalette, QFont
import pyqtgraph as pg

# Theme Colors (Muted Dark aesthetic)
BG_COLOR = "#0b0d10"
PANEL_BG = "#15181e"
TEXT_COLOR = "#8c9baf"
TEXT_PRIMARY = "#e0e6ed"
ACCENT_BLUE = "#00adb5"
ACCENT_GREEN = "#00d28a"
ACCENT_YELLOW = "#ffb74d"
ACCENT_RED = "#ff2a85"

pg.setConfigOption('background', PANEL_BG)
pg.setConfigOption('foreground', TEXT_COLOR)
pg.setConfigOptions(antialias=True)

class DashboardUI(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet(f"""
            QWidget {{ background-color: {BG_COLOR}; color: {TEXT_PRIMARY}; font-family: Inter, Arial; }}
            QLabel.header {{ font-size: 24px; font-weight: bold; color: {TEXT_PRIMARY}; padding: 10px 0; }}
            QLabel.panel-title {{ font-size: 11px; text-transform: uppercase; color: {TEXT_COLOR}; font-weight: bold; background-color: {PANEL_BG}; }}
            QTableWidget {{ background-color: {PANEL_BG}; border: none; font-size: 12px; }}
            QTableWidget::item {{ border-bottom: 1px solid #232731; padding: 5px; }}
            QHeaderView::section {{ background-color: {PANEL_BG}; border: none; color: {TEXT_COLOR}; font-size: 11px; }}
            QPushButton {{ background-color: transparent; border: 1px solid {ACCENT_BLUE}; color: {ACCENT_BLUE}; padding: 5px 15px; border-radius: 4px; }}
            QPushButton:hover {{ background-color: #002b36; }}
            QWidget#Panel {{ background-color: {PANEL_BG}; border-radius: 8px; }}
        """)

        main_layout = QVBoxLayout(self)

        # Header Region
        header_layout = QHBoxLayout()
        title = QLabel("The Telemetry Dashboard", self)
        title.setProperty("class", "header")
        header_layout.addWidget(title)
        
        self.btn_load_sample = QPushButton("Load Sample Data")
        self.btn_upload = QPushButton("Upload File")
        self.btn_export = QPushButton("Export PDF")
        
        header_layout.addStretch()
        header_layout.addWidget(self.btn_export)
        header_layout.addWidget(self.btn_load_sample)
        header_layout.addWidget(self.btn_upload)
        
        main_layout.addLayout(header_layout)

        # Plot Grid Layout
        self.grid = QGridLayout()
        self.grid.setSpacing(15)

        # --- Top: Waveform (Span 3 cols) ---
        self.plot_waveform = pg.PlotWidget(title="Filtered ECG Waveform (10s window)")
        self.grid.addWidget(self.create_panel(self.plot_waveform), 0, 0, 1, 3)

        # --- Row 1: Tables & Spectrum ---
        # 1. Stats Table
        self.table_hrv = QTableWidget()
        self.table_hrv.setColumnCount(2)
        self.table_hrv.horizontalHeader().setVisible(False)
        self.table_hrv.verticalHeader().setVisible(False)
        self.table_hrv.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_hrv.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_hrv.setFocusPolicy(Qt.NoFocus)
        self.table_hrv.setSelectionMode(QTableWidget.NoSelection)
        self.init_table()
        
        table_container = QVBoxLayout()
        lbl = QLabel("HRV Measures")
        lbl.setProperty("class", "panel-title")
        table_container.addWidget(lbl)
        table_container.addWidget(self.table_hrv)
        table_widget = QWidget()
        table_widget.setObjectName("Panel")
        table_widget.setLayout(table_container)
        table_widget.setMinimumWidth(300) # Prevents table horizontal squishing
        table_widget.setMinimumHeight(250)
        self.grid.addWidget(table_widget, 1, 0)

        # 2. PSD Spectrum (Spans remaining cols)
        self.plot_psd = pg.PlotWidget(title="Spectrum of RR Tachogram")
        self.plot_psd.setLabel('bottom', "Frequency (Hz)")
        self.plot_psd.setLabel('left', "Spectral Density")
        self.grid.addWidget(self.create_panel(self.plot_psd), 1, 1, 1, 2)

        # --- Row 2: Segment View (Spans all cols) ---
        self.plot_segment = pg.PlotWidget(title="Segmentwise HRV analysis")
        self.plot_segment.setMinimumHeight(250) # Prevents vertical squishing
        legend = self.plot_segment.addLegend()
        legend.anchor((1, 0), (1, 0), offset=(-10, 10))
        self.plot_segment.setLabel('bottom', "Beats")
        self.plot_segment.setLabel('left', "HRV parameters")
        self.grid.addWidget(self.create_panel(self.plot_segment), 2, 0, 1, 3)

        # --- Row 3: The Non-Linear Engine (Anatomy Map) ---
        engine_container = QWidget()
        engine_layout = QHBoxLayout(engine_container)
        engine_layout.setContentsMargins(0, 0, 0, 0)
        
        self.plot_poincare = pg.PlotWidget(title="The Non-Linear Engine: Poincaré Plot Anatomy")
        self.plot_poincare.setLabel('bottom', "RR_n (ms)")
        self.plot_poincare.setLabel('left', "RR_n+1 (ms)")
        engine_layout.addWidget(self.create_panel(self.plot_poincare), stretch=2)
        
        info_layout = QVBoxLayout()
        info_layout.setSpacing(10)
        
        def make_block(title, desc, color):
            box = QWidget()
            box.setStyleSheet(f"background-color: {PANEL_BG}; border: 1px solid {color}; border-radius: 6px;")
            l = QVBoxLayout(box)
            l.setContentsMargins(10, 10, 10, 10)
            t = QLabel(title)
            t.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 13px; border: none;")
            d = QLabel(desc)
            d.setStyleSheet("color: #8c9baf; font-size: 11px; border: none;")
            d.setWordWrap(True)
            l.addWidget(t)
            l.addWidget(d)
            return box

        b1 = make_block("The Geometry of Chaos", "Non-linear HRV does not require strict stationarity, making it highly robust against physiological noise.", "#ffb74d")
        b2 = make_block("SD1 (Minor Axis)", "Measures dispersion perpendicular to the line of identity. Quantifies short-term beat-to-beat variability (vagal tone / RSA).", "#00adb5")
        b3 = make_block("SD2 (Major Axis)", "Measures dispersion along the line of identity. Quantifies long-term, continuous variability.", "#00d28a")
        b4 = make_block("SD1/SD2 Ratio", "A powerful alternative metric for sympathovagal balance.", "#ff2a85")
        
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
        layout.setContentsMargins(5, 5, 5, 5)
        layout.addWidget(widget)
        return container

    def init_table(self):
        metrics = ["Mean RR", "HR", "SDNN", "RMSSD", "pNN50", "SampEn", "SD1", "SD2", "SD1/SD2 ratio", "LF Power", "HF Power", "LF/HF ratio"]
        self.table_hrv.setRowCount(len(metrics))
        for i, m in enumerate(metrics):
            item = QTableWidgetItem(m)
            self.table_hrv.setItem(i, 0, item)
            val = QTableWidgetItem("--")
            val.setForeground(QColor(ACCENT_BLUE))
            val.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table_hrv.setItem(i, 1, val)

    def update_table(self, td, nl, fd, sampen):
        values = [
            f"{td.get('mean_rr', '--')} ms",
            f"{td.get('hr', '--')} bpm",
            f"{td.get('sdnn', '--')} ms",
            f"{td.get('rmssd', '--')} ms",
            f"{td.get('pnn50', '--')} %",
            sampen,
            nl.get('sd1', '--'),
            nl.get('sd2', '--'),
            nl.get('ratio', '--'),
            f"{fd.get('lf', '--')} ms²",
            f"{fd.get('hf', '--')} ms²",
            fd.get('lfhf', '--')
        ]
        
        for i, val in enumerate(values):
            item = self.table_hrv.item(i, 1)
            if item:
                item.setText(val)
