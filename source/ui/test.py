# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'main.ui',
# licensing of 'main.ui' applies.
#
# Created: Tue Aug 13 20:21:48 2019
#      by: pyside2-uic  running on PySide2 5.13.0
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets
from fragments import ClientTable

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(720, 480)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")        
        
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 611, 20))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        # ui fragments
        self.load_components()

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QtWidgets.QApplication.translate("MainWindow", "MainWindow", None, -1))

    def load_components(self):
        tbl = ClientTable(self.centralwidget)
        tbl.setGeometry(0, 0, 500, self.centralwidget.parent().height() - self.statusbar.height())
        tbl.set_header('Computer Name', 'IP Address', 'Status', 'DB Checksum')
        tbl.setColumnWidth(0, 150)
        for i in range(30):
            tbl.add_row([
                'PC-%d' % i,
                '192.168.1.%d' % (5+i),
                'OFFLINE',
                'UPDATED'
            ])
        
        btnAllowAlways = QtWidgets.QPushButton(self.centralwidget)
        btnAllowAlways.setText('Allow Always')
        def cb(data):
            print(data)
            tbl.clearSelection()
        btnAllowAlways.clicked.connect(lambda: tbl.with_selected('Computer Name', 'IP Address', 'x', cb=cb))
        btnAllowAlways.setGeometry(550, 10, 120, 25)


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())

