from PyQt6.QtWidgets import QMessageBox


def show_info_message(input_text: str):
    """
    The function `show_info_message` displays an information message dialog with the input text in a
    PyQt application.

    :param input_text: The `show_info_message` function takes a string input_text as a parameter. This
    function creates an information dialog box using PyQt5 library in Python and displays the input_text
    as the message in the dialog box
    :type input_text: str
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
    The function `show_warning_message` displays a warning dialog with an input text and allows the user
    to either ignore or acknowledge the warning.

    Function returns a bool (True) when the ignore button is clicked

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


if __name__ == "__main__":
    pass
