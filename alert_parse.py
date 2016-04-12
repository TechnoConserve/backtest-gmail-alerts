from __future__ import print_function
import httplib2
import os
import re
import string

from apiclient import discovery, errors
import base64
import email
import oauth2client
from oauth2client import client
from oauth2client import tools

from HTMLParser import HTMLParser

try:
	import argparse
	flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
	flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/gmail-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Gmail API Python Quickstart'

class HistAlert(object):
	def __init__(self):
		self.credentials = get_credentials()
		self.http = self.credentials.authorize(httplib2.Http())
		self.service = discovery.build('gmail', 'v1', http=self.http)
		self.message_list = list_messages_matching_query(self.service, 'me', 'from:tim@timothysykes.com subject:TimAlert')

	def return_message_list(self):
		return self.message_list

	def return_target(self, index):
		parser = MyHTMLParser()
		date, message = get_message_body(self.service, 'me', self.message_list[index]['id'])
		parser.feed(str(message))
	
		parsed = parser.get_parsed()

		for idx, data in enumerate(parsed):
			if data == 'TIMalert:':
				alert = parsed[idx + 1]
				tickers = []
				signal = None
				pop = 0 # To help weight occurances of price levels
				print(date)
				year, month, day = email.utils.parsedate(date)[:3]
				# pad single digit dates with 0 so they have the format YYYYMMDD
				if len(str(month)) == 1:
					month = '0' + str(month)
				if len(str(day)) == 1:
					day = '0' + str(day)
				sdate = str(year) + str(month) + str(day)
				print(sdate)
				print(alert)

				price = re.findall("[-+\.]?\d+[\.]?\d*", alert)

				words = alert.split()
				for i, word in enumerate(words):
					upper = word.upper()
					if word.isupper() and len(word) > 1:
						tickers.append(word.translate(string.maketrans('',''), string.punctuation)) # Remove punctuation from tickers
						continue

					if word == 'at':
						# Numbers immediately after the word at are more likely to be
						# the price level you want to set the limit order to
						match = re.match("[+-\.]?\d+", words[i+1])
						# Match object created if the next word has numbers
						if match is not None and match.group() in price:
							# Moves that number to the front of the price list
							# since it is more likely to be the correct limit price
							price.insert(pop, price.pop(price.index(match.group())))
							pop += 1 # Update where the next occurance should be placed in list

					if (signal is None) and ("SHORT" in upper or "SOLD" in upper):
						signal = 'SELL'
					elif (signal is None) and ("BOUGHT" in upper or "COVER" in upper):
						signal = 'BUY'				

				print(tickers)
				print(signal)
				print(price)

		parser.reset_parsed()
		parser.close()
		return sdate, tickers[0], signal, price[0]

def get_credentials():
	"""
	Gets valid user credentials from storage.

	If nothing has been stored, or if the stored credentials are invalid,
	the OAuth2 flow is completed to obtain the new credentials.

	Returns:
	Credentials, the obtained credential.
	"""
	home_dir = os.path.expanduser('~')
	credential_dir = os.path.join(home_dir, '.credentials')
	if not os.path.exists(credential_dir):
		os.makedirs(credential_dir)
	credential_path = os.path.join(credential_dir,
		'gmail-python-quickstart.json')

	store = oauth2client.file.Storage(credential_path)
	credentials = store.get()
	if not credentials or credentials.invalid:
		flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
		flow.user_agent = APPLICATION_NAME
		if flags:
			credentials = tools.run_flow(flow, store, flags)
		else: # Needed only for compatibility with Python 2.6
			credentials = tools.run(flow, store)
		print('Storing credentials to ' + credential_path)
	return credentials

