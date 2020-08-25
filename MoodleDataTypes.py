"""
This file contains all the Data Types used by Moodle
"""

from datetime import datetime


class MoodleCourse:
    """
    This will be the course class holding neccesary information for the moodle courses
    """
    def __init__(self, url: str, name: str, sections: list = None, folders: list = None):
        """
        Sets default variables if none are given
        """
        self.url = url
        self.name = name
        self.sections = (list() if sections is None else sections)  # This fixes the problem with all objects having a list with the same memory pointer resulting in having the exact same list
        self.folders = (list() if folders is None else folders)

    @classmethod
    def from_dict(cls, course):
        """
        Can take a dict formatted as a course and sets the variables
        """
        url = course['url']
        name = course['name']
        return cls(url, name)


class MoodleSection:
    """
    This is a class holding neccesary information for the moodle course sections
    """
    def __init__(self, url: str, name: str, folders: list = None, files: list = None):
        """
        Sets default variables if none are given
        """
        self.url = url
        self.name = name
        self.folders = (list() if folders is None else folders)
        self.files = (list() if files is None else files)


class MoodleFolder:
    def __init__(self, url: str, name: str, subfolders: list = None, files: list = None):
        """
        Sets default variables if none are given
        """
        self.url = url
        self.name = name
        self.subfolders = (list() if subfolders is None else subfolders)
        self.files = (list() if files is None else files)


class MoodleFile:
    def __init__(self, url: str, name: str = None, path: str = None):
        """
        Sets default variables if none are given
        """
        self.url = url
        self.name = name
        self.path = path


class MoodleAssignment:
    def __init__(self, url: str, name: str = None, description: str = None, due_date: datetime = None):
        self.url = url
        self.name = name
        self.description = description
        self.due_date = due_date


class MoodleUrl:
    def __init__(self, url: str, name: str = None, path: str = None):
        self.url = url
        self.name = name
        self.path = path
