# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'Y:\SGTK\devs\tk-multi-bg-publish\resources\dialog.ui'
#
# Created: Mon May 16 17:23:25 2022
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from sgtk.platform.qt import QtCore, QtGui

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(540, 588)
        self.verticalLayout = QtGui.QVBoxLayout(Dialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.view = QtGui.QTreeView(Dialog)
        self.view.setStyleSheet("show-decoration-selected: 0;")
        self.view.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.view.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.view.setSelectionBehavior(QtGui.QAbstractItemView.SelectItems)
        self.view.setRootIsDecorated(True)
        self.view.setObjectName("view")
        self.view.header().setVisible(False)
        self.verticalLayout.addWidget(self.view)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QtGui.QApplication.translate("Dialog", "Form", None, QtGui.QApplication.UnicodeUTF8))

from . import resources_rc
