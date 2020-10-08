"""
This file contains all the Data Types used by Moodle
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

    @classmethod
    def from_dict(cls, course_dict):  # Not finished
        """
        Can take a dict formatted as a course and sets the variables
        """
        url = course_dict['url']
        name = course_dict['name']
        return cls(url, name)


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


class MoodleFolder:
    """
    This class holds neccesary information for a moodle course folder
    """
    def __init__(self, url: str, name: str, subfolders: list = None, files: list = None):
        self.url = url
        self.name = name
        self.subfolders = (list() if subfolders is None else subfolders)
        self.files = (list() if files is None else files)


class MoodleFile:
    """
    This class holds neccesary information for a moodle file
    """
    def __init__(self, url: str, name: str = None, path: str = None):
        self.url = url
        self.name = name
        self.path = path


class MoodleAssignment:
    """
    This class holds neccesary information for a moodle assignment
    """
    def __init__(self, url: str, name: str = None, description: str = None, due_date: datetime = None):
        self.url = url
        self.name = name
        self.description = description
        self.due_date = due_date


class MoodleUrl:
    """
    This class holds neccesary information for a moodle url
    """
    def __init__(self, url: str, name: str = None, path: str = None):
        self.url = url
        self.name = name
        self.path = path