def get_message_body(service, user_id, msg_id):
	"""
	Get a Message and use it to create a MIME Message.

	Args:
	service - Authorized Gmail API service instance.
	user_id - User's email address. The special value 'me'
		can be used to indicated the authenticated user.
	msg_id - The ID of the Message required.

	Returns:
	The body of a MIME Message.
	"""
	try:
		message = service.users().messages().get(userId=user_id, id=msg_id,
			format='raw').execute()
		date = service.users().messages().get(userId=user_id, id=msg_id).execute()
		date = date['payload']['headers'][4]['value'].split()[-7:]
		#print("Message date: %s" % " ".join(date))

		msg_str = base64.urlsafe_b64decode(message['raw'].encode('ASCII'))

		mime_msg = email.message_from_string(msg_str)
		return " ".join(date), mime_msg.get_payload()[1]
	except errors.HttpError, error:
		print("An error occurred: %s" % error)

def list_messages_matching_query(service, user_id, query=''):
	"""
	List all Messages of the user's mailbox matching the query.

	Args:
	service - Authorizes Gmail API service instance.
	user_id - User's email address. The special value 'me'
		can be used to indicate the authenticated user.
	query - String used to filter messages returned.
		E.g. - 'from:user@some_domain.com' for Messages from a particular sender.

	Returns:
	List of Messages that match the criteria of the query. Note that the
		returned list contains Message IDs, you must use get with the
		appropriate ID to get the details of a Message.
	"""
	try:
		response = service.users().messages().list(userId=user_id,
			q=query).execute()
		messages = []
		if 'messages' in response:
			messages.extend(response['messages'])

		while 'nextPageToken' in response:
			page_token = response['nextPageToken']
			response = service.users().messages().list(userId=user_id, q=query,
				pageToken=page_token).execute()
			messages.extend(response['messages'])
		return messages
	except errors.HttpError, error:
		print('An error occurred: %s' % error)

class MyHTMLParser(HTMLParser):
	parsed = []

	def handle_data(self, data):
		if data.strip() != '':
			#print("Here is the data: ", data.strip())
			self.parsed.append(data)

	def get_parsed(self):
		return self.parsed

	def reset_parsed(self):
		self.parsed = []

def main():
	"""
	Parse Gmail account to get past trade alert tickers, prices, and dates.
	"""
	credentials = get_credentials()
	http = credentials.authorize(httplib2.Http())
	service = discovery.build('gmail', 'v1', http=http)
	message_list = list_messages_matching_query(service, 'me', 'from:tim@timothysykes.com subject:TimAlert')

	parser = MyHTMLParser()

	for item in message_list[:1]:
		date, message = get_message_body(service, 'me', item['id'])
		parser.feed(str(message))
	
	parsed = parser.get_parsed()

	for idx, data in enumerate(parsed):
		if data == 'TIMalert:':
			alert = parsed[idx + 1]
			tickers = []
			signal = None
			pop = 0 # To help weight occurances of price levels
			print(date)
			year, month, day = email.utils.parsedate(date)[:3]
			print(str(year) + str(month) + str(day))
			print(alert)

			price = re.findall("[-+\.]?\d+[\.]?\d*", alert)

			words = alert.split()
			for i, word in enumerate(words):
				upper = word.upper()
				if word.isupper() and len(word) > 1:
					tickers.append(word)
					continue

				if word == 'at':
					# Numbers immediately after the word at are more likely to be
					# the price level you want to set the limit order to
					match = re.match("[+-\.]?\d+", words[i+1])
					# Match object created if the next word has numbers
					if match is not None and match.group() in price:
						# Moves that number to the front of the price list
						# since it is more likely to be the correct limit price
						price.insert(pop, price.pop(price.index(match.group())))
						pop += 1 # Update where the next occurance should be placed in list

				if (signal is None) and ("SHORT" in upper or "SOLD" in upper):
					signal = 'SELL'
				elif (signal is None) and ("BOUGHT" in upper or "COVER" in upper):
					signal = 'BUY'				

			print(tickers)
			print(signal)
			print(price)

	parser.close()

if __name__ == '__main__':
	main()