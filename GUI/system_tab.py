import sys

from PyQt6.QtWidgets import (
    QVBoxLayout, 
    QGroupBox, 
    QCheckBox, 
    QPlainTextEdit,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
    QPushButton,
    QScrollArea
    )
from PyQt6.QtGui import (
    QFont,
    )
from PyQt6.QtCore import (
    Qt,
    )

from tables.camera_overview_table import camera_overview_table

class system_tab(QWidget):
    def __init__(self, parent=None):
        super(system_tab, self).__init__(parent)
        # Add the parent to the class
        self.GUI = parent
        # Initialise the log groupbox
        self._init_log_groupbox()
        # Initialise the camera groupbox
        self._init_camera_summary_groupbox()
        # Set the global layout
        self._set_global_layout()

        
    def _init_log_groupbox(self) -> None:
        """
        The function `_init_log_groupbox` creates a group box for logging with checkboxes and a text
        box.
        """
        
        self.log_groupbox = QGroupBox("Log")

        self.check_log_active = QCheckBox("Print to log")
        self.check_log_active.setChecked(True)

        self.check_filter_exp = QCheckBox("Filter by experiment")
        self.check_filter_exp.setChecked(False)
        self.check_filder_setup = QCheckBox("Filter by setup")
        self.check_filder_setup.setChecked(False)

        self.log_textbox = QPlainTextEdit()
        self.log_textbox.setMaximumBlockCount(500)
        self.log_textbox.setFont(QFont('Courier', 12))
        self.log_textbox.setReadOnly(True)
        self._set_log_layout()

    def _set_log_layout(self) -> None:

        self.log_hlayout = QHBoxLayout()
        self.log_hlayout.addWidget(self.check_log_active)
        self.log_hlayout.addWidget(self.check_filter_exp)
        self.log_hlayout.addWidget(self.check_filder_setup)

        self.log_layout = QVBoxLayout()
        self.log_layout.addLayout(self.log_hlayout)
        self.log_layout.addWidget(self.log_textbox)
        self.log_groupbox.setLayout(self.log_layout)
        
    def _init_camera_summary_groupbox(self) -> None:
        '''Initialise the camera summary groupbox'''
        self.camera_groupbox = QGroupBox("Camera Summary")
        self.camera_scroll_container = QScrollArea()
        self.camera_scroll_container.setWidgetResizable(True)
        self.list_available_cameras = camera_overview_table()
        self.camera_scroll_container.setWidget(self.list_available_cameras)
        
        self._init_camera_summary_buttons()

        self._set_camera_layout()

    def _init_camera_summary_buttons(self):
        self.refresh_camera_button = QPushButton('Refresh Camera List')
        # self.start_experiment_button.clicked.connect(self.start_new_experiment)

    def _set_camera_layout(self):
        self.Hlayout_cam_buttons = QHBoxLayout()
        self.Hlayout_cam_buttons.addWidget(self.refresh_camera_button)

        self.Vlayout_exp = QVBoxLayout(self)
        self.Vlayout_exp.addWidget(self.camera_scroll_container)
        self.Vlayout_exp.addLayout(self.Hlayout_cam_buttons)

        self.camera_groupbox.setLayout(self.Vlayout_exp)

        
    def _set_global_layout(self) -> None:
        self.global_vlayout = QVBoxLayout()
        
        # Add sublayouts to the global layout
        self.global_vlayout.addWidget(self.camera_groupbox)
        self.global_vlayout.addWidget(self.log_groupbox)
        
        # Set the layout of the main widget
        self.setLayout(self.global_vlayout)
        