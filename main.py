import sys
from PyQt5.QtWidgets import QApplication
from ui.login_screen import LoginScreen

if __name__ == '__main__':
    app = QApplication(sys.argv)
    login = LoginScreen()
    login.show()
    sys.exit(app.exec_())