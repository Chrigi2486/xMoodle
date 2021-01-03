import os
import sys
import webbrowser
from json import load, dump
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5 import uic
from AppUIs import AppUI, MainPage


class MoodleApp(QMainWindow):
    def __init__(self, *args, **kwargs):

        def check_for_file(filename):
            if not os.path.isfile(filename):
                with open(filename, 'w') as wfile:
                    wfile.write('{}')
                return False
            return True

        super().__init__(*args, **kwargs)
        self.setWindowTitle('xMoodle')
        uic.loadUi('mainpage.ui', self)

        if not check_for_file('./config.json'):
            self.set_default_settings()

        with open('./config.json', 'r') as configfile:
            self.config = load(configfile)
            print(self.config)

        self.explorerButton.clicked.connect(lambda: self.open_explorer(self.config['default_path']))

    def set_default_settings(self):
        with open('./config.json', 'w') as wfile:
            config_dict = {'default_path': None, 'logindata': None, 'courses': None}
            dump(config_dict, wfile)

    def open_explorer(self, path):
        webbrowser.open(f'file:///{path}')  # https://stackoverflow.com/questions/47812372/python-how-to-open-a-folder-on-windows-explorerpython-3-6-2-windows-10/48096286


if __name__ == '__main__':
    app = QApplication(sys.argv)

    moodle_app = MoodleApp()
    moodle_app.show()

    try:
        sys.exit(app.exec_())
    except SystemExit:  # Here I should put all the stuff that should happen when the app closes like data dump
        print('Closing Window')
