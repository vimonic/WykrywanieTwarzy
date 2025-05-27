import time
import threading
from collections import deque
from datetime import datetime, timedelta

class MetricsCollector:
    """Collects real-time metrics for face recognition system"""

    def __init__(self, max_samples=1000):
        self.max_samples = max_samples

        # Authentication metrics
        self.auth_attempts = deque(maxlen=max_samples)  # (timestamp, success, confidence)
        self.detection_times = deque(maxlen=max_samples)  # (timestamp, detection_time)
        self.confidence_scores = deque(maxlen=max_samples)  # (timestamp, confidence)
        self.face_quality_scores = deque(maxlen=max_samples)  # (timestamp, quality_score)

        # Real-time counters
        self.total_attempts = 0
        self.successful_auths = 0
        self.failed_auths = 0

        # Thread safety
        self.lock = threading.Lock()

    def log_auth_attempt(self, success, confidence, detection_time=0):
        """Log an authentication attempt"""
        with self.lock:
            timestamp = datetime.now()
            self.auth_attempts.append((timestamp, success, confidence))

            if detection_time > 0:
                self.detection_times.append((timestamp, detection_time))

            self.confidence_scores.append((timestamp, confidence))

            self.total_attempts += 1
            if success:
                self.successful_auths += 1
            else:
                self.failed_auths += 1

    def log_face_quality(self, quality_score):
        """Log face detection quality (0-100)"""
        with self.lock:
            timestamp = datetime.now()
            self.face_quality_scores.append((timestamp, quality_score))

    def get_accuracy_over_time(self, hours=1):
        """Get accuracy percentage over specified hours"""
        with self.lock:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_attempts = [a for a in self.auth_attempts if a[0] >= cutoff_time]

            if not recent_attempts:
                return [], []

            # Group by 5-minute intervals
            intervals = {}
            for timestamp, success, _ in recent_attempts:
                # Round to 5-minute interval
                interval = timestamp.replace(second=0, microsecond=0)
                interval = interval.replace(minute=(interval.minute // 5) * 5)

                if interval not in intervals:
                    intervals[interval] = {'total': 0, 'success': 0}

                intervals[interval]['total'] += 1
                if success:
                    intervals[interval]['success'] += 1

            # Convert to lists for plotting
            times = sorted(intervals.keys())
            accuracies = [intervals[t]['success'] / intervals[t]['total'] * 100 for t in times]

            return times, accuracies

    def get_confidence_distribution(self, hours=1):
        """Get confidence score distribution"""
        with self.lock:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_scores = [score for timestamp, score in self.confidence_scores if timestamp >= cutoff_time]
            return recent_scores

    def get_detection_time_stats(self, hours=1):
        """Get detection time statistics"""
        with self.lock:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_times = [dt for timestamp, dt in self.detection_times if timestamp >= cutoff_time]
            return recent_times

    def get_current_stats(self):
        """Get current overall statistics"""
        with self.lock:
            accuracy = (self.successful_auths / self.total_attempts * 100) if self.total_attempts > 0 else 0
            return {
                'total_attempts': self.total_attempts,
                'successful_auths': self.successful_auths,
                'failed_auths': self.failed_auths,
                'accuracy': accuracy
            }

# Global metrics collector instance
metrics_collector = MetricsCollector()