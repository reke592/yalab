from classes.blacklist import Blacklist
import re

# blacklist: regex blocking
class RegexBlocking(Blacklist):
    def _after_init(self):
        self.compile()

    def compile(self):
        listed = []
        for key in self.db.keys():
            if self.db[key]:
                listed.append(key)
        print('compiling', len(listed))
        pattern = '(^|.*\.)({0})'.format('|'.join(listed))
        setattr(self, 'pattern', re.compile(pattern))

    def count(self):
        active = 0
        for key in self.db.keys():
            if self.db[key]:
                active = active + 1
        # (active, inactive)
        return (active, len(self.db.keys()) - active)

    def _test(self, client, domain):
        try:
            result = getattr(self, 'pattern').match(domain)
            return result
        except Exception as e:
            print('something went wrong while testing pattern:', e)
            print('Query has been blocked')
            return True

# x = RegexBlocking()
# d = [
#     ('facebook', True),
#     ('messenger', True)
# ]

# x.include(d)
# x.compile()
# print(x.check('127.0.0.1', 'www.facebook.com'))