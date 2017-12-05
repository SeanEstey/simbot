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
        id_a = ObjectId("5a25db9e43d0c4562e496aa5") # 11:34, 50 asks
        id_b = ObjectId("5a25dbe943d0c4562e496ae5") # 11:36, 49 asks
        book_diff_df(
            'QuadrigaCX',
            ('btc','cad'),
            'asks',
            g.db['pub_books'].find_one({"_id":id_a}),
            g.db['pub_books'].find_one({"_id":id_b}))

if __name__ == '__main__':
    unittest.main()
