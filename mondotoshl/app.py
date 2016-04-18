import os
from datetime import datetime
from flask import Flask
from flask import request
from toshl.client import ToshlClient, Account, Category, Entry
from logentries import LogentriesHandler
import logging


app = Flask(__name__)

MONDO_TOSHL_TOKEN = os.environ.get('MONDO_TOSHL_TOKEN')
TOSHL_API_TOKEN = os.environ.get('TOSHL_API_TOKEN')
TOSHL_MONDO_ACCOUNT_NAME = os.environ.get('TOSHL_MONDO_ACCOUNT_NAME', 'Mondo')
TOSHL_MONDO_CATEGORY_NAME = os.environ.get(
    'TOSHL_MONDO_CATEGORY_NAME', 'mondo-toshl')
TOSHL_MONDO_REFUND_CATEGORY_NAME = os.environ.get(
    'TOSHL_MONDO_REFUND_CATEGORY_NAME', 'mondo-toshl-refund')
LOGENTRIES_TOKEN = os.environ.get('LOGENTRIES_TOKEN')

log = logging.getLogger('logentries')
log.setLevel(logging.INFO)
mondotoshl_logger = LogentriesHandler(LOGENTRIES_TOKEN)
log.addHandler(mondotoshl_logger)


@app.route('/transactions', methods=['POST'])
def mondo_hook():
    if request.method == 'POST':
        token = request.args.get('token')
        if token == MONDO_TOSHL_TOKEN:
            data = request.get_json()
            log.info(data)
            # Only handle transaction.created events
            if data['type'] == 'transaction.created':
                is_load = data['data']['is_load']
                amount = data['data']['amount']
                # Only log expenses for the moment
                if not is_load:
                    client = ToshlClient(TOSHL_API_TOKEN)

                    account_client = Account(client)
                    account = account_client.search(TOSHL_MONDO_ACCOUNT_NAME)

                    category_client = Category(client)

                    if amount < 0:
                        category = category_client.search(
                            TOSHL_MONDO_CATEGORY_NAME)
                    else:
                        category = category_client.search(
                            TOSHL_MONDO_REFUND_CATEGORY_NAME)

                    now = datetime.now()

                    json_payload = {
                        'amount': amount * 0.01,
                        'currency': {
                            'code': 'GBP'
                        },
                        'date': '{0}-{1}-{2}'.format(
                            now.year, now.month, now.day),
                        'account': account,
                        'category': category,
                        'desc': data['data']['description']
                    }

                    entry_client = Entry(client)
                    entry_client.create(json_payload)

                    return '', 200
    return '', 200


if __name__ == '__main__':
    app.run(host='localhost', port=5000, debug=True)
