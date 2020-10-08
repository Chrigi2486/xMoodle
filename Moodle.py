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

    async def get_course_content(self, course: MoodleCourse) -> None:
        """
        Retrieves all the content of the given course

        Parameters:
            course (MoodleCourse): The course from which to get all content
        """
        async with self.get(course.url) as coursepage:
            page_items = BS(await coursepage.text(), 'html.parser').find_all('a')
            for item in page_items:  # This goes through all URLs in the course and finds any relevent URL

                # Perhaps split the url and check if one of the splits is section, resource, url, ...

                if 'section' in item['href']:   # Creates a new Section object for each Section
                    if item.string is None:
                        continue
                    section = MoodleSection(item['href'],
                                            item.string.replace(':', ';'))

                    course.sections.append(section)

                elif 'resource' in item['href']:  # Creates a new File object for each File
                    file = MoodleFile(item['href'],
                                      item.find(class_='instancename').contents[0],
                                      course.sections[-1].name)

                    course.sections[-1].files.append(file)

                elif 'folder' in item['href']:  # Creates a new Folder object for each Folder
                    folder = MoodleFolder(item['href'],
                                          item.find(class_='instancename').contents[0])

                    course.sections[-1].folders.append(folder)

                elif 'assignment' in item['href']:
                    assignment = MoodleAssignment(item['href'],
                                                  item.find(class_='instancename'))

                    course.sections[-1].assignments.append(assignment)

    async def download_file(self, file: MoodleFile, base_path) -> str:
        """
        Downloads a given file to the base path given

        Parameters:
            file (MoodleFile): The file to be downloaded
            base_path (str): The path to which the file is to be downloaded

        Returns:
            str: The final path of the file
        """
        async with self.get(file.url) as file_page:  # https://www.youtube.com/watch?v=E_oIU4IU2W8
            path = f'{base_path}/{file.path}/{unquote(str(file_page.url).split("/")[-1])}'
            os.makedirs(os.path.dirname(path), exist_ok=True)  # https://stackoverflow.com/questions/12517451/automatically-creating-directories-with-file-output
            content = await file_page.read()
            with open(path, 'wb') as new_file:
                new_file.write(content)
        return path

    async def send_file(self, file_path, assignment: MoodleAssignment):
        """
        Used to upload a file to a target assignment

        Parameters:
            file (str): path of the file to send
            assignment (MoodleAssignment): The target assignment
        """
        if not os.path.exists(file_path):  # Maybe don't check but let it raise the exception
            return
        await self.post(assignment.url, data={'file': open(file_path, 'rb')})  # Not tested


class IncorrectLogindata(Exception):  # Handling and raising exceptions reference: https://docs.python.org/3/tutorial/errors.html
    """
    Exception raised when the logindata is incorrect and authentication fails
    """
