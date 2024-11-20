from PyQt6.QtWidgets import QApplication, QMessageBox, QInputDialog

def show_error_message(input_text):
    app = QApplication([])

    error_dialog = QMessageBox()
    error_dialog.setIcon(QMessageBox.Icon.Critical)
    error_dialog.setWindowTitle("Error")
    error_dialog.setText(input_text)
    error_dialog.exec()

def show_info_message(input_text):
    info_dialog = QMessageBox()
    info_dialog.setIcon(QMessageBox.Icon.Information)
    info_dialog.setWindowTitle("Information")
    info_dialog.setText(input_text)
    info_dialog.exec()

if __name__ == "__main__":
    input_text, ok = QInputDialog.getText(None, "Input Dialog", "Enter error message:")
    if ok:
        show_error_message(input_text)