from datetime import datetime, timedelta
import sys
from PyQt5.QtCore import QTimer

# Optional cross-platform fallback
try:
    from plyer import notification as plyer_notification
except ImportError:
    plyer_notification = None

# Optional Windows toast
try:
    from win10toast import ToastNotifier
except ImportError:
    ToastNotifier = None

# macOS pync
try:
    from pync import Notifier
except ImportError:
    Notifier = None


class NotificationManager:
    """Cross-platform native notifications for scheduled blocks."""

    def __init__(self, schedule, settings, utils, parent) -> None:
        self.schedule = schedule
        self.settings = settings
        self.parent = parent
        self.utils = utils  # keep it for global theme if needed

        self.check_interval_ms = 5 * 1000  # 5 seconds
        self.timer = QTimer(self.parent)
        self.timer.timeout.connect(self.check_notifications)
        self.timer.start(self.check_interval_ms)

        self.notified_blocks = set()

        # Initialize Windows toaster if on Windows
        self.win_toaster = ToastNotifier() if sys.platform == "win32" and ToastNotifier else None

    def check_notifications(self) -> None:
        """Check schedule and notify for upcoming blocks."""
        now = datetime.now()
        notif_freq = getattr(self.settings, "notification_frequency", timedelta(minutes=30))

        for block in self.schedule.day(now):
            # Skip meals/breaks
            if any(keyword in block.name.lower() for keyword in ["breakfast", "lunch", "dinner", "break"]):
                continue

            time_until_start = block.start - now

            if timedelta(0) < time_until_start <= notif_freq and block not in self.notified_blocks:
                self.show_notification(block)
                self.notified_blocks.add(block)

    def show_notification(self, block) -> None:
        """Send a cross-platform native notification."""
        title = "yoo hoo"
        message = f"{block.start.strftime('%H:%M')} – {block.name}"

        try:
            if sys.platform == "darwin" and Notifier:  # macOS + pync
                Notifier.notify(message, title=title, sound="Ping")
            elif sys.platform == "win32" and self.win_toaster:  # Windows
                self.win_toaster.show_toast(title, message, duration=5, threaded=True)
            elif plyer_notification:  # fallback / Linux / other
                plyer_notification.notify(
                    title=title,
                    message=message,
                    app_name="Scheduler",
                    timeout=5
                )
            else:
                print(f"Notification: {title} – {message}")  # fallback if nothing available
        except Exception as e:
            print(f"Failed to show notification for '{block.name}': {e}")

    def reset_notifications(self) -> None:
        """Clear all notified blocks to allow re-notification."""
        self.notified_blocks.clear()
