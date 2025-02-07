from PyQt6.QtWidgets import QMessageBox

# TA Do we really need this module, most of this functionality could be done using generic pyQT dialogs.
# E.g. info message as a one liner:  QMessageBox.information(None, "Title", "Your message here")


def show_info_message(input_text: str):
    """
    Display an information message dialog box.
    """
    info_dialog = QMessageBox()
    info_dialog.setIcon(QMessageBox.Icon.Information)
    info_dialog.setWindowTitle("Information")
    info_dialog.setText(input_text)
    info_dialog.exec()


def show_warning_message(
    input_text: str, okayButtonPresent: bool, ignoreButtonPresent: bool
) -> bool:
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

    if ignoreButtonPresent and warning_dialog.clickedButton().text() == "Ignore":
        return True
    return False
