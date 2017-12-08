import logging, unittest, json
from datetime import datetime, timedelta
from bson import ObjectId
from flask import g
from app import create_app
from app.lib.mongo import create_client
from app.main.pub_data import book_diff_df
log = logging.getLogger(__name__)
db_client = create_client(connect=True, auth=False)

#-------------------------------------------------------------------------------
def init(self):
    self.app = create_app('app')
    self.user_id = 'sestey@vecova.ca'
    self._ctx = self.app.test_request_context()
    self._ctx.push()
    g.db = self.db = self.app.db_client['simbot']

class PubDataTests(unittest.TestCase):
    def setUp(self):
        init(self)

    def tearDown(self):
        pass

    def test_book_diff(self):
        import pandas as pd
        pd.set_option('display.width',1000)

        last = list(g.db['pub_books'].find(
            {'ex':'QuadrigaCX', 'pair':['btc','cad']
        }).sort('date',-1).limit(75))

        book_diff_df(
            'QuadrigaCX',
            ('btc','cad'),
            last[35],
            last[5]
        )


if __name__ == '__main__':
    unittest.main()
