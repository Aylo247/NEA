from PyQt5.QtWidgets import QListWidgetItem, QListWidget
from PyQt5.QtGui import QDrag
from PyQt5.QtCore import Qt, QMimeData, QByteArray

class BlockPool(QListWidget):   
    def __init__(self, day_view):
        super().__init__()
        self.day_view = day_view
        self.setFixedWidth(200)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDefaultDropAction(Qt.CopyAction)

        # Only two draggable items: Task and Event
        blocks = [
            {"name": "Task", "type": "task"},
            {"name": "Event", "type": "event"}
        ]

        for b in blocks:
            item = QListWidgetItem(b["name"])
            item.setData(Qt.UserRole, b)
            self.addItem(item)

    def startDrag(self, event):
        item = self.currentItem()
        if not item:
            return

        data = item.data(Qt.UserRole)

        mime = QMimeData()
        mime.setData(
            "application/x-block",
            QByteArray(str(data).encode())
        )

        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.exec(Qt.CopyAction)
