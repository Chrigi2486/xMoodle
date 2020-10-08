"""
This file contains all the Data Types used by MoodleSession
"""

from datetime import datetime


class MoodleCourse:
    """
    This class holds neccesary information for a moodle course
    """
    def __init__(self, url: str, name: str, sections: list = None):
        self.url = url
        self.name = name
        self.sections = (list() if sections is None else sections)  # This fixes the problem with all objects having a list with the same memory pointer resulting in having the exact same list

    def to_dict(self) -> dict:
        """
        Creates a dict with all neccesary variables of the course

        Returns:
            dict: A dict that can be used to create a MoodleCourse instance
        """
        sections = [section.to_dict() for section in self.sections]
        return {'url': self.url, 'name': self.name, 'sections': sections}

    @classmethod
    def from_dict(cls, course_dict: dict):
        """
        Can take a dict formatted as a course and returns an instance of MoodleCourse

        Parameters:
            dict: A dict formatted for MoodleCourse

        Returns:
            MoodleCourse: Returns a MoodleCourse instance
        """
        url = course_dict['url']
        name = course_dict['name']
        sections = [MoodleSection.from_dict(section) for section in course_dict['sections']]

        return cls(url, name, sections=sections)


class MoodleSection:
    """
    This class holds neccesary information for a moodle course section
    """
    def __init__(self, url: str, name: str, folders: list = None, files: list = None, assignments: list = None):
        self.url = url
        self.name = name
        self.folders = (list() if folders is None else folders)
        self.files = (list() if files is None else files)
        self.assignments = (list() if assignments is None else assignments)

    def to_dict(self) -> dict:
        """
        Creates a dict with all neccesary variables of the section

        Returns:
            dict: A dict that can be used to create a MoodleSection instance
        """
        folders = [folder.to_dict() for folder in self.folders]
        files = [file.to_dict() for file in self.files]
        assignments = [assignment.to_dict() for assignment in self.assignments]

        return {'url': self.url, 'name': self.name, 'folders': folders, 'files': files, 'assignments': assignments}

    @classmethod
    def from_dict(cls, section_dict: dict):
        """
        Can take a dict formatted as a section and returns an instance of MoodleSection

        Parameters:
            dict: A dict formatted for MoodleSection

        Returns:
            MoodleSection: Returns a MoodleSection instance
        """
        url = section_dict['url']
        name = section_dict['name']
        folders = [MoodleFolder.from_dict(folder) for folder in section_dict['folders']]
        files = [MoodleFile.from_dict(file) for file in section_dict['files']]
        assignments = [MoodleAssignment.from_dict(assignment) for assignment in section_dict['assignments']]

        return cls(url, name, folders=folders, files=files, assignments=assignments)


class MoodleFolder:
    """
    This class holds neccesary information for a moodle course folder
    """
    def __init__(self, url: str, name: str, subfolders: list = None, files: list = None):
        self.url = url
        self.name = name
        self.subfolders = (list() if subfolders is None else subfolders)
        self.files = (list() if files is None else files)

    def to_dict(self) -> dict:
        """
        Creates a dict with all neccesary variables of the folder

        Returns:
            dict: A dict that can be used to create a MoodleFolder instance
        """
        subfolders = [subfolder.to_dict() for subfolder in self.subfolders]
        files = [file.to_dict() for file in self.files]

        return {'url': self.url, 'name': self.name, 'subfolders': subfolders, 'files': files}

    @classmethod
    def from_dict(cls, folder_dict: dict):
        """
        Can take a dict formatted as a folder and returns an instance of MoodleFolder

        Parameters:
            dict: A dict formatted for MoodleFolder

        Returns:
            MoodleFolder: Returns a MoodleFolder instance
        """
        url = folder_dict['url']
        name = folder_dict['name']
        subfolders = [MoodleFolder.from_dict(subfolder) for subfolder in folder_dict['subfolders']]
        files = [MoodleFile.from_dict(file) for file in folder_dict['files']]

        return cls(url, name, subfolders=subfolders, files=files)


class MoodleFile:
    """
    This class holds neccesary information for a moodle file
    """
    def __init__(self, url: str, name: str = None, path: str = None):
        self.url = url
        self.name = name
        self.path = path

    def to_dict(self) -> dict:
        """
        Creates a dict with all neccesary variables of the file

        Returns:
            dict: A dict that can be used to create a MoodleFile instance
        """

        return {'url': self.url, 'name': self.name, 'path': self.path}

    @classmethod
    def from_dict(cls, file_dict: dict):
        """
        Can take a dict formatted as a file and returns an instance of MoodleFile

        Parameters:
            dict: A dict formatted for MoodleFile

        Returns:
            MoodleFile: Returns a MoodleFile instance
        """
        url = file_dict['url']
        name = file_dict['name']
        path = file_dict['path']

        return cls(url, name, path=path)


class MoodleAssignment:
    """
    This class holds neccesary information for a moodle assignment
    """
    def __init__(self, url: str, name: str = None, description: str = None, due_date: datetime = None):
        self.url = url
        self.name = name
        self.description = description
        self.due_date = due_date

    def to_dict(self) -> dict:
        """
        Creates a dict with all neccesary variables of the assignment

        Returns:
            dict: A dict that can be used to create a MoodleAssignment instance
        """

        return {'url': self.url, 'name': self.name, 'description': self.description, 'due_date': self.due_date}

    @classmethod
    def from_dict(cls, assignment_dict: dict):
        """
        Can take a dict formatted as an assignment and returns an instance of MoodleAssignment

        Parameters:
            dict: A dict formatted for MoodleAssignment

        Returns:
            MoodleAssignment: Returns a MoodleAssignment instance
        """
        url = assignment_dict['url']
        name = assignment_dict['name']
        description = assignment_dict['description']
        due_date = assignment_dict['due_date']

        return cls(url, name, description=description, due_date=due_date)


class MoodleUrl:
    """
    This class holds neccesary information for a moodle url
    """
    def __init__(self, url: str, name: str = None, path: str = None):
        self.url = url
        self.name = name
        self.path = path

    def to_dict(self) -> dict:
        """
        Creates a dict with all neccesary variables of the url

        Returns:
            dict: A dict that can be used to create a MoodleUrl instance
        """

        return {'url': self.url, 'name': self.name, 'path': self.path}

    @classmethod
    def from_dict(cls, url_dict: dict):
        """
        Can take a dict formatted as a url and returns an instance of MoodleUrl

        Parameters:
            dict: A dict formatted for MoodleUrl

        Returns:
            MoodleUrl: Returns a MoodleUrl instance
        """
        url = url_dict['url']
        name = url_dict['name']
        path = url_dict['path']

        return cls(url, name=name, path=path)
