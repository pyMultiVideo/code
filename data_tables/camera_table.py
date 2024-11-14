'''
File for loading camera data from a csv that is generated on startup.

This is going to be embedded in the experiments tab. 

Important ideas that this captures: 
- The camera name 
- serial number 
- camera settinsg (fps etc)

The information in this table comes from a camera_config_x.csv

''' 

import db as database


import time
from typing import List

from pyqtgraph import Qt
from pyqtgraph.Qt import QtCore, QtGui




class experiment_overview_table(QtGui.QTableWidget):
    " Table for system tab that shows all experiments currently running"

    def __init__(self, only_active: bool = False, parent=None):

        super(QtGui.QTableWidget, self).__init__(1, 7, parent=parent)

        self.header_names = ['Select', 'Name', 'Setups', 'User', 
                             'Active', 'Protocol', 'Subjects',
                             'n_subjects'
                             ]
        self._set_headers()
        self.only_active = only_active

        self.fill_table()

    def _set_headers(self):

        self.setHorizontalHeaderLabels(self.header_names)
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(Qt.QtWidgets.QTableWidget.NoEditTriggers)
        self.select_col_ix = self.header_names.index("Select")

    def fill_table(self):

        self.clearContents()
        if self.only_active:
            self.setRowCount(sum(database.exp_df['Active']))
        else:
            self.setRowCount(len(database.exp_df))

        self.buttons = []
        row_index = 0
        for _, row in database.exp_df.iterrows():
            if ((not self.only_active) or (self.only_active and row['Active'])):
                for col_index in range(self.columnCount()):

                    try:
                        cHeader = self.header_names[col_index]

                        self.setItem(row_index, col_index, Qt.QtWidgets.QTableWidgetItem(str(row[cHeader])))
                    except KeyError:
                        pass

                chkBoxItem = QtGui.QTableWidgetItem()
                chkBoxItem.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
                chkBoxItem.setCheckState(QtCore.Qt.Unchecked)
                self.setItem(row_index, self.select_col_ix, chkBoxItem)
                row_index += 1

    def get_checked_experiments(self) -> List[str]:
        """Check which experiments the user has checked

        Returns:
            List[str]: Names of selected experiments
        """
        selected_experiments = []
        for rowN in range(self.rowCount()):
            if self(rowN, 0).checkState() == 2:  # 2 is checked state
                expName = self.item(rowN, self.header_names.index('Name')).text()
                selected_experiments.append(expName)

        return selected_experiments

    def end_experiments(self, experiment_names: List[str]) -> None:
        """ End experiment by switching off handlers for relevant setups, closing files and updating setup, experiment
            databases.

        Args:
            experiment_names (List[str]): names of experiments to be ended
        """
        for exp_name in experiment_names:
            for setup in database.exp_df.loc[database.exp_df['Name'] == exp_name, 'Setups'].values:
                setup = eval(setup)[0]

                if database.controllers.items():  # if there are any controllers
                    print(exp_name)
                    handler_ = [setup_ for k, setup_ in database.controllers.items() if k == setup][0]

                    handler_.PYC.stop_framework()
                    time.sleep(.05)
                    handler_.PYC.process_data()
                    handler_.close_files()
                    handler_.PYC.reset()

                    database.exp_df.loc[database.exp_df['Name'] == exp_name, 'Active'] = False
                    database.setup_df.loc[database.setup_df['Setup_ID'] == setup, 'Experiment'] = None
                    database.setup_df.to_csv(database.setup_df.file_location)
                    database.exp_df.to_csv(database.exp_df.file_location)

                    print("CLOSED")

                for subject in eval(database.exp_df.loc[database.exp_df['Name'] == exp_name, 'Subjects'].values[0]):
                    database.mouse_df.loc[database.mouse_df['Mouse_ID'] == subject, 'in_system'] = False

