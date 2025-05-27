import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
from datetime import datetime, timedelta
import os

from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout,
                             QPushButton, QWidget, QLabel, QMessageBox, QFileDialog)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont

from metrics.collector import metrics_collector


class MetricsWindow(QMainWindow):
    """Window displaying real-time metrics charts"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('System Metrics - Face Recognition')
        self.setGeometry(100, 100, 1200, 800)

        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # Title
        title = QLabel('System Performance Metrics')
        title.setFont(QFont('Segoe UI', 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Control buttons
        btn_layout = QHBoxLayout()

        self.refresh_btn = QPushButton('Odśwież wykresy')
        self.refresh_btn.clicked.connect(self.update_charts)

        self.save_btn = QPushButton('Zapisz wykresy')
        self.save_btn.clicked.connect(self.save_charts)

        self.close_btn = QPushButton('Zamknij')
        self.close_btn.clicked.connect(self.close)

        for btn in [self.refresh_btn, self.save_btn, self.close_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #73198a;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 8px 16px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #451552;
                }
            """)

        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addWidget(self.save_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.close_btn)
        layout.addLayout(btn_layout)

        # Create matplotlib figure
        self.figure = Figure(figsize=(12, 8))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        # Stats label
        self.stats_label = QLabel()
        self.stats_label.setFont(QFont('Segoe UI', 10))
        self.stats_label.setStyleSheet('padding: 10px; background-color: #f0f0f0; border-radius: 5px;')
        layout.addWidget(self.stats_label)

        # Auto-refresh timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_charts)
        self.timer.start(5000)  # Update every 5 seconds

        # Initial chart update
        self.update_charts()

    def update_charts(self):
        """Update all charts with latest data"""
        try:
            self.figure.clear()

            # Create subplots
            ax1 = self.figure.add_subplot(2, 2, 1)
            ax2 = self.figure.add_subplot(2, 2, 2)
            ax3 = self.figure.add_subplot(2, 2, 3)
            ax4 = self.figure.add_subplot(2, 2, 4)

            # 1. Accuracy over time
            self.plot_accuracy_over_time(ax1)

            # 2. Confidence score distribution
            self.plot_confidence_distribution(ax2)

            # 3. Detection time statistics
            self.plot_detection_times(ax3)

            # 4. Authentication success/failure pie chart
            self.plot_auth_summary(ax4)

            # Adjust layout and refresh
            self.figure.tight_layout(pad=2.0)
            self.canvas.draw()

            # Update stats
            self.update_stats_display()

        except Exception as e:
            print(f"Error updating charts: {e}")
            # Show error message on the figure
            self.figure.clear()
            ax = self.figure.add_subplot(1, 1, 1)
            ax.text(0.5, 0.5, f'Błąd podczas aktualizacji wykresów:\n{str(e)}',
                    ha='center', va='center', transform=ax.transAxes,
                    bbox=dict(boxstyle='round', facecolor='red', alpha=0.3))
            ax.set_title('Błąd')
            self.canvas.draw()

    def plot_accuracy_over_time(self, ax):
        """Plot accuracy over time with fixed matplotlib locator"""
        try:
            times, accuracies = metrics_collector.get_accuracy_over_time(hours=2)

            if not times or len(times) == 0:
                ax.text(0.5, 0.5, 'Brak danych', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Dokładność w czasie (2h)', fontsize=12, fontweight='bold')
                return

            # Convert datetime objects to matplotlib dates
            dates = mdates.date2num(times)

            ax.plot(dates, accuracies, 'b-o', markersize=4, linewidth=2)
            ax.set_title('Dokładność w czasie (2h)', fontsize=12, fontweight='bold')
            ax.set_ylabel('Dokładność (%)')
            ax.set_ylim(0, 100)
            ax.grid(True, alpha=0.3)

            # FIXED: Use MaxNLocator to limit number of ticks
            from matplotlib.ticker import MaxNLocator
            ax.xaxis.set_major_locator(MaxNLocator(6))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))

            # Rotate labels
            for label in ax.get_xticklabels():
                label.set_rotation(45)
                label.set_ha('right')

        except Exception as e:
            ax.text(0.5, 0.5, f'Błąd: {str(e)}', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Dokładność w czasie (2h)', fontsize=12, fontweight='bold')

    def plot_confidence_distribution(self, ax):
        """Plot confidence score distribution"""
        try:
            scores = metrics_collector.get_confidence_distribution(hours=1)

            if not scores or len(scores) == 0:
                ax.text(0.5, 0.5, 'Brak danych', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Rozkład pewności (1h)', fontsize=12, fontweight='bold')
                return

            # Create histogram
            ax.hist(scores, bins=min(20, len(scores)), alpha=0.7, color='green', edgecolor='black')
            ax.axvline(x=0.8, color='red', linestyle='--', linewidth=2, label='Próg akceptacji')
            ax.set_title('Rozkład pewności (1h)', fontsize=12, fontweight='bold')
            ax.set_xlabel('Pewność')
            ax.set_ylabel('Liczba prób')
            ax.legend()
            ax.grid(True, alpha=0.3)

        except Exception as e:
            ax.text(0.5, 0.5, f'Błąd: {str(e)}', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Rozkład pewności (1h)', fontsize=12, fontweight='bold')

    def plot_detection_times(self, ax):
        """Plot detection time statistics"""
        try:
            times = metrics_collector.get_detection_time_stats(hours=1)

            if not times or len(times) == 0:
                ax.text(0.5, 0.5, 'Brak danych', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Czasy wykrywania (1h)', fontsize=12, fontweight='bold')
                return

            # Box plot
            bp = ax.boxplot([times], patch_artist=True,
                            boxprops=dict(facecolor='lightblue'),
                            medianprops=dict(color='red', linewidth=2))
            ax.set_title('Czasy wykrywania (1h)', fontsize=12, fontweight='bold')
            ax.set_ylabel('Czas (s)')
            ax.set_xticklabels(['Czas wykrywania'])
            ax.grid(True, alpha=0.3)

            # Add statistics text
            avg_time = np.mean(times)
            max_time = np.max(times)
            min_time = np.min(times)
            ax.text(0.02, 0.98, f'Średni: {avg_time:.2f}s\nMin: {min_time:.2f}s\nMax: {max_time:.2f}s',
                    transform=ax.transAxes, verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

        except Exception as e:
            ax.text(0.5, 0.5, f'Błąd: {str(e)}', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Czasy wykrywania (1h)', fontsize=12, fontweight='bold')

    def plot_auth_summary(self, ax):
        """Plot authentication success/failure summary"""
        try:
            stats = metrics_collector.get_current_stats()

            if stats['total_attempts'] == 0:
                ax.text(0.5, 0.5, 'Brak danych', ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Podsumowanie autoryzacji', fontsize=12, fontweight='bold')
                return

            # Pie chart
            labels = ['Udane', 'Nieudane']
            sizes = [stats['successful_auths'], stats['failed_auths']]
            colors = ['#2ecc71', '#e74c3c']

            # Filter out zero values
            filtered_labels = []
            filtered_sizes = []
            filtered_colors = []

            for i, size in enumerate(sizes):
                if size > 0:
                    filtered_labels.append(labels[i])
                    filtered_sizes.append(size)
                    filtered_colors.append(colors[i])

            if filtered_sizes:
                wedges, texts, autotexts = ax.pie(filtered_sizes, labels=filtered_labels,
                                                  colors=filtered_colors, autopct='%1.1f%%',
                                                  startangle=90, textprops={'fontsize': 10})

                # Add center text with total
                centre_circle = plt.Circle((0, 0), 0.50, fc='white')
                ax.add_artist(centre_circle)
                ax.text(0, 0, f'Łącznie\n{stats["total_attempts"]}', ha='center', va='center',
                        fontsize=12, fontweight='bold')

            ax.set_title('Podsumowanie autoryzacji', fontsize=12, fontweight='bold')

        except Exception as e:
            ax.text(0.5, 0.5, f'Błąd: {str(e)}', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Podsumowanie autoryzacji', fontsize=12, fontweight='bold')

    def update_stats_display(self):
        """Update the statistics display label"""
        try:
            stats = metrics_collector.get_current_stats()

            # Get recent data for additional stats
            recent_scores = metrics_collector.get_confidence_distribution(hours=1)
            recent_times = metrics_collector.get_detection_time_stats(hours=1)

            avg_confidence = np.mean(recent_scores) if recent_scores else 0
            avg_detection_time = np.mean(recent_times) if recent_times else 0

            stats_text = f"""
            📊 Statystyki ogólne: Łączne próby: {stats['total_attempts']} | Udane: {stats['successful_auths']} | Nieudane: {stats['failed_auths']} | Dokładność: {stats['accuracy']:.1f}%
            ⏱️ Ostatnia godzina: Średnia pewność: {avg_confidence:.3f} | Średni czas wykrywania: {avg_detection_time:.2f}s
            """

            self.stats_label.setText(stats_text.strip())

        except Exception as e:
            self.stats_label.setText(f"Błąd podczas aktualizacji statystyk: {str(e)}")

    def save_charts(self):
        """Save charts to disk"""
        try:
            # Create metrics directory if it doesn't exist
            os.makedirs('metrics_reports', exist_ok=True)

            # Generate filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'metrics_reports/face_recognition_metrics_{timestamp}.png'

            # Save the figure
            self.figure.savefig(filename, dpi=300, bbox_inches='tight')

            # Also save as PDF
            pdf_filename = filename.replace('.png', '.pdf')
            self.figure.savefig(pdf_filename, bbox_inches='tight')

            QMessageBox.information(self, 'Zapisano',
                                    f'Wykresy zostały zapisane:\n{filename}\n{pdf_filename}')

        except Exception as e:
            QMessageBox.warning(self, 'Błąd', f'Nie można zapisać wykresów:\n{str(e)}')

    def closeEvent(self, event):
        """Clean up when window is closed"""
        if hasattr(self, 'timer'):
            self.timer.stop()
        event.accept()