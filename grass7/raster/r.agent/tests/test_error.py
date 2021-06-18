import unittest2 as unittest

# import unittest

from libagent import error


class TestOurExceptions(unittest.TestCase):
    #    def setUp(self):

    def raise_base(context, message):
        raise error.Error(context, message)

    def raise_env(context, message):
        raise error.EnvError(context, message)

    def raise_data(context, message):
        raise error.DataError(context, message)

    def test_error(self):
        self.assertRaises(error.Error, self.raise_base, ("tests", "base"))

    def test_enverror(self):
        self.assertRaises(error.Error, self.raise_base, ("tests", "env"))
        self.assertRaises(error.EnvError, self.raise_env, ("tests", "env"))

    def test_dataerror(self):
        self.assertRaises(error.Error, self.raise_base, ("tests", "data"))
        self.assertRaises(error.DataError, self.raise_data, ("tests", "data"))


#    def tearDown(self):
