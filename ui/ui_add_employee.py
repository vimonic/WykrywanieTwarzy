# Form implementation generated from reading ui file 'add_employee.ui'
from PyQt6 import QtCore, QtGui, QtWidgets

class Ui_AddEmployeeWindow(object):
    def setupUi(self, AddEmployeeWindow):
        AddEmployeeWindow.setObjectName("AddEmployeeWindow")
        AddEmployeeWindow.resize(800, 600)
        self.videoLabel = QtWidgets.QLabel(AddEmployeeWindow)
        self.videoLabel.setGeometry(QtCore.QRect(50, 100, 640, 480))
        self.nameInput = QtWidgets.QLineEdit(AddEmployeeWindow)
        self.nameInput.setGeometry(QtCore.QRect(50, 30, 200, 30))
        self.startButton = QtWidgets.QPushButton(AddEmployeeWindow)
        self.startButton.setGeometry(QtCore.QRect(270, 30, 100, 30))
        self.startButton.setText("Start")
        self.retranslateUi(AddEmployeeWindow)
        QtCore.QMetaObject.connectSlotsByName(AddEmployeeWindow)

    def retranslateUi(self, AddEmployeeWindow):
        _translate = QtCore.QCoreApplication.translate
        AddEmployeeWindow.setWindowTitle(_translate("AddEmployeeWindow", "Dodaj pracownika"))
