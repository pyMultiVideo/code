import PyQt6.QtGui as QtGui, PyQt6.QtWidgets as QtWidgets

from PyQt6.QtWidgets import (
    QVBoxLayout,
    QGroupBox,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget
    )


class encoder_tab(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(encoder_tab, self).__init__(parent)

        self.GUI = parent
        
        self._init_encoder_groupbox()
        self._set_encoder_layout()
        
        # self.setLayout(self.encoder_groupbox)
        # self.write(self.GUI.encoder_config)
        
    def _init_encoder_groupbox(self):
        self.encoder_groupbox = QGroupBox("Encoder")
        
        self.encoder_textbox = QPlainTextEdit()
        self.encoder_textbox.setMaximumBlockCount(500)
        self.encoder_textbox.setFont(QtGui.QFont('Courier', 12))
        self.encoder_textbox.setReadOnly(True)
        for key, value in self.GUI.recording_config.items():
            self.encoder_textbox.insertPlainText(f'{key}: {value}\n')
        self._set_encoder_layout()
        
    def _set_encoder_layout(self):
        self.settings_layout = QVBoxLayout()
        self.settings_layout.addWidget(self.encoder_textbox)
        self.encoder_groupbox.setLayout(self.settings_layout)
        

        
        
        
