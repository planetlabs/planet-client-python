import unittest

from planet.auth import AuthException


class MyException1(Exception):

    def __init__(self, msg):
        self.messagr = msg


class MyException2(Exception):

    def __init__(self, msg):
        self.messagr = msg


class TestCredential(unittest.TestCase):

    def test_decorator_default(self):
        @AuthException.recast()
        def raise_my_exception1():
            raise MyException1(msg="test")
        with self.assertRaises(AuthException):
            raise_my_exception1()

    def test_decorator_explicit(self):
        @AuthException.recast(MyException1)
        def raise_my_exception1():
            raise MyException1(msg="test")
        with self.assertRaises(AuthException):
            raise_my_exception1()

    def test_passes_not_recast_exception(self):
        @AuthException.recast(MyException1)
        def raise_my_exception2():
            raise MyException2(msg="test")
        with self.assertRaises(MyException2):
            raise_my_exception2()
