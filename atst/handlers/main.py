import atst
from atst.handler import BaseHandler, authenticated

class MainHandler(BaseHandler):

    def initialize(self, page):
        self.page = page

    @authenticated
    def get(self):
        self.render( '%s.html.to' % self.page, page = self.page )
