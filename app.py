import os
import sys
import asyncio
import traceback
import webbrowser
import subprocess
from json import load, dump
from PyQt5.QtWidgets import QApplication, QMainWindow, QListWidgetItem, QSystemTrayIcon, QFileDialog, QLineEdit, QAction, QMenu, qApp
from PyQt5.QtGui import QIcon
from PyQt5 import uic, QtCore
from aiohttp.client_exceptions import ClientConnectionError
from Moodle import MoodleSession, MoodleParser, IncorrectLogindata
from MoodleDataTypes import MoodleCourse, MoodleFile


class MoodleApp(QMainWindow):

    download_running = False
    minimised = False

    def __init__(self, *args, **kwargs):

        def check_for_file(filename, l=False):
            if not os.path.isfile(filename):
                with open(filename, 'w') as wfile:
                    wfile.write(('[]' if l else'{}'))
                return False
            return True

        super().__init__(*args, **kwargs)
        uic.loadUi('mainpage.ui', self)
        self.setFixedSize(902, 501)

        if not check_for_file('./config.json'):
            self.set_default_settings()

        with open('./config.json', 'r') as configfile:
            self.config = load(configfile)

        check_for_file('./courses.json', l=True)
        check_for_file('./files.json', l=True)
        check_for_file('./assignments.json', l=True)

        self.settings = Settings(self.config)

        self.tray_icon = QSystemTrayIcon(self)              # https://evileg.com/en/post/68/
        self.tray_icon.setIcon(QIcon('./xmoodleicon.png'))
        open_action = QAction("Open", self)
        quit_action = QAction("Exit", self)
        run_action = QAction("Run", self)
        open_action.triggered.connect(self.show)
        run_action.triggered.connect(self.run_download)
        quit_action.triggered.connect(qApp.quit)
        tray_menu = QMenu()
        tray_menu.addAction(open_action)
        tray_menu.addAction(run_action)
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

        self.settingsButton.clicked.connect(self.settings.show)
        self.explorerButton.clicked.connect(lambda: self.open_file(self.config['default_path']))
        self.browserButton.clicked.connect(lambda: self.open_browser(self.config['urls']['home']))
        self.downloadButton.clicked.connect(self.run_download)
        self.filesList.itemClicked.connect(lambda item: self.open_explorer(item.path))  # have to fix the single click being called when double clicked
        # self.filesList.itemDoubleClicked.connect(lambda item: self.open_file(item.path))
        # self.assignmentsList.itemDoubleClicked.connect(lambda item: self.open_browser(item.url))

        self.update_files_list()
        self.update_assignments_list()

    def show(self):
        self.minimised = False
        super().show()

    def set_default_settings(self):
        with open('./config.json', 'w') as wfile:
            default_urls = {'home': 'https://moodle.ksz.ch/my/', 'login': 'https://moodle.ksz.ch/login/index.php'}
            config_dict = {'default_path': None, 'minimise': True, 'urls': default_urls, 'logindata': None, 'courses': None}
            dump(config_dict, wfile)

    def open_file(self, path):
        webbrowser.open(f'file:///{path}')  # https://stackoverflow.com/questions/47812372/python-how-to-open-a-folder-on-windows-explorerpython-3-6-2-windows-10/48096286

    def open_explorer(self, path):  # might not work on MacOS  https://stackoverflow.com/questions/281888/open-explorer-on-a-file
        subprocess.Popen(f'explorer /select, "{os.path.normpath(path)}"')

    def open_browser(self, url):
        webbrowser.open(url)

    def run_download(self):
        if self.download_running:
            return
        self.download_running = True
        self.downloadLabel.setText('Logging In...')
        self.update()
        loop = asyncio.get_event_loop()
        moodle = MoodleSession(self.config['urls']['home'], self.config['urls']['login'])

        try:
            loop.run_until_complete(moodle.login(self.config['logindata']))
        except IncorrectLogindata:
            self.downloadLabel.setText('Incorrect Logindata')
            self.download_running = False
            return
        except ClientConnectionError:
            self.downloadLabel.setText('No Internet Connection')
            self.download_running = False
            return
        except TimeoutError:
            self.downloadLabel.setText('Bad Network Connection')
            self.download_running = False
            return
        except Exception as e:
            self.downloadLabel.setText('Error')  # Log the error here
            print(traceback.format_exc())
            self.download_running = False
            return

        self.downloadLabel.setText('Gathering Course Content...')
        self.update()

        with open('courses.json', 'r') as courses_file:
            all_courses = load(courses_file)

        courses = []

        for course in all_courses:
            if course['checked']:
                new_course = MoodleCourse.from_dict(course)
                courses.append(new_course)

        course_content = asyncio.gather(*[moodle.get_course_content(course) for course in courses])
        loop.run_until_complete(course_content)

        self.downloadLabel.setText('Comparing Files...')
        self.update()

        with open('files.json', 'r') as files_file:
            downloaded_files = load(files_file)

        downloaded_files_urls = [file['url'] for file in downloaded_files]

        files_to_download = []

        for course in courses:
            for section in course.sections:
                for file in section.files:
                    if file.url not in downloaded_files_urls:
                        file.path = f'{course.name}/{file.path}'
                        files_to_download.append(file)

        self.downloadLabel.setText(f'Downloading Files... ({len(files_to_download)} Files)')

        file_download = [moodle.download_file(file, f"{self.config['default_path']}") for file in files_to_download]
        downloaded_paths = loop.run_until_complete(asyncio.gather(*file_download))

        loop.run_until_complete(moodle.close())

        for i, file in enumerate(files_to_download):
            file.download_path = downloaded_paths[i]

        downloaded_files += [file.to_dict() for file in files_to_download]

        with open('files.json', 'w') as files_file:
            dump(downloaded_files, files_file)

        self.downloadLabel.setText(f'{len(files_to_download)} Files Downloaded')

        self.update_files_list()

        if self.minimised:
            self.tray_icon.showMessage(
                "xMoodle",
                f"{len(files_to_download)} Files Downloaded",
            )

        self.download_running = False

    def update_files_list(self):
        with open('files.json', 'r') as files_file:
            files_to_show = load(files_file)[-50:]

        for file in files_to_show:
            item = QListWidgetItem(f"{file['path'].split('/', 1)[0]}: {file['name']}")
            item.path = file['download_path']
            self.filesList.addItem(item)

    def update_assignments_list(self):
        pass

    def closeEvent(self, event):
        if self.config['minimise']:
            self.minimised = True
            event.ignore()
            self.hide()
            # self.tray_icon.showMessage(
            #     "xMoodle",
            #     "xMoodle was minimised to Tray",
            # )


