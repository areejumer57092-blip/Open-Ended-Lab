import sys
import numpy as np
import pandas as pd
from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox
from PyQt5.QtGui import QPainter, QPdfWriter
from PyQt5.QtCore import Qt
from dashboard_ui import DashboardUI
from signal_processing import SignalProcessing
import pyqtgraph as pg

class TelemetryApp(DashboardUI):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Telemetry Dashboard - PyQt/Python")
        self.resize(1200, 800)
        
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
                    import os
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

    def export_pdf(self):
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, "Export Dashboard as PDF", "Telemetry_Report.pdf", "PDF Files (*.pdf)", options=options)
        
        if file_name:
            try:
                # Grab the entire dashboard visual footprint as High-Res Pixmap
                pixmap = self.grab()
                
                # Initialize PDF Writer targeting the save path
                writer = QPdfWriter(file_name)
                # Maximize resolution
                writer.setResolution(300) 
                
                # Commandeer a QPainter to draw the Pixmap onto the PDF layout
                painter = QPainter(writer)
                rect = painter.viewport()
                size = pixmap.size()
                
                # Scale appropriately maintaining wide landscape aspect ratio
                size.scale(rect.size(), Qt.KeepAspectRatio)
                painter.setViewport(rect.x(), rect.y(), size.width(), size.height())
                painter.setWindow(pixmap.rect())
                
                painter.drawPixmap(0, 0, pixmap)
                painter.end()
                
                QMessageBox.information(self, "Success", f"Dashboard strictly exported to {file_name}!")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export PDF: {str(e)}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TelemetryApp()
    window.show()
    sys.exit(app.exec_())
