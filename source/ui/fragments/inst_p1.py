# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'inst_p1.ui',
# licensing of 'inst_p1.ui' applies.
#
# Created: Wed Aug 14 06:05:26 2019
#      by: pyside2-uic  running on PySide2 5.13.0
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets
import re

class Ui_WizardPage(object):
    def setupUi(self, WizardPage: QtWidgets.QWizardPage):
        WizardPage.setObjectName("WizardPage")
        WizardPage.resize(412, 300)
        self.verticalLayoutWidget = QtWidgets.QWidget(WizardPage)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(20, 30, 371, 211))
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtWidgets.QLabel(self.verticalLayoutWidget)
        font = QtGui.QFont()
        font.setPointSize(14)
        self.label.setFont(font)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.textBrowser = QtWidgets.QTextBrowser(self.verticalLayoutWidget)
        self.textBrowser.setObjectName("textBrowser")
        self.verticalLayout.addWidget(self.textBrowser)
        self.checkBox = QtWidgets.QCheckBox(self.verticalLayoutWidget)
        self.checkBox.setObjectName("checkBox")
        self.verticalLayout.addWidget(self.checkBox)

        self.retranslateUi(WizardPage)
        QtCore.QMetaObject.connectSlotsByName(WizardPage)
        
        WizardPage.isComplete = self.isComplete 
        self.checkBox.clicked.connect(WizardPage.completeChanged)
        return self

    def isComplete(self):
        return self.checkBox.isChecked()

    def retranslateUi(self, WizardPage):
        WizardPage.setWindowTitle(QtWidgets.QApplication.translate("WizardPage", "Yalab v1.0", None, -1))
        self.label.setText(QtWidgets.QApplication.translate("WizardPage", "YaLab v0.01", None, -1))
        message = '''
        <html>
            <head>
                <meta name="qrichtext" content="1" />
                <style type="text/css">
                    p, li { white-space: pre-wrap; }
                </style>
            </head>
            <body style=" font-family:\'Sans Serif\'; font-size:9pt; font-weight:400; font-style:normal;">
                <p align="center" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /><span style=" font-weight:600;">Warning</span></p>
                <p align="center" style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-weight:600;"><br /></p>
                <p align="center" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">The developer takes no responsibility in any damages made to the network and security.</p>
                <p align="center" style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p>
                <p align="center" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-weight:600;">Install at your own risk.</span></p>
            </body>
        </html>'''
        self.textBrowser.setHtml(QtWidgets.QApplication.translate("WizardPage", re.sub('\s{2,}|\n','',message)))
        self.checkBox.setText(QtWidgets.QApplication.translate("WizardPage", "I understand and accept.", None, -1))

