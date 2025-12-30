from PyQt5.QtWidgets import QListWidget, QListWidgetItem, QPushButton, QDialog
from PyQt5.QtCore import Qt, QMimeData, QByteArray
from PyQt5.QtGui import QDrag
import pickle
from dialogs import AddCustomBlockDialog

class BlockPool(QListWidget):   
    def __init__(self, day_view, custom_blocks):
        super().__init__()
        self.day_view = day_view
        self.custom_blocks = custom_blocks
        self.setFixedWidth(200)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDefaultDropAction(Qt.CopyAction)

        # default blocks
        self.blocks = [
            {"name": "Task", "type": "task"},
            {"name": "Event", "type": "event"}
        ]
        
        self.refresh_list()

    def startDrag(self, event):
        item = self.currentItem()
        if not item:
            return

        data = item.data(Qt.UserRole)

        mime = QMimeData()
        mime.setData(
            "application/x-block",
            QByteArray(pickle.dumps(data))
        )

        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.exec(Qt.CopyAction)

    def refresh_list(self):
        self.clear()
        # Add default blocks
        for b in self.blocks:
            item = QListWidgetItem(b["name"])
            item.setData(Qt.UserRole, b)
            self.addItem(item)
        
        # Add custom templates
        for template in self.custom_blocks.templates:
            # mark as custom so dropEvent knows
            custom_data = template.copy()
            custom_data["is_custom"] = True
            item = QListWidgetItem(template["name"])
            item.setData(Qt.UserRole, custom_data)
            self.addItem(item)

    def create_custom_block(self):
        dlg = AddCustomBlockDialog(utils=self.day_view.util, parent=self)
        if dlg.exec_() != QDialog.Accepted:
            return

        # Get data from the dialog
        data = dlg.get_data()

        # Add the new block as a template
        self.custom_blocks.add_template(data)  # you already have a method for adding

        # Refresh the pool list
        self.refresh_list()
