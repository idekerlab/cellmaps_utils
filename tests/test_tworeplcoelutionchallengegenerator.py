#! /usr/bin/env python

import os
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock
import argparse
from cellmaps_utils.challenge import *


class TestTwoReplCoelutionChallengeGenerator(unittest.TestCase):

    def setUp(self):
        self._parser = argparse.ArgumentParser(description='foo',
                                               formatter_class=constants.ArgParseFormatter)
        subparsers = self._parser.add_subparsers(dest='command',
                                                 help='Command to run. '
                                                      'Type <command> -h for '
                                                      'more help')
        subparsers.required = True
        TwoReplCoelutionChallengeGenerator.add_subparser(subparsers)
        self._parser.add_argument('--version', action='version',
                                   version=('%(prog)s ' +
                                   cellmaps_utils.__version__))


    def tearDown(self):
        pass

    def test_write_id_mapping_file(self):
        temp_dir = tempfile.mkdtemp()
        try:
            theargs = self._parser.parse_args([TwoReplCoelutionChallengeGenerator.COMMAND,
                                               temp_dir,
                                               '--repl1_tsv', 'x',
                                               '--repl2_tsv', 'y'])

            gen = TwoReplCoelutionChallengeGenerator(theargs)
            dest_file = os.path.join(temp_dir, REPL_MAPPING)
            gen.write_id_mapping_file(id_mapping={'hi': 'there'})
            with open(dest_file, 'r') as f:
                data = json.load(f)
            self.assertTrue(data['hi'] == 'there')
        finally:
            shutil.rmtree(temp_dir)


if __name__ == '__main__':
    unittest.main()
