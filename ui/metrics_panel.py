import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QGridLayout, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
from metrics.collector import metrics_collector

class MetricsPanel(QWidget):
    """Panel wyświetlający metryki systemu"""

    def __init__(self):
        super().__init__()
        self.init_ui()
        
        # Timer do odświeżania metryk
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_metrics)
        self.update_timer.start(1000)  # Odświeżaj co sekundę

        # Historia metryk
        self.auth_history = []
        self.confidence_history = []
        self.detection_time_history = []
        self.quality_history = []
        self.timestamps = []

    def init_ui(self):
        layout = QVBoxLayout()

        # Tytuł
        title = QLabel("Metryki Systemu")
        title.setFont(QFont('Segoe UI', 18, QFont.Bold))
        title.setStyleSheet('color: #333; margin-bottom: 20px;')
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Grid na metryki i wykresy
        metrics_grid = QGridLayout()
        metrics_grid.setSpacing(20)

        # Statystyki autoryzacji
        auth_frame = self.create_metric_frame("Statystyki Autoryzacji")
        self.total_attempts_label = QLabel("0")
        self.successful_auths_label = QLabel("0")
        self.failed_auths_label = QLabel("0")
        self.avg_confidence_label = QLabel("0.00")
        
        auth_layout = QGridLayout()
        auth_layout.addWidget(QLabel("Całkowita liczba prób:"), 0, 0)
        auth_layout.addWidget(self.total_attempts_label, 0, 1)
        auth_layout.addWidget(QLabel("Udane autoryzacje:"), 1, 0)
        auth_layout.addWidget(self.successful_auths_label, 1, 1)
        auth_layout.addWidget(QLabel("Nieudane autoryzacje:"), 2, 0)
        auth_layout.addWidget(self.failed_auths_label, 2, 1)
        auth_layout.addWidget(QLabel("Średnia pewność:"), 3, 0)
        auth_layout.addWidget(self.avg_confidence_label, 3, 1)
        
        auth_frame.setLayout(auth_layout)
        metrics_grid.addWidget(auth_frame, 0, 0)

        # Statystyki wydajności
        perf_frame = self.create_metric_frame("Wydajność Systemu")
        self.avg_detection_time_label = QLabel("0.00s")
        self.face_quality_label = QLabel("0%")
        
        perf_layout = QGridLayout()
        perf_layout.addWidget(QLabel("Średni czas detekcji:"), 0, 0)
        perf_layout.addWidget(self.avg_detection_time_label, 0, 1)
        perf_layout.addWidget(QLabel("Jakość detekcji twarzy:"), 1, 0)
        perf_layout.addWidget(self.face_quality_label, 1, 1)
        
        perf_frame.setLayout(perf_layout)
        metrics_grid.addWidget(perf_frame, 0, 1)

        # Wykresy
        charts_layout = QGridLayout()
        
        # Wykres kołowy autoryzacji
        self.auth_figure = Figure(figsize=(4, 3))
        self.auth_canvas = FigureCanvas(self.auth_figure)
        self.auth_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        charts_layout.addWidget(self.auth_canvas, 0, 0)

        # Wykres historii pewności
        self.confidence_figure = Figure(figsize=(4, 3))
        self.confidence_canvas = FigureCanvas(self.confidence_figure)
        self.confidence_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        charts_layout.addWidget(self.confidence_canvas, 0, 1)

        # Wykres czasu detekcji
        self.detection_figure = Figure(figsize=(4, 3))
        self.detection_canvas = FigureCanvas(self.detection_figure)
        self.detection_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        charts_layout.addWidget(self.detection_canvas, 1, 0)

        # Wykres jakości detekcji
        self.quality_figure = Figure(figsize=(4, 3))
        self.quality_canvas = FigureCanvas(self.quality_figure)
        self.quality_canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        charts_layout.addWidget(self.quality_canvas, 1, 1)

        metrics_grid.addLayout(charts_layout, 1, 0, 1, 2)

        layout.addLayout(metrics_grid)
        layout.addStretch()
        self.setLayout(layout)

    def create_metric_frame(self, title):
        """Tworzy ramkę dla grupy metryk"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 15px;
            }
            QLabel {
                font-family: 'Segoe UI';
                font-size: 12px;
                color: #333;
            }
        """)
        
        # Dodaj tytuł do ramki
        title_label = QLabel(title)
        title_label.setFont(QFont('Segoe UI', 14, QFont.Bold))
        title_label.setStyleSheet('color: #333; margin-bottom: 10px;')
        
        return frame

    def update_metrics(self):
        """Aktualizuje wyświetlane metryki i wykresy"""
        # Aktualizacja etykiet
        self.total_attempts_label.setText(str(metrics_collector.total_attempts))
        self.successful_auths_label.setText(str(metrics_collector.successful_auths))
        self.failed_auths_label.setText(str(metrics_collector.failed_auths))
        
        # Obliczanie metryk
        avg_confidence = 0
        if metrics_collector.confidence_scores:
            avg_confidence = sum(score for _, score in metrics_collector.confidence_scores) / len(metrics_collector.confidence_scores)
            self.avg_confidence_label.setText(f"{avg_confidence:.2%}")
        
        avg_time = 0
        if metrics_collector.detection_times:
            avg_time = sum(time for _, time in metrics_collector.detection_times) / len(metrics_collector.detection_times)
            self.avg_detection_time_label.setText(f"{avg_time:.2f}s")
        
        avg_quality = 0
        if metrics_collector.face_quality_scores:
            avg_quality = sum(score for _, score in metrics_collector.face_quality_scores) / len(metrics_collector.face_quality_scores)
            self.face_quality_label.setText(f"{avg_quality:.0f}%")

        # Aktualizacja historii
        current_time = datetime.now()
        self.timestamps.append(current_time)
        self.auth_history.append((metrics_collector.successful_auths, metrics_collector.failed_auths))
        self.confidence_history.append(avg_confidence)
        self.detection_time_history.append(avg_time)
        self.quality_history.append(avg_quality)

        # Zachowaj tylko ostatnie 60 próbek (1 minuta przy odświeżaniu co sekundę)
        max_samples = 60
        if len(self.timestamps) > max_samples:
            self.timestamps = self.timestamps[-max_samples:]
            self.auth_history = self.auth_history[-max_samples:]
            self.confidence_history = self.confidence_history[-max_samples:]
            self.detection_time_history = self.detection_time_history[-max_samples:]
            self.quality_history = self.quality_history[-max_samples:]

        # Aktualizacja wykresów
        self.update_auth_chart()
        self.update_confidence_chart()
        self.update_detection_chart()
        self.update_quality_chart()

    def update_auth_chart(self):
        """Aktualizuje wykres kołowy autoryzacji"""
        self.auth_figure.clear()
        ax = self.auth_figure.add_subplot(111)
        
        success = metrics_collector.successful_auths
        failed = metrics_collector.failed_auths
        
        if success + failed > 0:
            sizes = [success, failed]
            labels = ['Udane', 'Nieudane']
            colors = ['#2ecc71', '#e74c3c']
            
            ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            ax.axis('equal')
        else:
            ax.text(0.5, 0.5, 'Brak danych', ha='center', va='center')
            ax.axis('off')
        
        self.auth_figure.suptitle('Statystyki autoryzacji', fontsize=10)
        self.auth_canvas.draw()

    def update_confidence_chart(self):
        """Aktualizuje wykres historii pewności"""
        self.confidence_figure.clear()
        ax = self.confidence_figure.add_subplot(111)
        
        if self.confidence_history:
            ax.plot(self.timestamps, self.confidence_history, 'g-', linewidth=2)
            ax.set_ylim(0, 1)
            ax.set_ylabel('Pewność')
            ax.tick_params(axis='x', rotation=45)
            ax.grid(True, alpha=0.3)
        else:
            ax.text(0.5, 0.5, 'Brak danych', ha='center', va='center')
            ax.axis('off')
        
        self.confidence_figure.suptitle('Historia pewności', fontsize=10)
        self.confidence_figure.tight_layout()
        self.confidence_canvas.draw()

    def update_detection_chart(self):
        """Aktualizuje wykres czasu detekcji"""
        self.detection_figure.clear()
        ax = self.detection_figure.add_subplot(111)
        
        if self.detection_time_history:
            ax.plot(self.timestamps, self.detection_time_history, 'b-', linewidth=2)
            ax.set_ylabel('Czas (s)')
            ax.tick_params(axis='x', rotation=45)
            ax.grid(True, alpha=0.3)
        else:
            ax.text(0.5, 0.5, 'Brak danych', ha='center', va='center')
            ax.axis('off')
        
        self.detection_figure.suptitle('Czas detekcji', fontsize=10)
        self.detection_figure.tight_layout()
        self.detection_canvas.draw()

    def update_quality_chart(self):
        """Aktualizuje wykres jakości detekcji"""
        self.quality_figure.clear()
        ax = self.quality_figure.add_subplot(111)
        
        if self.quality_history:
            ax.plot(self.timestamps, self.quality_history, 'r-', linewidth=2)
            ax.set_ylim(0, 100)
            ax.set_ylabel('Jakość (%)')
            ax.tick_params(axis='x', rotation=45)
            ax.grid(True, alpha=0.3)
        else:
            ax.text(0.5, 0.5, 'Brak danych', ha='center', va='center')
            ax.axis('off')
        
        self.quality_figure.suptitle('Jakość detekcji', fontsize=10)
        self.quality_figure.tight_layout()
        self.quality_canvas.draw() 