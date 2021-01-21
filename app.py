import os
import sys
import asyncio
import traceback
import webbrowser
import subprocess
from json import load, dump
from PyQt5.QtWidgets import QApplication, QMainWindow, QListWidgetItem
from PyQt5 import uic
from aiohttp.client_exceptions import ClientConnectionError
from Moodle import MoodleSession, IncorrectLogindata
from MoodleDataTypes import MoodleCourse, MoodleFile


class MoodleApp(QMainWindow):

    download_running = False

    def __init__(self, *args, **kwargs):

        def check_for_file(filename, l=False):
            if not os.path.isfile(filename):
                with open(filename, 'w') as wfile:
                    wfile.write(('[]' if l else'{}'))
                return False
            return True

        super().__init__(*args, **kwargs)
        uic.loadUi('mainpage.ui', self)

        if not check_for_file('./config.json'):
            self.set_default_settings()

        check_for_file('./files.json', l=True)
        check_for_file('./assignments.json', l=True)

        with open('./config.json', 'r') as configfile:
            self.config = load(configfile)
            print(self.config)

        self.explorerButton.clicked.connect(lambda: self.open_file(self.config['default_path']))
        self.browserButton.clicked.connect(lambda: self.open_browser(self.config['urls']['home']))
        self.downloadButton.clicked.connect(self.run_download)
        self.filesList.itemClicked.connect(lambda item: self.open_explorer(item.path))  # have to fix the single click being called when double clicked
        # self.filesList.itemDoubleClicked.connect(lambda item: self.open_file(item.path))
        # self.assignmentsList.itemDoubleClicked.connect(lambda item: self.open_browser(item.url))

        self.update_files_list()
        self.update_assignments_list()

    def set_default_settings(self):
        with open('./config.json', 'w') as wfile:
            config_dict = {'default_path': None, 'urls': None, 'logindata': None, 'courses': None}
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

        courses = []

        for course in self.config['courses']:
            new_course = MoodleCourse.from_dict(self.config['courses'][course])
            new_course.title = course
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
                        file.path = f'{course.title}/{file.path}'
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


if __name__ == '__main__':
    app = QApplication(sys.argv)

    moodle_app = MoodleApp()
    moodle_app.show()

    try:
        sys.exit(app.exec_())
    except SystemExit:  # Here I should put all the stuff that should happen when the app closes like data dump
        print('Closing Window')
