
from PyQt6.QtWidgets import (
    QVBoxLayout, 
    QGroupBox, 
    QPlainTextEdit,
    QVBoxLayout,
    QWidget
    )
from PyQt6.QtGui import (
    QFont,
    )

from IPython import embed

class ipython_tab(QWidget):
    def __init__(self, parent=None):
        super(ipython_tab, self).__init__(parent)
        # Add the parent to the class
        self.GUI = parent
        
        self._init_ipython_groupbox()
        
        
        
    def _init_ipython_groupbox(self):
        self.ipython_groupbox = QGroupBox("IPython")
        
        self.ipython_textbox = QPlainTextEdit()
        self.ipython_textbox.setMaximumBlockCount(500)
        self.ipython_textbox.setFont(QFont('Courier', 12))
        self.ipython_textbox.setReadOnly(False)
        self._set_ipython_layout()
        
    def _set_ipython_layout(self):
        layout = QVBoxLayout()
        layout.addWidget(self.ipython_textbox)
        self.ipython_groupbox.setLayout(layout)
        
    def write(self, text):
        self.ipython_textbox.insertPlainText(text)
        
    