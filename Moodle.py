from requests import Session 			#reference: https://requests.readthedocs.io/en/master/
from requests import ConnectionError
from bs4 import BeautifulSoup as BS 	#reference: https://www.crummy.com/software/BeautifulSoup/bs4/doc/


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
				if home_page.url == self.login_url:
					return False
				return True

		logindata['logintoken'] = get_logintoken()
		post_logindata()
		if not check_login():
			raise IncorrectLogindata()



class IncorrectLogindata(Exception): 	#Handling and raising exceptions reference: https://docs.python.org/3/tutorial/errors.html
	'''
	Exception raised when the logindata is incorrect and authentication fails
	'''
	pass