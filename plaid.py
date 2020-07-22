import datetime

import requests

import config

rs = requests.Session()

def exchange_token(public_token):
	data = _post('/item/public_token/exchange', json={
		'public_token': public_token,
	})
	return data['item_id'], data['access_token']

def auth(access_token):
	return _post('/auth/get', json={'access_token': access_token})

class TransactionIter:
	def __init__(self, access_token):
		self.access_token = access_token
		self.total_offset = 0
		self.data_offset = 0
		self.data = self.post()
		self.accounts = self.data['accounts']
	
	def post(self):
		return _post('/transactions/get', json={
			'access_token': self.access_token,
			'start_date': '2000-01-01',
			'end_date': str(datetime.date.today()),
			'options': {
				'offset': self.total_offset,
				'count': 500,
			},
		})

	def __iter__(self):
		return self

	def __next__(self):
		if self.data_offset >= len(self.data['transactions']):
			self.total_offset += len(self.data['transactions'])
			if self.total_offset >= self.data['total_transactions']:
				raise StopIteration
			self.data = self.post()
			self.data_offset = 0

		transaction = self.data['transactions'][self.data_offset]
		self.data_offset += 1
		return transaction

def get_accounts(access_token):
	data = _post('/accounts/get', json={'access_token': access_token})
	return data['accounts']

def get_categories():
	# why does this require a JSON object?
	# https://github.com/plaid/plaid-python/blob/master/plaid/api/categories.py
	response = requests.post('https://%s.plaid.com/categories/get' % config.plaid.environment, json={})
	response.raise_for_status()
	return response.json()['categories']

def _post(endpoint, json):
	json.update({
		'client_id': config.plaid.client_id,
		'secret': config.plaid.development,
	})
	response = rs.post('https://%s.plaid.com%s' % (config.plaid.environment, endpoint), json=json)
	response.raise_for_status()
	return response.json()
