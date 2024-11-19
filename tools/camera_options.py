def cbox_update_options(cbox, options, used_cameras_labels, selected):
    """Update the options available in a qcombobox without changing the selection."""
    available_options = sorted(list(set(options) - set(used_cameras_labels)), key=str.lower)
    # print('avialable_options', avialable_options)
    # get the current test from the combobox
    selected = cbox.currentText()
    # print('selected', selected)
    
    if selected:
        available_options = sorted(list(set([selected] + available_options)), key=str.lower)
        i = available_options.index(selected)
    else:  # cbox is currently empty.
        i = 0
        pass
    cbox.clear()
    cbox.addItems(available_options)
    cbox.setCurrentIndex(i)
