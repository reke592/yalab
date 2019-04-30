# blacklist base class
class Blacklist:
    db = {}

    def __init__(self, data=[]):
        self.include(data)
        self._after_init()
    
    def include(self, data=[], cb=None):
        row_ids = []
        for item in data:
            id, domain, blocking = item
            self.db[domain] = blocking
            row_ids.append(str(id))
        if cb:
            cb(row_ids)
    
    def check(self, client, domain):
        print('from', client)
        result = False
        try:
            result = self._test(client, domain)
        except KeyError:
            pass
        finally:
            if result:
                print('blocked request from "{0}" query: "{1}"'.format(client, domain))
            return result

    def _after_init(self):
        pass

    # overriden by child class
    def _test(self, client, domain):
        return self.db[domain]
