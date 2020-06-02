#!/usr/bin/env python3

import collections
import datetime

from db import db
import plaid

def transaction_info():
	payees = collections.defaultdict(list)
	categories = collections.defaultdict(list)
	for t in iter_transactions():
		if t['amount'] < 0 or t['category'].startswith('Transfer,'):
			continue
		payees[t['name']].append(t)
		categories[t['category']].append(t)

	cat_by_periodicity = []
	for name, transactions in categories.items():
		periodicity = group_periodicity(transactions)
		transactions_list = [{'date': t['date'], 'name': t['name'], 'amount': t['amount']} for t in transactions]
		cat_by_periodicity.append((name, periodicity, transactions_list))
	cat_by_periodicity.sort(key=lambda cbp: cbp[1], reverse=True)
	return cat_by_periodicity

def group_periodicity(transactions):
	if len(transactions) < 3:
		return 0.0

	first = datetime.datetime.strptime(transactions[0]['date'], '%Y-%m-%d')

	last_date = datetime.datetime.strptime(transactions[1]['date'], '%Y-%m-%d')
	last_interval = last_date - first
	last_amount = transactions[1]['amount']
	total_periodicity = 0.0
	for t in transactions[2:]:
		date = datetime.datetime.strptime(t['date'], '%Y-%m-%d')
		interval = date - last_date
		total_periodicity += transactions_periodicity(interval, last_interval, t['amount'], last_amount)

		last_interval = interval
		last_date = date
		last_amount = t['amount']
	return total_periodicity / (len(transactions) - 2)

def transactions_periodicity(interval, last_interval, amount, last_amount):
	periodicity = 0.0
	if interval.days > 20:
		periodicity += 0.2
	if abs(interval - last_interval).days < 7:
		periodicity += 0.4
	if abs(amount - last_amount) / last_amount < 0.4:
		periodicity += 0.4
	return periodicity

def iter_transactions():
	with db:
		cur = db.execute('''
			SELECT date, name, amount, category
			FROM plaid_transaction ORDER BY date ASC
		''')
		while True:
			row = cur.fetchone()
			if row is None:
				break
			yield row