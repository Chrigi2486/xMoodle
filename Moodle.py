from requests import Session 			#reference: https://requests.readthedocs.io/en/master/
from requests import Timeout 			#imports the Timeout error class
from bs4 import BeautifulSoup as BS 	#reference: https://www.crummy.com/software/BeautifulSoup/bs4/doc/
from urllib.parse import unquote 		#reference: https://stackoverflow.com/questions/11768070/transform-url-string-into-normal-string-in-python-20-to-space-etc
import os


# All html reference from https://moodle.ksz.ch by viewing page source

class MoodleSession(Session):
	'''
	This inherits from requests.Session() and will be the Session used to get information from Moodle
	'''
	DEFAULT_TIMEOUT = 5

	def __init__(self, session_urls, *args, **kwargs):
		'''
		Setting variables
		session_urls is a dict that consists of home_url and login_url
		'''
		self.home_url = session_urls['home']
		self.login_url = session_urls['login']

		Session.__init__(self, *args, **kwargs)


	def get_page(self, url, times=0, timeout=DEFAULT_TIMEOUT):
		'''
		This function will act as self.get() but will include a default timeout and handler
		'''
		
		try:
			with self.get(url, timeout=timeout) as page:
				return(page)

		except Timeout: 	#If a Timeout occurs, it will retry 3 times before raising an error
			print('timeout', times, timeout)
			if times == 3:
				raise ConnectionError()

			self.get_page(url, times=(times+1))



	def login(self, logindata):
		'''
		Logs into the provided account
		logindata is a dict that consists of username and password
		'''
		def get_logintoken():
			'''
			Retrieve a valid logintoken to use as authentication
			'''
			with self.get_page(self.login_url) as login_page:
				return(BS(login_page.text, 'html.parser').find(attrs={'name': 'logintoken'})['value'])

		def post_logindata():
			'''
			Sends the logindata to Moodle to authenticate the Session
			and checks if the Session has been authenticated
			'''
			with self.post(self.login_url, data=logindata) as home_page:
				if home_page.url == self.login_url: # Checks if the authentication was successful
					return False
				return True


		logindata['logintoken'] = get_logintoken()
		if not post_logindata():
			raise IncorrectLogindata()


	def get_courses(self):
		'''
		Gets all the courses available for the student
		'''
		with self.get_page(self.home_url) as homepage:
			course_list = BS(homepage.text, 'html.parser').find_all('a')
			courses = []
			for course in course_list: #Creates a new Course object for each course found
				if 'course' not in course['href']:
					continue
				new_course = MoodleCourse(course['href'], course.find(class_='media-body').string)
				courses.append(new_course)
		return(courses) #returns a list of courses

	def get_course_content(self, course):
		'''
		Retrieves all the content of the given course
		'''
		with self.get_page(course.url) as coursepage:
			page_items = BS(coursepage.text, 'html.parser').find_all('a')
			for item in page_items: #This goes through all URLs in the course and finds any relevent URL
				
				if 'section' in item['href']: 	#Creates a new Section object for each Section
					if item.string == None:
						continue
					section = MoodleSection(item['href'], item.string)
					course.sections.append(section)

				elif 'resource' in item['href']:#Creates a new File object for each File
					file = MoodleFile(item['href'], item.find(class_='instancename').contents[0], course.sections[-1].name)
					course.sections[-1].files.append(file)

				elif 'folder' in item['href']: 	#Creates a new Folder object for each Folder
					folder = MoodleFolder(item['href'], item.find(class_='instancename').contents[0])
					course.folders.append(folder)



	def download_file(self, file, base_path):
		'''
		Downloads a given file to the base path given
		'''
		with self.get_page(file.url) as file_page:
			path = f'{base_path}/{file.path}/{unquote(str(file_page.url).split("/0/")[1])}'
			os.makedirs(os.path.dirname(path), exist_ok=True) 	#https://stackoverflow.com/questions/12517451/automatically-creating-directories-with-file-output
			with open(path, 'wb') as file:
				file.write(file_page.content)
		return(path)





class MoodleCourse:
	'''
	This will be the course class holding neccesary information for the moodle courses
	'''
	def __init__(self, url: str, name: str, sections: list = None, folders: list = None, files: list = None):
		'''
		Sets default variables if none are given
		'''
		self.url = url
		self.name = name
		self.sections = (list() if sections is None else sections) 	#This fixes the problem with all objects having a list with the same memory pointer resulting in having the exact same list
		self.folders = (list() if folders is None else folders)
		self.files = (list() if files is None else files)

	def from_dict(self, course):
		'''
		Can take a dict formatted as a course and sets the variables
		'''
		self.url = course['url']
		self.name = course['name']
		self.sections = list()
		self.folders = list()
		self.files = list()


class MoodleSection:
	'''
	This is a class holding neccesary information for the moodle course sections
	'''
	def __init__(self, url: str, name: str, subsections: list = None, folders: list = None, files: list = None):
		'''
		Sets default variables if none are given
		'''
		self.url = url
		self.name = name
		self.subsections = (list() if subsections is None else subsections)
		self.folders = (list() if folders is None else folders)
		self.files = (list() if files is None else files)

	def get_files(self): # Needs test
		'''
		Retrieves all files in the section and in all sections within it
		'''
		subsection_files = []
		for subsection in self.subsections:
			child_files = subsection.get_files()
			for child_file in child_files:
				child_file.path = f'{self.name}/{child_file.path}'
				subsection_files.append(child_file)


		return(self.files + subsection_files) # Returs a list of all the sections files including files of subsections


class MoodleFolder:
	def __init__(self, url: str, name: str, subfolders: list = None, files: list = None):
		'''
		Sets default variables if none are given
		'''
		self.url = url
		self.name = name
		self.subfolders = (list() if subfolders is None else subfolders)
		self.files = (list() if files is None else files)


class MoodleFile:
	def __init__(self, url: str, name: str = None, path: str = None):
		'''
		Sets default variables if none are given
		'''
		self.url = url
		self.name = name
		self.path = path



class IncorrectLogindata(Exception): 	#Handling and raising exceptions reference: https://docs.python.org/3/tutorial/errors.html
	'''
	Exception raised when the logindata is incorrect and authentication fails
	'''
	pass