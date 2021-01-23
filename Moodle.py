"""
This file contains the MoodleSession class and all Exception classes
"""

import os
from urllib.parse import unquote        # reference: https://stackoverflow.com/questions/11768070/transform-url-string-into-normal-string-in-python-20-to-space-etc
from datetime import datetime           # reference: https://docs.python.org/3/library/datetime.html

from bs4 import BeautifulSoup as BS     # reference: https://www.crummy.com/software/BeautifulSoup/bs4/doc/
from aiohttp import ClientSession       # reference: https://docs.aiohttp.org/en/stable/client_reference.html
from aiohttp import ClientTimeout

from MoodleDataTypes import (
    MoodleCourse, MoodleSection,
    MoodleFolder, MoodleFile,
    MoodleAssignment, MoodleUrl
)


# All html reference from https://moodle.ksz.ch by viewing page source

class MoodleSession(ClientSession):
    """
    Inherits from aiohttp.ClientSession and is used to access Moodle
    """
    DEFAULT_TIMEOUT = 0.00

    def __init__(self, home_url, login_url, *args, **kwargs):
        """
        The constructor for MoodleSession

        Parameters:
            home_url (str): The URL you get after you login
            login_url (str): The login URL
        """
        self.home_url = home_url
        self.login_url = login_url

        super().__init__(*args,
                         timeout=ClientTimeout(self.DEFAULT_TIMEOUT),
                         **kwargs)

    async def login(self, logindata) -> None:
        """
        Authenticates the MoodleSession with the provided logindata

        Parameters:
            logindata (dict): contains 'username' and 'password'
                              which are used to authenticate
        """
        async def get_logintoken() -> str:
            """
            Retrieves a valid logintoken to use for authentication

            Returns:
                str: A valid logintoken
            """
            async with self.get(self.login_url) as login_page:
                login_html = BS((await login_page.text()), 'html.parser')
                return login_html.find(attrs={'name': 'logintoken'})['value']

        async def post_logindata() -> bool:
            """
            Sends a POST request to authenticate the Session
            and checks if it was successful

            Returns:
                bool: If the authentication was successful
            """
            await self.post(self.login_url, data=logindata, allow_redirects=False)  # allow redirects is set to false as to simulate this process manually as otherwise it doesn't work

            async with self.get(self.home_url) as home_page:
                if str(home_page.url) != self.home_url:  # Checks if the authentication was successful
                    return False
                return True

        logindata['logintoken'] = await get_logintoken()  # Gets the logintoken
        if not await post_logindata():  # Posts the logindata
            raise IncorrectLogindata()  # Raises an exception if the logindata was wrong

    async def get_courses(self) -> list:
        """
        Gets all the courses available for the student

        Returns:
            list: A list of courses
        """
        async with self.get(self.home_url) as homepage:
            course_list = BS(await homepage.text(), 'html.parser').find_all('a')
            courses = []
            for course in course_list:  # Creates a new Course object for each course found
                if 'course' not in course['href']:
                    continue
                new_course = MoodleCourse(course['href'], course.find(class_='media-body').string)
                courses.append(new_course)
        return courses  # returns a list of courses

    async def get_course_content(self, course: MoodleCourse, files=True, assignments=True) -> None:
        """
        Retrieves all the content of the given course

        Parameters:
            course (MoodleCourse): The course from which to get all content
        """
        async with self.get(course.url) as coursepage:
            page_items = BS(await coursepage.text(), 'html.parser').find_all('a')
            for item in page_items:  # This goes through all URLs in the course and finds any relevent URL

                try:
                    item['href']
                except KeyError:
                    continue

                # Perhaps split the url and check if one of the splits is section, resource, url, ...

                if 'section' in item['href']:   # Creates a new MoodleSection instance for each Section
                    if item.string is None:
                        continue
                    section = MoodleSection(item['href'],
                                            MoodleParser.parse_windows(item.string))

                    course.sections.append(section)

                elif 'resource' in item['href'] and files:  # Creates a new MoodleFile instance for each File
                    file = MoodleFile(item['href'],
                                      item.find(class_='instancename').contents[0],
                                      course.sections[-1].name)

                    section.files.append(file)

                elif 'folder' in item['href'] and files:  # Creates a new MoodleFolder instance for each Folder
                    folder = MoodleFolder(item['href'],
                                          MoodleParser.parse_windows(item.find(class_='instancename').contents[0]))

                    await self.get_folder_content(section, folder)

                    section.folders.append(folder)

                elif 'assign' in item['href'] and assignments:  # Creates a new MoodleAssignment instance for each Assignment
                    assignment = MoodleAssignment(item['href'],
                                                  item.find(class_='instancename').contents[0])
                    await self.get_assignment_content(assignment)
                    section.assignments.append(assignment)

                elif 'url' in item['href'] and files:  # Creates a new MoodleUrl instance for each Url
                    file = MoodleUrl(item['href'],
                                     item.find(class_='instancename').contents[0],
                                     course.sections[-1].name)

                    section.files.append(file)

    async def get_assignment_content(self, assignment: MoodleAssignment):
        async with self.get(assignment.url) as assignment_page:
            content = BS(await assignment_page.text(), 'html.parser')
            generalinfo = content.find(class_='generaltable').find_all('tr')
            status = generalinfo[0].td.string
            assignment.status = status != 'No attempt'
            due_date = generalinfo[2].td.string
            assignment.due_date = str(datetime.strptime(due_date, '%A, %d %B %Y, %I:%M %p'))  # https://stackabuse.com/converting-strings-to-datetime-in-python/

    async def get_folder_content(self, section: MoodleSection, folder: MoodleFolder, parentfolder=False):
        async with self.get(folder.url) as folderpage:
            page_items = BS(await folderpage.text(), 'html.parser').find_all('a')

            for item in page_items:
                if '/content/' in item['href']:
                    file = MoodleFile(item['href'].split('?')[0],
                                      item.find(class_='fp-filename').contents[0],
                                      f'{section.name}/{folder.path + "/" if folder.path else ""}{folder.name}')

                    folder.files.append(file)
                    section.files.append(file)  # Simplify downloading and presentation

                # Get the file content for subfiles
                # elif '???' in item['href']:
                #     subfolder = MoodleFolder(item['href'],
                #                              item.find(class_='???').contents[0])

                #     await self.get_folder_content(subfolder, f'{folder.path + "/" if folder.path else ""}{folder.name}')
                #     folder.folders.append(subfolder)

    async def download_file(self, file: MoodleFile, base_path) -> str:
        """
        Downloads a given file to the base path given

        Parameters:
            file (MoodleFile): The file to be downloaded
            base_path (str): The path to which the file is to be downloaded

        Returns:
            str: The final path of the file
        """
        if isinstance(file, MoodleUrl):
            await self.download_url(file, base_path)
            return

        async with self.get(file.url) as file_page:  # https://www.youtube.com/watch?v=E_oIU4IU2W8
            path = f'{base_path}/{file.path}/{unquote(str(file_page.url).split("/")[-1])}'
            os.makedirs(os.path.dirname(path), exist_ok=True)  # https://stackoverflow.com/questions/12517451/automatically-creating-directories-with-file-output
            content = await file_page.read()
            with open(path, 'wb') as new_file:
                new_file.write(content)
        return path

    async def download_url(self, url: MoodleUrl, base_path) -> str:
        """
        Downloads a given url to the base path given

        Parameters:
            url (MoodleUrl): The url to be downloaded
            base_path (str): The path to which the url is to be downloaded

        Returns:
            str: The final path of the url
        """
        async with self.get(url.url) as file_page:
            path = f'{base_path}/{url.path}/{MoodleParser.parse_windows(url.name)}.url'
            os.makedirs(os.path.dirname(path), exist_ok=True)
            content = BS(await file_page.read(), 'html.parser')
            redirect_url = content.find_all(class_='urlworkaround')[0].a['href']
            with open(path, 'w') as new_file:
                new_file.write(f'[InternetShortcut]\nURL={redirect_url}')
        return path

    async def upload_file(self, file_path, assignment: MoodleAssignment):
        """
        Used to upload a file to a target assignment

        Parameters:
            file (str): path of the file to send
            assignment (MoodleAssignment): The target assignment
        """
        if not os.path.exists(file_path):  # Maybe don't check but let it raise the exception
            return

        async with self.get(f'{assignment.url}&action=editsubmission') as assignment_page:
            content = BS(await assignment_page.text(), 'html.parser')
            keys = content.select('#id_files_filemanager_fieldset > noscript')[0].div.object['data']
            item_id = keys.split('&')[2].split('=')[1]
            ctx_id = keys.split('&')[7].split('=')[1]
            sesskey = keys.split('&')[9].split('=')[1]
            userid = content.select('#page-wrapper > nav > ul.nav.navbar-nav.usernav > li:nth-child(1)')[0].div['data-userid']
            title = file_path.split('\\')[-1] if '\\' in file_path else file_path.split('/')[-1]

        async with self.post(f"{self.home_url.split('/my')[0]}?action=upload", data={
                                              'repo_upload_file': open(file_path, 'rb'),
                                              'sesskey': sesskey,
                                              'repo_id': '0',
                                              'item_id': item_id,
                                              # 'author': userid,
                                              'savepath': '/',
                                              'title': title,
                                              'ctx_id': ctx_id,
                                              'accepted_types[]': f"[{title.split('.')[1]}]"
                                              }) as upload:
            print(upload.status)

        async with self.post(f'{assignment.url}&lastmodified={datetime.timestamp(datetime.now())}&userid={userid}&action=savesubmission&sesskey={sesskey}&_qf__mod_assign_submission_form=1&files_filemanager=184629888&submitbutton=Save+changes') as submit:
            print(submit.status)


class IncorrectLogindata(Exception):  # Handling and raising exceptions reference: https://docs.python.org/3/tutorial/errors.html
    """
    Exception raised when the logindata is incorrect and authentication fails
    """


class MoodleParser:
    """
    This Class will contain any parsers needed by MoodleSession
    """
    windows_reserved_chars = {  # https://docs.microsoft.com/en-us/windows/win32/fileio/naming-a-file#naming-conventions
        '<': '',
        '>': '',
        ':': ';',
        '"': '\'',
        '/': ',',
        '\\': ',',
        '|': ',',
        '?': '.',
        '*': ''
    }

    @staticmethod
    def parse_windows(string):
        for char, newchar in MoodleParser.windows_reserved_chars.items():
            string = string.replace(char, newchar)
        return string
