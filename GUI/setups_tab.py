import PyQt6.QtGui as QtGui, PyQt6.QtWidgets as QtWidgets

from PyQt6.QtWidgets import (
    QVBoxLayout,
    QGroupBox,
    QPlainTextEdit,
    QVBoxLayout,
    QHBoxLayout,
    QWidget
    )

from tables.camera_overview_table import camera_overview_table

class setups_tab(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(setups_tab, self).__init__(parent)

        self.GUI = parent
        
        self._init_camera_table_groupbox()
        self._set_camera_table_layout()
    
        self._page_layout()
    
    def _init_camera_table_groupbox(self):
        
        self.camera_table_groupbox = QGroupBox("Camera Table")
        self.camera_table = camera_overview_table(parent = self)
    
        self._set_camera_table_layout()
        
    def _set_camera_table_layout(self):
        
        self.camera_table_layout = QVBoxLayout()
        self.camera_table_layout.addWidget(self.camera_table)
        self.camera_table_groupbox.setLayout(self.camera_table_layout)
        
    def _page_layout(self):
        
        self.page_layout = QHBoxLayout()
        self.page_layout.addWidget(self.camera_table_groupbox)
        self.setLayout(self.camera_table_layout)