# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'inst_p2.ui',
# licensing of 'inst_p2.ui' applies.
#
# Created: Wed Aug 14 16:17:22 2019
#      by: pyside2-uic  running on PySide2 5.13.0
#
# WARNING! All changes made in this file will be lost!

from PySide2 import QtCore, QtGui, QtWidgets
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
import re

class Ui_WizardPage(object):
    def setupUi(self, WizardPage: QtWidgets.QWizardPage):
        WizardPage.setObjectName("WizardPage")
        WizardPage.resize(412, 300)
        self.formLayoutWidget = QtWidgets.QWidget(WizardPage)
        self.formLayoutWidget.setGeometry(QtCore.QRect(20, 30, 371, 211))
        self.formLayoutWidget.setObjectName("formLayoutWidget")
        self.formLayout = QtWidgets.QFormLayout(self.formLayoutWidget)
        self.formLayout.setContentsMargins(0, 0, 0, 0)
        self.formLayout.setObjectName("formLayout")
        self.label_2 = QtWidgets.QLabel(self.formLayoutWidget)
        self.label_2.setObjectName("label_2")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label_2)
        self.leTCPPort = QtWidgets.QLineEdit(self.formLayoutWidget)
        self.leTCPPort.setObjectName("leTCPPort")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.leTCPPort)
        self.label_3 = QtWidgets.QLabel(self.formLayoutWidget)
        self.label_3.setObjectName("label_3")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.label_3)
        self.leUDPPort = QtWidgets.QLineEdit(self.formLayoutWidget)
        self.leUDPPort.setObjectName("leUDPPort")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.leUDPPort)
        self.label_4 = QtWidgets.QLabel(self.formLayoutWidget)
        self.label_4.setObjectName("label_4")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.label_4)
        self.leMGrp = QtWidgets.QLineEdit(self.formLayoutWidget)
        self.leMGrp.setObjectName("leMGrp")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.leMGrp)
        self.label_5 = QtWidgets.QLabel(self.formLayoutWidget)
        self.label_5.setObjectName("label_5")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.label_5)

        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.rbClient = QtWidgets.QRadioButton(self.formLayoutWidget)
        self.rbClient.setChecked(True)
        self.rbClient.setObjectName("rbClient")
        self.verticalLayout_2.addWidget(self.rbClient)

        self.hLayoutPubKey = QtWidgets.QHBoxLayout()
        self.hLayoutPubKey.setObjectName("hLayoutPubKey")
        self.lePubKey = QtWidgets.QLineEdit(self.formLayoutWidget)
        self.lePubKey.setObjectName("lePubKey")
        self.lePubKey.setPlaceholderText("public_key file")
        self.hLayoutPubKey.addWidget(self.lePubKey)
        self.tbBrowse = QtWidgets.QToolButton(self.formLayoutWidget)
        self.tbBrowse.setObjectName("tbBrowse")
        self.tbBrowse.setText("...")
        self.hLayoutPubKey.addWidget(self.tbBrowse)
        self.verticalLayout_2.addLayout(self.hLayoutPubKey)

        self.rbMaster = QtWidgets.QRadioButton(self.formLayoutWidget)
        self.rbMaster.setObjectName("rbMaster")
        self.verticalLayout_2.addWidget(self.rbMaster)
        self.formLayout_3 = QtWidgets.QFormLayout()
        self.formLayout_3.setObjectName("formLayout_3")
        self.label_6 = QtWidgets.QLabel(self.formLayoutWidget)
        self.label_6.setObjectName("label_6")
        self.formLayout_3.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label_6)
        self.lePass = QtWidgets.QLineEdit(self.formLayoutWidget)
        self.lePass.setEchoMode(QtWidgets.QLineEdit.Password)
        self.lePass.setObjectName("lePass")
        self.formLayout_3.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.lePass)
        self.lePassConfirm = QtWidgets.QLineEdit(self.formLayoutWidget)
        self.lePassConfirm.setEchoMode(QtWidgets.QLineEdit.Password)
        self.lePassConfirm.setObjectName("lePassConfirm")
        self.formLayout_3.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.lePassConfirm)
        self.verticalLayout_2.addLayout(self.formLayout_3)
        self.horizontalLayout_2.addLayout(self.verticalLayout_2)
        self.formLayout.setLayout(3, QtWidgets.QFormLayout.FieldRole, self.horizontalLayout_2)

        self.retranslateUi(WizardPage)
        QtCore.QMetaObject.connectSlotsByName(WizardPage)

        WizardPage.isComplete = self.isComplete
        self._public_key = None
        self.valid_ip = re.compile(r'(?:\d{1,3}\.){3}(\d{1,3})$')
        self.valid_port = re.compile(r'(\d{1,})$')
        self.valid_keyext = re.compile(r'^[a-zA-Z0-9_-]*(\.pem)$')
        self.toggleEdit()
        self.rbClient.clicked.connect(WizardPage.completeChanged)
        self.rbClient.clicked.connect(self.toggleEdit)
        self.rbMaster.clicked.connect(WizardPage.completeChanged)
        self.rbMaster.clicked.connect(self.toggleEdit)
        self.lePass.textChanged.connect(WizardPage.completeChanged)
        self.lePassConfirm.textChanged.connect(WizardPage.completeChanged)
        self.leTCPPort.textChanged.connect(WizardPage.completeChanged)
        self.leUDPPort.textChanged.connect(WizardPage.completeChanged)
        self.leMGrp.textChanged.connect(WizardPage.completeChanged)
        self.tbBrowse.clicked.connect(self.openDialog)
        self.lePubKey.textChanged.connect(self.try_load_public_key)
        self.lePubKey.textChanged.connect(WizardPage.completeChanged)
        return self

    def openDialog(self):
        path = QtWidgets.QFileDialog().getOpenFileName(None, "Select Public key file", None, "RSA Public Key (*.pem)")
        self.lePubKey.setText(path[0])

    def toggleEdit(self):
        forMaster = self.rbMaster.isChecked()
        self.lePass.setEnabled(forMaster)
        self.lePassConfirm.setEnabled(forMaster)
        self.lePubKey.setEnabled(not forMaster)
        self.tbBrowse.setEnabled(not forMaster)

    def isComplete(self):
        try:
            tcp = self.leTCPPort.text()
            udp = self.leUDPPort.text()
            if not self.valid_port.match(tcp):
                raise ValueError('Invalid TCP Port number')
            if not self.valid_port.match(udp):
                raise ValueError('Invalid UDP Port number')
            if int(tcp) == int(udp):
                raise ValueError('TCP and UDP port must not be thesame')
            if not self.valid_ip.match(self.leMGrp.text()):
                raise ValueError('Invalid IP format')
            if self.rbClient.isChecked():
                if not self._public_key:
                    raise ValueError('Invalid Public key')
            if self.rbMaster.isChecked():
                passwd = self.lePass.text()
                if len(passwd) < 5:
                    raise ValueError('Minimum password length 5 characters')
                if passwd != self.lePassConfirm.text():
                    raise ValueError('Password confirm did not match')
        except ValueError as e:
            print(e)
            return False
        else:
            return True

    def try_load_public_key(self, completeChanged):
        try:
            with open(self.lePubKey.text(), 'rb') as key_file:
                self._public_key = serialization.load_pem_public_key(
                    data = key_file.read(),
                    backend = default_backend()
                )
        except:
            self._public_key = None

    def retranslateUi(self, WizardPage):
        WizardPage.setWindowTitle(QtWidgets.QApplication.translate("WizardPage", "WizardPage", None, -1))
        self.label_2.setText(QtWidgets.QApplication.translate("WizardPage", "TCP Port:", None, -1))
        self.label_3.setText(QtWidgets.QApplication.translate("WizardPage", "UDP Port", None, -1))
        self.label_4.setText(QtWidgets.QApplication.translate("WizardPage", "Multicast Group:", None, -1))
        self.label_5.setText(QtWidgets.QApplication.translate("WizardPage", "Service Type:", None, -1))
        self.rbClient.setText(QtWidgets.QApplication.translate("WizardPage", "Client", None, -1))
        self.rbMaster.setText(QtWidgets.QApplication.translate("WizardPage", "Master", None, -1))
        self.label_6.setText(QtWidgets.QApplication.translate("WizardPage", "UI Password:", None, -1))
        self.lePass.setPlaceholderText(QtWidgets.QApplication.translate("WizardPage", "Password", None, -1))
        self.lePassConfirm.setPlaceholderText(QtWidgets.QApplication.translate("WizardPage", "Confirm Password", None, -1))

