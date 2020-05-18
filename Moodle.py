from requests import Session 			#reference: https://requests.readthedocs.io/en/master/
from requests import ConnectionError
from bs4 import BeautifulSoup as BS 	#reference: https://www.crummy.com/software/BeautifulSoup/bs4/doc/


# All html reference https://moodle.ksz.ch by viewing page source

class MoodleSession(Session):
	'''
	This inherits from requests.Session() and will be the Session used to get information from Moodle
	'''

	def __init__(self, session_urls, *args, **kwargs):
		'''
		Setting variables
		session_urls is a dict that consists of home_url and login_url
		'''
		self.home_url = session_urls['home']
		self.login_url = session_urls['login']

		Session.__init__(self, *args, **kwargs)

	def login(self, logindata):
		'''
		Logs into the provided account
		logindata is a dict that consists of username and password
		'''
		def get_logintoken():
			'''
			Retrieve a valid logintoken to use as authentication
			'''
			with self.get(self.login_url) as login_page:
				return(BS(login_page.text, 'html.parser').find(attrs={'name': 'logintoken'})['value'])

		def post_logindata():
			'''
			Sends the logindata to Moodle to authenticate the Session
			'''
			self.post(self.login_url, data=logindata)

		def check_login():
			'''
			Checks if the Session has been authenticated
			'''
			with self.get(self.home_url) as home_page:
				if home_page.url == self.login_url: # Checks if the authentication was successful
					return False
				return True

		logindata['logintoken'] = get_logintoken()
		post_logindata()
		if not check_login():
			raise IncorrectLogindata()


	def get_courses(self):
		'''
		Gets all the courses available for the student
		'''
		with self.get(self.home_url) as homepage:
			course_list = BS(homepage.text, 'html.parser').find_all('a')
			courses = []
			for course in course_list: #Creates a new Course object for each course found
				if 'course' not in course['href']:
					continue
				new_course = MoodleCourse()
				new_course.url = course['href']
				new_course.name = course.find(class_='media-body').string
				courses.append(new_course)
			return(courses) #returns a list of courses

	def get_course_content(self, course):
		'''
		Retrieves all the content of the given course
		'''
		with self.get(course.url) as coursepage:
			page_items = BS(coursepage.text, 'html.parser').find_all('a')
			for item in page_items: #Creates a new Section object for all each Section
				if 'section' in item['href']:
					if item.string == None:
						continue
					section = MoodleSection(item.string, item['href'])
					course.sections.append(section)

				# Add subsections

				# Add folders to course

				# Add files to course in sections






class MoodleCourse:
	'''
	This will be the course class holding neccesary information for the moodle courses
	'''
	def __init__(self, url='', name='', sections=[], files=[]):
		'''
		Sets default variables if none are given
		'''
		self.url = url
		self.name = name
		self.sections = sections
		self.files = files

	def from_dict(self, course):
		'''
		Can take a dict formatted as a course and sets the variables
		'''
		self.url = course['url']
		self.name = course['name']
		self.sections = course['sections']
		self.files = course['files']


class MoodleSection:
	'''
	This is a class holding neccesary information for the moodle course sections
	'''
	def __init__(self, name='', url='', subsections=[], files=[]):
		'''
		Sets default variables if none are given
		'''
		self.name = name
		self.url = url
		self.subsections = subsections
		self.files = files

	def get_files(self): # Needs test
		'''
		Retrieves all files in the section and in all sections within it
		'''
		subsection_files
		for subsection in self.subsections:
			child_files = subsection.get_files()
			for child_file in child_files:
				child_file.path = f'{self.name}/{child_file.path}'
				files.append(child_file)

		return(self.files + subsection_files) # Returs a list of all the sections files including files of subsections



class MoodleFile:
	def __init__(self, name='', url='', path=''):
		'''
		Sets default variables if none are given
		'''
		self.name = name
		self.url = url
		self.path = path


class MoodleFolder:
	def __init__(self, name='', url='', subsfolders=[], files=[]):
		'''
		Sets default variables if none are given
		'''
		self.name = name
		self.url = url
		self.subfolders = subfolders
		self.files = files


class IncorrectLogindata(Exception): 	#Handling and raising exceptions reference: https://docs.python.org/3/tutorial/errors.html
	'''
	Exception raised when the logindata is incorrect and authentication fails
	'''
	pass