import unittest
import os

from .config_finder import cfg

class TestConfigValueFinder(unittest.TestCase):

    def setUp(self):
        # set up bottom layer config (file at /env)
        with open("/env", 'w+') as envfile:
            envfile.write("first=envfile\n")
            envfile.write("second=envfile\n")
            envfile.write("third=envfile\n")

        # set up middle layer (file at /secret/<key>)
        with open("/secret/first", 'w+') as secfile:
            secfile.write("secretfile")
        with open("/secret/second", 'w+') as envfile:
            envfile.write("secretfile")

        # set up top layer (os.environ)
        os.environ['first'] = 'environ'

    def tearDown(self):
        try: del os.environ['environ']
        except: pass
        try: os.remove("/env")
        except: pass
        try: os.remove("/secret/secretfile")
        except: pass
        try: os.remove("/secret/envfile")
        except: pass

    def test_cfg_search_path(self):
        """ cfg should look in the correct places first """
        self.assertEqual(cfg('first'), "environ")
        self.assertEqual(cfg('second'), "secretfile")
        self.assertEqual(cfg('third'), "envfile")

        # removing top layers should result in returning the next layer down
        del os.environ['first']
        os.remove('/secret/second')
        self.assertEqual(cfg('first'), "secretfile")
        self.assertEqual(cfg('second'), "envfile")

    def test_cfg_default(self):
        """ if there is noting set, return the default or error """
        # default case
        self.assertEqual(cfg('notthekey', "default"), "default")

        # should accept odd values as default
        self.assertEqual(cfg('notthekey', None), None)
        self.assertEqual(cfg('notthekey', False), False)
        obj = object()
        self.assertEqual(cfg('notthekey', obj), obj)
        self.assertEqual(cfg('notthekey', int), int)
        self.assertEqual(cfg('notthekey', ...), Ellipsis)
        self.assertEqual(cfg('notthekey', type(int)), type)

        # error case
        with self.assertRaises(KeyError):
            cfg("theesearenotthekeysyouarelookingfor")
