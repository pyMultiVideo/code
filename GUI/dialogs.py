from PyQt6.QtWidgets import QMessageBox


def show_info_message(input_text:str):
    info_dialog = QMessageBox()
    info_dialog.setIcon(QMessageBox.Icon.Information)
    info_dialog.setWindowTitle("Information")
    info_dialog.setText(input_text)
    info_dialog.exec()

if __name__ == "__main__":
    pass