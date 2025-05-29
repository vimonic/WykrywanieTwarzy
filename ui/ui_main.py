from PyQt6 import QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(600, 400)

        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.btnAddEmployee = QtWidgets.QPushButton("Dodaj Pracownika", self.centralwidget)
        self.btnAddEmployee.setGeometry(50, 50, 200, 50)
        self.btnRecognize = QtWidgets.QPushButton("Rozpoznawanie Twarzy", self.centralwidget)
        self.btnRecognize.setGeometry(50, 150, 200, 50)

        MainWindow.setCentralWidget(self.centralwidget)
