from PyQt6 import QtWidgets

class Ui_RecognizeWindow(object):
    def setupUi(self, RecognizeWindow):
        RecognizeWindow.setObjectName("RecognizeWindow")
        RecognizeWindow.resize(400, 300)

        self.centralwidget = QtWidgets.QWidget(RecognizeWindow)
        self.startButton = QtWidgets.QPushButton("Start Rozpoznawania", self.centralwidget)
        self.startButton.setGeometry(120, 70, 150, 40)

        RecognizeWindow.setCentralWidget(self.centralwidget)
