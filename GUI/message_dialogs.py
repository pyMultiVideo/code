from PyQt6.QtWidgets import QMessageBox


def show_info_message(input_text: str):
    """
    Display an information message dialog box.
    - Adds info icon to message box
    - Removes need for explicitly writing info_dialog.exec()
    """
    info_dialog = QMessageBox()
    info_dialog.setIcon(QMessageBox.Icon.Information)
    info_dialog.setWindowTitle("Information")
    info_dialog.setText(input_text)
    info_dialog.exec()


def show_warning_message(input_text: str, okayButtonPresent: bool, ignoreButtonPresent: bool) -> bool:
    """
    Displays a warning message with Ignore button.
    Returns True if ignore button clicked else False.
    """
    warning_dialog = QMessageBox()
    warning_dialog.setIcon(QMessageBox.Icon.Warning)
    warning_dialog.setWindowTitle("Warning")
    warning_dialog.setText(input_text)
    if ignoreButtonPresent:
        warning_dialog.addButton("Ignore", QMessageBox.ButtonRole.ActionRole)
    if okayButtonPresent:
        warning_dialog.addButton(QMessageBox.StandardButton.Ok)

    result = warning_dialog.exec()
    if ignoreButtonPresent and result == QMessageBox.ButtonRole.ActionRole:
        return True
    return False
