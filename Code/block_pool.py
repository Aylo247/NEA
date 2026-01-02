from PyQt5.QtWidgets import QListWidget, QListWidgetItem, QDialog
from PyQt5.QtCore import Qt, QMimeData, QByteArray
from PyQt5.QtGui import QDrag
import pickle
from dialogs import AddCustomBlockDialog

class BlockPool(QListWidget):
    """
    sidebar list containing draggable block templates

    supports default block types and user-defined custom templates,
    which can be dragged into the day view
    """

    def __init__(self, day_view, custom_blocks) -> None:
        super().__init__()
        self.day_view = day_view
        self.custom_blocks = custom_blocks
        self.setFixedWidth(200)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDefaultDropAction(Qt.CopyAction)

        # Default block templates
        self.blocks = [
            {"name": "task", "type": "task"},
            {"name": "event", "type": "event"}
        ]
        
        self.refresh_list()

    def startDrag(self, event) -> None:
        """
        start a drag operation for the currently selected block

        the block metadata is serialised and attached as custom MIME data
        so it can be reconstructed when dropped into a view
        """

        item = self.currentItem()

        # prevnts a None item being packaged
        if not item:
            return

        data = item.data(Qt.UserRole)

        # package block data for drag-and-drop
        mime = QMimeData()
        mime.setData(
            "application/x-block",
            QByteArray(pickle.dumps(data))
        )

        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.exec(Qt.CopyAction)

    def refresh_list(self) -> None:
        """rebuild the block pool from default and custom block templates"""
        #reset the list
        self.clear()

        # add default blocks
        for b in self.blocks:
            item = QListWidgetItem(b["name"])
            item.setData(Qt.UserRole, b)
            self.addItem(item)
        
        # add custom templates
        for template in self.custom_blocks.templates:
            # flag as custom so dropEvent logic can differentiate
            custom_data = template.copy()
            custom_data["is_custom"] = True

            item = QListWidgetItem(template["name"])
            item.setData(Qt.UserRole, custom_data)
            self.addItem(item)

    def create_custom_block(self) -> None:
        """
        open the custom block dialog and add the resulting
        block definition as a reusable template
        """
        dlg = AddCustomBlockDialog(utils=self.day_view.util, customs=self.custom_blocks, parent=self)

        if dlg.exec_() != QDialog.Accepted:
            return

        data = dlg.get_data()

        # add the new block as a template
        self.custom_blocks.add_template(data) 

        # refresh the pool list
        self.refresh_list()
