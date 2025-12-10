from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QScrollArea
from PyQt5.QtGui import QPainter, QColor, QFont
from PyQt5.QtCore import Qt
import sys

class DayContainer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # constants
        self.hour_height = 120
        self.main_line_height = 3
        self.faint_line_height = 1
        self.num_faint_lines = 3
        self.segment_spacing = (self.hour_height - self.main_line_height - (self.faint_line_height * self.num_faint_lines)) / (self.num_faint_lines + 1)

        self.setMinimumHeight(24 * self.hour_height)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setFont(QFont("Arial", 12))
        painter.setPen( QColor(128,128,128))


        for hour in range(24):
            y_start = int(hour * self.hour_height)

            # MAIN hour line (dark gray)
            painter.fillRect(50, y_start, self.width()-50, self.main_line_height, QColor(128,128,128))

            # Faint lines (light gray)
            current_y = y_start + self.main_line_height
            for _ in range(self.num_faint_lines):
                current_y += self.segment_spacing
                painter.fillRect(50, int(current_y), self.width()-50, self.faint_line_height,  QColor(100,100,100))
                current_y += self.faint_line_height

            # HOUR NUMBER (aligned next to main line)
            text_y = int(y_start + self.main_line_height/2 + 4)  # vertically centered with main line
            painter.setPen(Qt.black)
            painter.drawText(5, text_y, f"{hour:02d}:00")


class DayView(QWidget):
    def __init__(self):
        super().__init__()
        self.setGeometry(300, 100, 350, 900)
        self.setWindowTitle("Day View Left Side")

        layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)

        container = DayContainer()
        scroll.setWidget(container)
        self.show()


app = QApplication(sys.argv)
window = DayView()
sys.exit(app.exec_())
