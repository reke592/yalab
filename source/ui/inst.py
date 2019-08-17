# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'inst_p1.ui',
# licensing of 'inst_p1.ui' applies.
#
# Created: Wed Aug 14 06:05:26 2019
#      by: pyside2-uic  running on PySide2 5.13.0
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets
from fragments import InstallWizardPage1, InstallWizardPage2

if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication()
    Wizard = QtWidgets.QWizard()
    Wizard.addPage(QtWidgets.QWizardPage())
    Wizard.addPage(QtWidgets.QWizardPage())
    Wizard.addPage(QtWidgets.QWizardPage())
    Wizard.resize(430, 350)    
    InstallWizardPage1().setupUi(Wizard.page(0))
    InstallWizardPage2().setupUi(Wizard.page(1))
    Wizard.show()
    sys.exit(app.exec_())
