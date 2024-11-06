from PyQt6.QtWidgets import QTableWidget



class camera_overview_table(QTableWidget):
    'List of the cameras and their current settings'
    def __init__(self, parent=None):
        super(camera_overview_table, self).__init__(parent)
        
        # Example headers
        self.header_names = ['Camera', 'Status', 'Resolution', 'Frame Rate', 'Exposure Time', 'Gain', 'White Balance']
        
        self._set_headers()
        
    def _set_headers(self):
        
        self.setColumnCount(len(self.header_names))
        self.setHorizontalHeaderLabels(self.header_names)
        
        pass
    
    