
from PyQt6.QtWidgets import (
    QApplication,
    QTextEdit,
    QPushButton,
    QVBoxLayout, 
    QGroupBox, 
    QPlainTextEdit,
    QVBoxLayout,
    QWidget
    )
from PyQt6.QtGui import (
    QFont,
    )
from PyQt6.QtCore import Qt

from IPython.terminal.embed import InteractiveShellEmbed
from IPython import embed
import sys
from io import StringIO
import threading


# from PyQt6.QtWidgets import QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget, QPushButton

class IPythonConsole(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)  # Prevent user from typing directly
        self.ipython_buffer = StringIO()  # Buffer to hold IPython output

        # Initialize an interactive IPython shell
        self.ipython_shell = InteractiveShellEmbed()
        
        # Redirect output to the text widget
        self.ipython_shell.write = self._append_output

    def _append_output(self, output):
        """Append IPython output to the QTextEdit widget."""
        self.insertPlainText(output)
        self.ensureCursorVisible()

    def run_code(self, code):
        """Run a given code in the IPython shell context."""
        threading.Thread(target=self._execute_code, args=(code,)).start()

    def _execute_code(self, code):
        # Run code asynchronously to avoid freezing the UI
        self.ipython_shell.run_cell(code)

# class MainWindow(QMainWindow):
#     def __init__(self):
#         super().__init__()
#         self.setWindowTitle("Embedded IPython Console in PyQt6")
#         self.setGeometry(100, 100, 800, 600)

#         # Main widget setup
#         main_widget = QWidget(self)
#         self.setCentralWidget(main_widget)

#         # Layout setup
#         layout = QVBoxLayout()
#         main_widget.setLayout(layout)

#         # IPython console widget
#         self.console = IPythonConsole(self)
#         layout.addWidget(self.console)

#         # Run button to execute a predefined code snippet
#         self.run_button = QPushButton("Run Code", self)
#         self.run_button.clicked.connect(self.run_example_code)
#         layout.addWidget(self.run_button)

#     def run_example_code(self):
#         code = "import math\nprint(math.sqrt(16))"
#         self.console.run_code(code)


class iPythonTab(QWidget):
    def __init__(self, parent=None):
        super(iPythonTab, self).__init__(parent)
        # Add the parent to the class
        self.GUI = parent
        
        self._init_ipython_groupbox()
        
        
        
    def _init_ipython_groupbox(self):
        self.console_groupbox = QGroupBox("IPython")
        
        self.run_code_button = QPushButton("Run Code")
        self.run_code_button.clicked.connect(self.run_code)
        
        
        self.console = IPythonConsole()

        self.console.setFont(QFont('Courier', 12))
        self.console.setReadOnly(False)
        self.console.setAcceptRichText(False)
        self._set_ipython_layout()
        
    def _set_ipython_layout(self):
        layout = QVBoxLayout()
        layout.addWidget(self.console)
        layout.addWidget(self.run_code_button)
        self.console_groupbox.setLayout(layout)
        self.setLayout(layout)
        
    def run_code(self):
        code = "import math\nprint(math.sqrt(16))"
        self.console.run_code(code)
        

        
    