#! /usr/bin/env python

import os
import shutil
import tempfile
import time
import unittest
import pandas as pd
from unittest.mock import MagicMock
import argparse
from cellmaps_utils.challenge import *
import cellmaps_utils


class TestSolutionGenerator(unittest.TestCase):

    def setUp(self):
        self._parser = argparse.ArgumentParser(description='foo',
                                               formatter_class=constants.ArgParseFormatter)
        subparsers = self._parser.add_subparsers(dest='command',
                                                 help='Command to run. '
                                                      'Type <command> -h for '
                                                      'more help')
        subparsers.required = True
        SolutionGenerator.add_subparser(subparsers)
        self._parser.add_argument('--version', action='version',
                                   version=('%(prog)s ' +
                                   cellmaps_utils.__version__))


    def tearDown(self):
        pass

    def test_full_run_on_example_repls(self):
        temp_dir = tempfile.mkdtemp()
        try:
            testdatadir = os.path.join(os.path.dirname(__file__), 'data')

            input_dir = os.path.join(temp_dir, 'input')
            os.makedirs(input_dir, mode=0o755)
            shutil.copy(os.path.join(testdatadir, 'repl1_repl2_id_mapping.json'),
                        os.path.join(input_dir, 'repl1_repl2_id_mapping.json')),
            shutil.copy(os.path.join(testdatadir, 'repl1_repl2_combined.tsv'),
                        os.path.join(input_dir, 'repl1_repl2_combined.tsv'))
            shutil.copy(os.path.join(testdatadir, 'testsolrepl1.tsv'),
                        os.path.join(input_dir, 'testsolrepl1.tsv'))
            shutil.copy(os.path.join(testdatadir, 'testsolrepl2.tsv'),
                        os.path.join(input_dir, 'testsolrepl2.tsv'))

            solcx = os.path.join(testdatadir, 'testsolution_genes.cx2')

            theargs = self._parser.parse_args([SolutionGenerator.COMMAND,
                                               temp_dir,
                                               '--input', input_dir,
                                               '--standards', solcx + ',genes,test,4'])

            gen = SolutionGenerator(theargs)
            self.assertEqual(0, gen.run())
            # result_dir = os.path.join(temp_dir,
            #                          'tworeplcoelution_challenge_kolf'
            #                          '2.1j_undifferentiated_untreated')
            #self.assertTrue(os.path.isdir(result_dir))

        finally:
            shutil.rmtree(temp_dir)


if __name__ == '__main__':
    unittest.main()
