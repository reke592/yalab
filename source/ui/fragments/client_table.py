#
# client_table.py
#
from PySide2 import QtCore, QtWidgets

class ClientTable(QtWidgets.QTableWidget):
    def __init__(self, parent):
        super(ClientTable, self).__init__(parent)
        self.setEnabled(True)
        self.setObjectName('tblClients')
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.horizontalHeader().setCascadingSectionResizes(False)
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setVisible(False)
        self.setSortingEnabled(True)
        self._header_count = 0

    def set_header(self, *argv):
        self._header_count = len(argv)
        self._header_text = []
        self.setColumnCount(self._header_count)
        for i in range(self._header_count):
            item = QtWidgets.QTableWidgetItem(argv[i])
            self.setHorizontalHeaderItem(i, item)
            self._header_text.append(argv[i].replace(' ', '_'))
   
    def add_row(self, data: list = []):
        if not self._header_count:
            raise ValueError('No defined table headers')
        last_row = self.rowCount()
        self.insertRow(last_row)
        for i in range(self._header_count):
            try:
                v = data[i] or ''
            except:
                v = ''
            self.setItem(last_row, i, QtWidgets.QTableWidgetItem(v))

    def get_selected(self, header_name):
        r = []
        try:
            col_index = self._header_text.index(header_name.replace(' ', '_'))
        except:
            print('Warning: header %s is not defined' % header_name)
        else:
            for i in self.selectionModel().selectedRows():
                r.append(self.item(i.row(), col_index).text())
        return r

    # run callback with selected row data
    def with_selected(self, *header_text, cb=None):
        col_index = []
        T = type(cb).__name__
        if T != 'function' and T != 'method':
            raise Exception('callback must me a function or method')
        # compute header index
        for v in header_text:
            try:
                i = self._header_text.index(v.replace(' ', '_'))
            except:
                 print('Warning: header %s not defined' % v)
            else:
                col_index.append(i)
        # time complexity may varry based on size of columns to fetch
        for i in self.selectionModel().selectedRows():
            data = []
            row = i.row()
            for col in col_index:
                data.append(self.item(row, col).text())
            # run callback
            cb(data)
