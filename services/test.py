import logging
import sys
import traceback

class test:
    def b(self):
        print(getattr(self, 'a'))

class A(test):
    def __init__(self):
        self.c = 1

    def a(self):
        return 1

x = A()
x.b()
