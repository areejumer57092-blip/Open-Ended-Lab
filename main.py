import sys
import os
import numpy as np
import pandas as pd
from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox
from PyQt5.QtGui import QPainter, QImage
from PyQt5.QtCore import Qt, QBuffer, QByteArray
from dashboard_ui import DashboardUI
from signal_processing import SignalProcessing
import pyqtgraph as pg
from datetime import datetime


class TelemetryApp(DashboardUI):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Clinical Telemetry Dashboard")
        self.resize(1200, 800)

        # Store latest computed results for PDF export
        self._last_td = None
        self._last_nl = None
        self._last_fd = None
        self._last_sampen = None
        self._last_nn = None
        self._last_fs = None
        self._last_data_len = None

        # Connect signals
        self.btn_load_sample.clicked.connect(self.load_sample)
        self.btn_upload.clicked.connect(self.upload_file)
        self.btn_export.clicked.connect(self.export_pdf)

    def load_sample(self):
        self.btn_load_sample.setText("Loading...")
        QApplication.processEvents()

        # Generate 60s sample at 250Hz
        fs = 250
        data = SignalProcessing.generate_mock_ecg(fs, 60)
        self.process_data(data, fs)

        self.btn_load_sample.setText("Load Sample Data")

    def upload_file(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Open ECG File", "", "Supported Files (*.csv *.mat *.dat);;CSV (*.csv);;MATLAB (*.mat);;WFDB (*.dat)", options=options)

        if file_name:
            try:
                ecg_data = None

                if file_name.lower().endswith('.csv'):
                    df = pd.read_csv(file_name)
                    for col in df.columns:
                        if pd.api.types.is_numeric_dtype(df[col]):
                            ecg_data = df[col].dropna().values
                            break

                elif file_name.lower().endswith('.mat'):
                    from scipy.io import loadmat
                    mat = loadmat(file_name)
                    for key, val in mat.items():
                        if not key.startswith('__') and isinstance(val, np.ndarray):
                            val_squeeze = np.squeeze(val)
                            if val_squeeze.ndim == 1:
                                ecg_data = val_squeeze
                                break

                elif file_name.lower().endswith('.dat'):
                    try:
                        import wfdb
                        # WFDB format expects name without extension
                        record_name = os.path.splitext(file_name)[0]
                        record = wfdb.rdrecord(record_name)
                        ecg_data = np.squeeze(record.p_signal[:, 0]) # Channel 0
                    except Exception:
                        # Fallback for plain text arrays
                        ecg_data = np.loadtxt(file_name)

                if ecg_data is not None and len(ecg_data) > 500:
                    self.process_data(ecg_data, 250)
                else:
                    QMessageBox.warning(self, "Data Error", "Could not load sufficient valid numeric data from file.")
            except Exception as e:
                QMessageBox.critical(self, "File Error", f"Failed to read file: {str(e)}")

    def process_data(self, data, fs):
        # 0. Filter the raw data to clean baseline wander & noise
        data = SignalProcessing.filter_ecg(data, fs)

        # 1. Processing
        peaks, peak_vals = SignalProcessing.detect_peaks(data, fs)
        nn = SignalProcessing.calculate_nn_intervals(peaks, fs)

        td = SignalProcessing.calc_time_domain(nn)
        nl = SignalProcessing.calc_poincare(nn)
        fd = SignalProcessing.calc_frequency_domain(nn)
        sampen = SignalProcessing.calc_sample_entropy(nn)

        # Store for PDF export
        self._last_td = td
        self._last_nl = nl
        self._last_fd = fd
        self._last_sampen = sampen
        self._last_nn = nn
        self._last_fs = fs
        self._last_data_len = len(data)

        # 2. Update Table
        self.update_table(td, nl, fd, sampen)

        # 3. Update Plots
        self.plot_waveform.clear()
        self.plot_poincare.clear()
        self.plot_psd.clear()
        self.plot_segment.clear()

        # Waveform (only first 10s per requirement)
        ten_sec_samples = min(fs * 10, len(data))
        time_axis = np.linspace(0, 10, ten_sec_samples)
        self.plot_waveform.plot(time_axis, data[:ten_sec_samples], pen=pg.mkPen('#00adb5', width=1.5))

        # Add peak annotation markers in the 10s window
        peaks_10s = peaks[peaks < ten_sec_samples]
        peak_vals_10s = data[peaks_10s]
        peaks_time = peaks_10s / fs

        # Scatter for peaks
        scatter = pg.ScatterPlotItem(x=peaks_time, y=peak_vals_10s, symbol='o', size=8, brush='#ff2a85')
        self.plot_waveform.addItem(scatter)
        self.plot_waveform.setXRange(0, 10)

        # The Non-Linear Engine (Anatomy Map)
        if len(nl['x']) > 0:
            scatter_map = pg.ScatterPlotItem(x=nl['x'], y=nl['y'], symbol='o', size=5, brush=pg.mkBrush(0, 210, 138, 150))
            self.plot_poincare.addItem(scatter_map)

            mean_rr = np.mean(nn) if len(nn) > 0 else 0
            try:
                sd1 = float(nl['sd1'])
                sd2 = float(nl['sd2'])
            except ValueError:
                sd1, sd2 = 0, 0

            if mean_rr > 0 and sd1 > 0 and sd2 > 0:
                # 1. Line of Identity (45 Deg Magenta Dash)
                min_val = min(np.min(nl['x']), np.min(nl['y'])) * 0.8
                max_val = max(np.max(nl['x']), np.max(nl['y'])) * 1.2
                line = pg.PlotDataItem([min_val, max_val], [min_val, max_val], pen=pg.mkPen('#ff2a85', width=1.5, style=Qt.DashLine))
                self.plot_poincare.addItem(line)

                # 2. Parametric Ellipse spanning 2 standard deviations
                t = np.linspace(0, 2*np.pi, 100)
                a = sd2 * 2  # Major Axis
                b = sd1 * 2  # Minor Axis
                theta = np.pi / 4

                ellipse_x = mean_rr + a * np.cos(t) * np.cos(theta) - b * np.sin(t) * np.sin(theta)
                ellipse_y = mean_rr + a * np.cos(t) * np.sin(theta) + b * np.sin(t) * np.cos(theta)

                ellipse_curve = pg.PlotDataItem(ellipse_x, ellipse_y, pen=pg.mkPen('#ff2a85', width=2))
                self.plot_poincare.addItem(ellipse_curve)

                # 3. Axial Vectors (Cross mapping)
                sd2_line = pg.PlotDataItem([mean_rr - a*np.cos(theta), mean_rr + a*np.cos(theta)],
                                           [mean_rr - a*np.sin(theta), mean_rr + a*np.sin(theta)], 
                                           pen=pg.mkPen('w', width=1.5))
                sd1_line = pg.PlotDataItem([mean_rr - b*np.sin(theta), mean_rr + b*np.sin(theta)],
                                           [mean_rr + b*np.cos(theta), mean_rr - b*np.cos(theta)], 
                                           pen=pg.mkPen('w', width=1.5))
                self.plot_poincare.addItem(sd2_line)
                self.plot_poincare.addItem(sd1_line)

                # Labels
                tip2_x = mean_rr + a * np.cos(theta)
                tip2_y = mean_rr + a * np.sin(theta)
                tip1_x = mean_rr - b * np.sin(theta)
                tip1_y = mean_rr + b * np.cos(theta)

                txt_sd2 = pg.TextItem("SD2 (Major Axis)", color='w', anchor=(0, 1))
                txt_sd2.setPos(tip2_x, tip2_y)
                self.plot_poincare.addItem(txt_sd2)

                txt_sd1 = pg.TextItem("SD1 (Minor Axis)", color='w', anchor=(1, 1))
                txt_sd1.setPos(tip1_x, tip1_y)
                self.plot_poincare.addItem(txt_sd1)

        # PSD
        if len(fd['freqs']) > 0:
            self.plot_psd.plot(fd['freqs'], fd['psd'], fillLevel=0, brush=(0, 210, 138, 100), pen=pg.mkPen('#00d28a', width=2))

        # Segment 
        if len(nn) > 70:
            segments = SignalProcessing.calc_segmentwise(nn, window=60)

            # Matched to the reference picture's distinct color theme
            self.plot_segment.plot(segments['hf'], pen=pg.mkPen('#00adb5', width=2), name="HF")
            self.plot_segment.plot(segments['hr'], pen=pg.mkPen('#ffb74d', width=2), name="rMedian (HR)")
            self.plot_segment.plot(segments['rmssd'], pen=pg.mkPen('#ff2a85', width=2), name="RMSSD")
            self.plot_segment.plot(segments['sd_ratio'], pen=pg.mkPen('#00d28a', width=2), name="SD1/SD2")
        elif len(nn) > 0:
            # Fallback simple moving trend for extremely short files 
            window = 5
            if len(nn) > window:
                trend = np.convolve(nn, np.ones(window)/window, mode='valid')
                self.plot_segment.plot(trend, pen=pg.mkPen('#ffb74d', width=2), name="NN Trend")

    # ── PDF Report Generation ────────────────────────────────────────────
    def _render_plot_to_image(self, plot_widget, width=720, height=300):
        """Render a pyqtgraph PlotWidget to a QImage at high resolution."""
        from PyQt5.QtGui import QPixmap
        # Temporarily resize for consistent render
        original_size = plot_widget.size()
        plot_widget.resize(width, height)
        QApplication.processEvents()
        
        pixmap = plot_widget.grab()
        plot_widget.resize(original_size)
        QApplication.processEvents()
        
        # Convert QPixmap to bytes for ReportLab
        buffer = QBuffer()
        buffer.open(QBuffer.ReadWrite)
        pixmap.save(buffer, "PNG")
        return bytes(buffer.data())

    def export_pdf(self):
        if self._last_td is None:
            QMessageBox.warning(self, "No Data", "Please load or upload ECG data before exporting.")
            return

        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Export HRV Analysis Report", 
            f"HRV_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            "PDF Files (*.pdf)", options=options
        )

        if not file_name:
            return

        try:
            self._generate_report(file_name)
            QMessageBox.information(self, "Success", f"Report exported to:\n{file_name}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export PDF:\n{str(e)}")

    def _generate_report(self, filepath):
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm, inch
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
        from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                         TableStyle, Image, PageBreak, HRFlowable)
        from reportlab.graphics.shapes import Drawing, Rect, String, Line
        from reportlab.graphics import renderPDF
        import io
        import tempfile

        td = self._last_td
        nl = self._last_nl
        fd = self._last_fd
        sampen = self._last_sampen
        nn = self._last_nn
        fs = self._last_fs
        data_len = self._last_data_len

        # ── Colors (clean white-background report) ────────────────────
        BLACK = colors.HexColor("#1a1a1a")
        DARK_GRAY = colors.HexColor("#333333")
        MED_GRAY = colors.HexColor("#666666")
        LIGHT_GRAY = colors.HexColor("#999999")
        BORDER = colors.HexColor("#d0d0d0")
        ROW_ALT = colors.HexColor("#f7f8fa")
        HEADER_BG = colors.HexColor("#eef1f5")
        ACCENT = colors.HexColor("#0066cc")
        GREEN_A = colors.HexColor("#1a8a4a")
        AMBER_A = colors.HexColor("#b8860b")

        # ── Styles ───────────────────────────────────────────────────────
        styles = getSampleStyleSheet()

        s_title = ParagraphStyle('ReportTitle', parent=styles['Title'],
            fontSize=22, leading=26, textColor=BLACK,
            fontName='Helvetica-Bold', alignment=TA_LEFT, spaceAfter=2)

        s_subtitle = ParagraphStyle('ReportSubtitle', parent=styles['Normal'],
            fontSize=10, leading=13, textColor=MED_GRAY,
            fontName='Helvetica', alignment=TA_LEFT, spaceAfter=10)

        s_section = ParagraphStyle('SectionHead', parent=styles['Heading2'],
            fontSize=13, leading=16, textColor=BLACK,
            fontName='Helvetica-Bold', spaceBefore=10, spaceAfter=4,
            borderWidth=0)

        s_body = ParagraphStyle('BodyText', parent=styles['Normal'],
            fontSize=9, leading=13, textColor=DARK_GRAY,
            fontName='Helvetica', spaceAfter=4)

        s_small = ParagraphStyle('SmallText', parent=styles['Normal'],
            fontSize=8, leading=10, textColor=LIGHT_GRAY,
            fontName='Helvetica')

        s_label = ParagraphStyle('MetricLabel', parent=styles['Normal'],
            fontSize=9, leading=12, textColor=DARK_GRAY,
            fontName='Helvetica')

        s_value = ParagraphStyle('MetricValue', parent=styles['Normal'],
            fontSize=10, leading=13, textColor=BLACK,
            fontName='Helvetica-Bold', alignment=TA_RIGHT)

        s_cat_header = ParagraphStyle('CategoryHeader', parent=styles['Normal'],
            fontSize=8, leading=11, textColor=MED_GRAY,
            fontName='Helvetica-Bold', spaceBefore=0, spaceAfter=0)

        # ── Build Document ───────────────────────────────────────────────
        doc = SimpleDocTemplate(
            filepath, pagesize=A4,
            leftMargin=20*mm, rightMargin=20*mm,
            topMargin=20*mm, bottomMargin=20*mm
        )

        story = []

        # ── PAGE 1: Header + Metrics ─────────────────────────────────────

        # Top accent line
        story.append(HRFlowable(width="100%", thickness=2, color=ACCENT, spaceAfter=8))

        # Title
        story.append(Paragraph("HRV Analysis Report", s_title))
        story.append(Paragraph(
            f"Generated: {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}  |  "
            f"Clinical Telemetry Dashboard",
            s_subtitle
        ))

        # Signal Metadata
        story.append(Paragraph("Signal Information", s_section))
        duration_s = data_len / fs if fs > 0 else 0
        n_beats = len(nn) if nn is not None else 0

        meta_data = [
            [Paragraph("Parameter", s_cat_header), Paragraph("Value", s_cat_header)],
            [Paragraph("Sampling Rate", s_label), Paragraph(f"{fs} Hz", s_value)],
            [Paragraph("Signal Duration", s_label), Paragraph(f"{duration_s:.1f}s ({duration_s/60:.1f} min)", s_value)],
            [Paragraph("Total Samples", s_label), Paragraph(f"{data_len:,}", s_value)],
            [Paragraph("Detected Beats (NN)", s_label), Paragraph(f"{n_beats}", s_value)],
            [Paragraph("Ectopic Rejection", s_label), Paragraph("20% Quotient Rule", s_value)],
            [Paragraph("Bandpass Filter", s_label), Paragraph("0.5–45 Hz (Butterworth 3rd)", s_value)],
        ]

        meta_table = Table(meta_data, colWidths=[doc.width * 0.50, doc.width * 0.50])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HEADER_BG),
            ('TEXTCOLOR', (0, 0), (-1, -1), BLACK),
            ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, ROW_ALT]),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 6))

        # ── HRV Metrics Table ────────────────────────────────────────────
        story.append(Paragraph("Heart Rate Variability Metrics", s_section))

        def metric_row(label, value):
            return [
                Paragraph(f"&nbsp;&nbsp;{label}", s_label),
                Paragraph(str(value), s_value)
            ]

        hrv_data = [
            [Paragraph("TIME DOMAIN", ParagraphStyle('TDHead', parent=s_cat_header, textColor=ACCENT)),
             Paragraph("", s_label)],
            metric_row("Mean RR Interval", f"{td.get('mean_rr', '--')} ms"),
            metric_row("Heart Rate", f"{td.get('hr', '--')} bpm"),
            metric_row("SDNN", f"{td.get('sdnn', '--')} ms"),
            metric_row("RMSSD", f"{td.get('rmssd', '--')} ms"),
            metric_row("pNN50", f"{td.get('pnn50', '--')} %"),
            [Paragraph("NONLINEAR ANALYSIS", ParagraphStyle('NLHead', parent=s_cat_header, textColor=GREEN_A)),
             Paragraph("", s_label)],
            metric_row("Sample Entropy (SampEn)", str(sampen)),
            metric_row("SD1 (Short-term)", str(nl.get('sd1', '--'))),
            metric_row("SD2 (Long-term)", str(nl.get('sd2', '--'))),
            metric_row("SD1/SD2 Ratio", str(nl.get('ratio', '--'))),
            [Paragraph("FREQUENCY DOMAIN", ParagraphStyle('FDHead', parent=s_cat_header, textColor=AMBER_A)),
             Paragraph("", s_label)],
            metric_row("LF Power (0.04–0.15 Hz)", f"{fd.get('lf', '--')} ms\u00b2"),
            metric_row("HF Power (0.15–0.40 Hz)", f"{fd.get('hf', '--')} ms\u00b2"),
            metric_row("LF/HF Ratio", str(fd.get('lfhf', '--'))),
        ]

        hrv_table = Table(hrv_data, colWidths=[doc.width * 0.55, doc.width * 0.45])

        table_style_cmds = [
            ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]

        for sec_row in [0, 6, 11]:
            table_style_cmds.append(('BACKGROUND', (0, sec_row), (-1, sec_row), HEADER_BG))

        data_rows = [i for i in range(len(hrv_data)) if i not in [0, 6, 11]]
        for idx, row_i in enumerate(data_rows):
            bg = colors.white if idx % 2 == 0 else ROW_ALT
            table_style_cmds.append(('BACKGROUND', (0, row_i), (-1, row_i), bg))

        hrv_table.setStyle(TableStyle(table_style_cmds))
        story.append(hrv_table)

        # ── PAGE 2: Charts ───────────────────────────────────────────────
        story.append(PageBreak())
        story.append(HRFlowable(width="100%", thickness=2, color=ACCENT, spaceAfter=6))
        story.append(Paragraph("Waveform & Spectral Analysis", s_section))
        story.append(Paragraph(
            "Filtered ECG waveform (first 10s) with R-peaks annotated. "
            "PSD computed via Welch's method after cubic spline interpolation at 4 Hz.",
            s_body
        ))
        story.append(Spacer(1, 4))

        # Render charts to temp PNG files
        temp_dir = os.path.join(os.path.dirname(filepath), ".report_tmp")
        os.makedirs(temp_dir, exist_ok=True)

        try:
            chart_configs = [
                (self.plot_waveform, "ecg_waveform.png", "Filtered ECG Waveform (10s Window)", 700, 260),
                (self.plot_psd, "psd_spectrum.png", "Power Spectral Density of RR Tachogram", 700, 260),
                (self.plot_poincare, "poincare_plot.png", "Poincaré Plot — Nonlinear Dynamics", 700, 340),
                (self.plot_segment, "segment_trend.png", "Segmentwise HRV Trend Analysis", 700, 260),
            ]

            image_paths = []
            for plot_widget, fname, caption, w, h in chart_configs:
                img_bytes = self._render_plot_to_image(plot_widget, w, h)
                img_path = os.path.join(temp_dir, fname)
                with open(img_path, 'wb') as f:
                    f.write(img_bytes)
                image_paths.append((img_path, caption))

            # Waveform
            story.append(Image(image_paths[0][0], width=doc.width, height=155))
            story.append(Paragraph(image_paths[0][1], ParagraphStyle(
                'Caption', parent=s_small, alignment=TA_CENTER, spaceBefore=1, spaceAfter=6,
                textColor=LIGHT_GRAY, fontName='Helvetica-Oblique')))

            # PSD
            story.append(Image(image_paths[1][0], width=doc.width, height=155))
            story.append(Paragraph(image_paths[1][1], ParagraphStyle(
                'Caption', parent=s_small, alignment=TA_CENTER, spaceBefore=1, spaceAfter=6,
                textColor=LIGHT_GRAY, fontName='Helvetica-Oblique')))

            # ── PAGE 3: Nonlinear + Trend ────────────────────────────────
            story.append(PageBreak())
            story.append(HRFlowable(width="100%", thickness=2, color=ACCENT, spaceAfter=6))
            story.append(Paragraph("Nonlinear & Trend Analysis", s_section))
            story.append(Paragraph(
                "Poincar\u00e9 plot maps RR(n) vs RR(n+1). SD1 = short-term vagal variability, "
                "SD2 = long-term dynamics. Segmentwise analysis uses a sliding window.",
                s_body
            ))
            story.append(Spacer(1, 4))

            # Poincaré
            story.append(Image(image_paths[2][0], width=doc.width, height=200))
            story.append(Paragraph(image_paths[2][1], ParagraphStyle(
                'Caption2', parent=s_small, alignment=TA_CENTER, spaceBefore=1, spaceAfter=6,
                textColor=LIGHT_GRAY, fontName='Helvetica-Oblique')))

            # Segment trend
            story.append(Image(image_paths[3][0], width=doc.width, height=155))
            story.append(Paragraph(image_paths[3][1], ParagraphStyle(
                'Caption3', parent=s_small, alignment=TA_CENTER, spaceBefore=1, spaceAfter=6,
                textColor=LIGHT_GRAY, fontName='Helvetica-Oblique')))

            # ── Footer / Disclaimer ──────────────────────────────────────
            story.append(Spacer(1, 10))
            story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceAfter=4))
            story.append(Paragraph(
                "This report was generated by the Clinical Telemetry Dashboard. "
                "Metrics follow ESC Task Force (1996) standards. "
                "For research/educational use only — not a clinical diagnosis.",
                ParagraphStyle('Disclaimer', parent=s_small, textColor=LIGHT_GRAY, spaceBefore=2)
            ))
            story.append(Paragraph(
                f"Report ID: RPT-{datetime.now().strftime('%Y%m%d%H%M%S')}  |  "
                f"Welch PSD + Poincar\u00e9 Geometry  |  Butterworth BPF 0.5-45Hz",
                ParagraphStyle('FooterMeta', parent=s_small, textColor=colors.HexColor("#aaaaaa"))
            ))

            # ── Build ────────────────────────────────────────────────────
            doc.build(story)

        finally:
            # Clean up temp images
            import shutil
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TelemetryApp()
    window.show()
    sys.exit(app.exec_())
