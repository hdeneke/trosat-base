import os, pathlib
from trosat import pathutil as pu

from unittest import TestCase

class TestPathFormatter(TestCase):

    def test_home(self):
        '''
        Test two different syntaxes for accessing environment variables
        '''
        p1 = pu.PathFormatter('$HOME')()
        p2 = pu.PathFormatter('{ENV[HOME]}')()
        self.assertEqual(p1, p2)

    def test_callable(self):
        '''
        Test that PathFormatter instances are callable
        '''
        p1 = pu.PathFormatter('{0}')('test')
        p2 = pu.PathFormatter('{0}').format('test')
        self.assertEqual(p1, p2)
        return
        
    def test_convert_field(self):
        '''
        Test custom conversion characters
        '''
        s = 'AbCdEfG'
        self.assertEqual(pu.PathFormatter('{0!l}')(s), pathlib.Path(s.lower()))
        self.assertEqual(pu.PathFormatter('{0!u}')(s), pathlib.Path(s.upper()))
        self.assertEqual(pu.PathFormatter('{0!t}')(s), pathlib.Path(s.title()))
        self.assertEqual(pu.PathFormatter('{0!c}')(s), pathlib.Path(s.capitalize()))
        return

class TestPathMatcher(TestCase):
    
    def test_match(self):
        return
        
