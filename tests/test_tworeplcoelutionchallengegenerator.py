#! /usr/bin/env python

import os
import tempfile
import unittest
import json
import shutil
import pandas as pd
import argparse
from cellmaps_utils.challenge import *
from cellmaps_utils.challenge import REPL_MAPPING
from cellmaps_utils.challenge import TwoReplCoelutionChallengeGenerator
import cellmaps_utils
from cellmaps_utils.constants import ArgParseFormatter


class TestTwoReplCoelutionChallengeGenerator(unittest.TestCase):

    def setUp(self):
        fmt = constants.ArgParseFormatter
        self._parser = argparse.ArgumentParser(description='foo',
                                               formatter_class=fmt)
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

    def test_full_run_on_example_repls(self):
        temp_dir = tempfile.mkdtemp()
        try:
            testdatadir = os.path.join(os.path.dirname(__file__), 'data')
            repl1_file = os.path.join(testdatadir, 'repl1_example.tsv')
            repl2_file = os.path.join(testdatadir, 'repl2_example.tsv')

            theargs = self._parser.parse_args([TwoReplCoelutionChallengeGenerator.COMMAND,
                                               temp_dir,
                                               '--repl1_tsv', repl1_file,
                                               '--repl2_tsv', repl2_file,
                                               '--seed', '1'])

            gen = TwoReplCoelutionChallengeGenerator(theargs)
            self.assertEqual(0, gen.run())
            result_dir = os.path.join(temp_dir,
                                      'tworeplcoelution_challenge_kolf'
                                      '2.1j_undifferentiated_untreated')
            self.assertTrue(os.path.isdir(result_dir))
            mapping_file = os.path.join(result_dir,
                                        'repl1_repl2_id_mapping.json')
            with open(mapping_file, 'r') as f:
                data = json.load(f)
            self.assertTrue(os.path.isfile(os.path.join(result_dir,
                                                        data['repl1.tsv'])))
            self.assertTrue(os.path.isfile(os.path.join(result_dir,
                                                        data['repl2.tsv'])))
            self.assertTrue('forward' in data)
            self.assertTrue('reverse' in data)
            self.assertTrue(data['forward']['P04637'] in data['reverse'])
            self.assertTrue(data['forward']
                            ['A6NCE7;Q9GZQ8'] in data['reverse'])
            self.assertEqual('P04637',
                             data['reverse'][data['forward']
                                                 ['P04637']])
            self.assertTrue('A6NCE7;Q9GZQ8' in
                            data['reverse'][data['forward']['A6NCE7;Q9GZQ8']])

            df = pd.read_table(os.path.join(result_dir,
                                            'repl1_repl2_combined.tsv'))
            self.assertEqual(2, len(df))
            self.assertTrue(list(df.columns), ['xxx', 'repl1_1',
                                               'repl1_2', 'repl1_3',
                                               'repl2_1',
                                               'repl2_2', 'repl2_3'])
            self.assertEqual(len(df['xxx']), 2)
            result_loc = df.loc[df['xxx'] == data['forward']['P04637']]
            self.assertTrue(str(df.head()),
                            pd.isna(result_loc['repl1_1'].tolist()[0]))
            self.assertAlmostEqual(result_loc['repl1_2'].tolist()[0], 0.1)
            self.assertAlmostEqual(result_loc['repl1_3'].tolist()[0], 0.2)
            self.assertTrue(str(df.head()),
                            pd.isna(result_loc['repl2_1'].tolist()[0]))
            self.assertAlmostEqual(result_loc['repl2_2'].tolist()[0], 0.1)
            self.assertTrue(str(df.head()),
                            pd.isna(result_loc['repl2_3'].tolist()[0]))

            result_loc = df.loc[df['xxx'] == data['forward']['A6NCE7;Q9GZQ8']]
            self.assertTrue(str(df.head()),
                            pd.isna(result_loc['repl1_1'].tolist()[0]))
            self.assertAlmostEqual(result_loc['repl1_2'].tolist()[0], 0.44)
            self.assertAlmostEqual(result_loc['repl1_3'].tolist()[0], 0.55)
            self.assertTrue(str(df.head()),
                            pd.isna(result_loc['repl2_1'].tolist()[0]))
            self.assertTrue(str(df.head()),
                            pd.isna(result_loc['repl2_2'].tolist()[0]))
            self.assertAlmostEqual(result_loc['repl2_3'].tolist()[0], 0.55)
        finally:
            shutil.rmtree(temp_dir)


if __name__ == '__main__':
    unittest.main()
