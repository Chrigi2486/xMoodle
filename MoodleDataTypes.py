"""
This file contains all the Data Types used by MoodleSession
"""

from datetime import datetime


class MoodleData:
    """
    This class will the the base class for Moodle Data Types
    """
    def to_dict(self) -> dict:
        """
        Creates a dict with all neccesary variables of the Data Type

        Returns:
            dict: A dict that can be used to replicate the Data Type instance
        """
        data_dict = dict()
        for key, value in self.__dict__.items():
            if isinstance(value, list):
                value = [item.to_dict() for item in value]
            data_dict[key] = value

        return data_dict

    @classmethod
    def from_dict(cls, data_dict: dict):
        """
        Can take a dict formatted as a Data Type and
        returns an instance of the replicated Data Type

        Parameters:
            dict: A dict formatted for a Data Type

        Returns:
            cls: Returns an instance of the Data Type
        """
        self = cls.__new__(cls)  # Creates a new instance of the class without activating __init__

        for key, value in data_dict.items():
            if isinstance(value, list):  # checks if the value is a dict, indicating that it's a class
                value = [globals()[item['type']].from_dict(item) for item in value]  # dunno if using globals() is good practice https://www.xspdf.com/resolution/51693418.html#:~:text=Python%20get%20class%20from%20module,somemodule.
            self.__setattr__(key, value)
        return self
# make sure every subclass has an attr called type with the same name as the class


class MoodleCourse(MoodleData):
    """
    This class holds neccesary information for a moodle course
    """
    def __init__(self, url: str, name: str, sections: list = None):
        self.url = url
        self.name = name
        self.sections = sections or list()
        self.type = 'MoodleCourse'


class MoodleSection(MoodleData):
    """
    This class holds neccesary information for a moodle course section
    """
    def __init__(self, url: str, name: str, folders: list = None, files: list = None, assignments: list = None):
        self.url = url
        self.name = name
        self.folders = folders or list()
        self.files = files or list()
        self.assignments = assignments or list()
        self.type = 'MoodleSection'


class MoodleFolder(MoodleData):  # needs to be tested
    """
    This class holds neccesary information for a moodle course folder
    """
    def __init__(self, url: str, name: str, path: str = None, folders: list = None, files: list = None):
        self.url = url
        self.name = name
        self.path = path
        self.folders = folders or list()
        self.files = files or list()
        self.type = 'MoodleFolder'


class MoodleFile(MoodleData):
    """
    This class holds neccesary information for a moodle file
    """
    def __init__(self, url: str, name: str = None, path: str = None):
        self.url = url
        self.name = name
        self.path = path
        self.type = 'MoodleFile'


class MoodleAssignment(MoodleData):  # needs to be tested
    """
    This class holds neccesary information for a moodle assignment
    """
    def __init__(self, url: str, name: str = None, status: str = None, due_date: str = None):
        self.url = url
        self.name = name
        self.status = status
        self.due_date = due_date
        self.type = 'MoodleAssignment'


class MoodleUrl(MoodleData):
    """
    This class holds neccesary information for a moodle url
    """
    def __init__(self, url: str, name: str, path: str = None):
        self.url = url
        self.name = name
        self.path = path
        self.type = 'MoodleUrl'