class Settings(QMainWindow):
    def __init__(self, config, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi('settings.ui', self)

        self.config = config

        self.passwordInput.setEchoMode(QLineEdit.Password)  # https://stackoverflow.com/questions/18275771/pyqt-how-do-make-my-text-have-an-asterisk-on-it
        self.minimiseCheckBox.setChecked(config['minimise'])
        self.saveButton.clicked.connect(self.save_settings)
        self.pathEditButton.clicked.connect(self.get_default_path)
        self.loginEditButton.clicked.connect(self.get_logindata)
        self.coursesRefreshButton.clicked.connect(self.refresh_courses)

        self.update_courses_list()

    def get_default_path(self):  # https://stackoverflow.com/questions/44750439/using-simple-pyqt-ui-to-choose-directory-path-crushing
        default_path = QFileDialog.getExistingDirectory(None, 'Select a folder:', os.path.expanduser('~'))
        print(default_path)
        if default_path:
            self.config['default_path'] = default_path

    def get_logindata(self):
        logindata = {'username': str(self.usernameInput.text()), 'password': str(self.passwordInput.text())}

        self.usernameInput.setText('')
        self.passwordInput.setText('')

        loop = asyncio.get_event_loop()
        moodle = MoodleSession(self.config['urls']['home'], self.config['urls']['login'])

        try:
            loop.run_until_complete(moodle.login(dict(logindata)))
        except IncorrectLogindata:
            self.usernameInput.setText('Incorrect Logindata')
        except ClientConnectionError:
            self.usernameInput.setText('No Internet Connection')
        except TimeoutError:
            self.usernameInput.setText('Bad Network Connection')
        except Exception as e:  # Log the error here
            self.usernameInput.setText('Error')
            print(traceback.format_exc())
        else:
            self.usernameInput.setText('Success')
            self.config['logindata'] = logindata

        loop.run_until_complete(moodle.close())

    def save_settings(self):
        self.config['minimise'] = self.minimiseCheckBox.isChecked()
        with open('./config.json', 'w') as config_file:
            dump(self.config, config_file)

        courses = []
        for i in range(self.coursesList.count()):
            course = self.coursesList.item(i)
            course.course_dict['name'] = MoodleParser.parse_windows(course.text())
            course.course_dict['checked'] = bool(course.checkState())
            courses.append(course.course_dict)

        with open('./courses.json', 'w') as config_file:
            dump(courses, config_file)

        self.hide()

    def refresh_courses(self):
        loop = asyncio.get_event_loop()
        moodle = MoodleSession(self.config['urls']['home'], self.config['urls']['login'])

        try:
            loop.run_until_complete(moodle.login(self.config['logindata']))
        except IncorrectLogindata:
            self.coursesList.addItem('Incorrect Logindata')
            return
        except ClientConnectionError:
            self.coursesList.addItem('No Internet Connection')
            return
        except TimeoutError:
            self.coursesList.addItem('Bad Network Connection')
            return
        except Exception as e:  # Log the error here
            self.coursesList.addItem('Error')
            print(traceback.format_exc())
            return

        courses = loop.run_until_complete(moodle.get_courses())
        loop.run_until_complete(moodle.close())

        with open('courses.json', 'r') as courses_file:
            found_courses = load(courses_file)

        course_urls = [course['url'] for course in found_courses]

        for course in courses:
            if course.url not in course_urls:
                course.checked = False
                found_courses.append(course.to_dict())

        with open('courses.json', 'w') as courses_file:
            dump(found_courses, courses_file)

        self.update_courses_list()

    def update_courses_list(self):
        with open('courses.json', 'r') as courses_file:
            courses = load(courses_file)

        for course in courses:
            item = QListWidgetItem(course['name'])
            item.setCheckState(2 if course['checked'] else 0)
            item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
            item.course_dict = course

            self.coursesList.addItem(item)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    moodle_app = MoodleApp()
    moodle_app.show()

    try:
        sys.exit(app.exec_())
    except SystemExit:  # Here I should put all the stuff that should happen when the app closes like data dump
        print('Closing App')
