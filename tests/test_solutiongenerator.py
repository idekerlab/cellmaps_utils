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
            solcsv = os.path.join(testdatadir, 'testsolution.csv')

            theargs = self._parser.parse_args([SolutionGenerator.COMMAND,
                                               temp_dir,
                                               '--input', input_dir,
                                               '--standards',
                                               solcx + ',genes,test,4,true',
                                               solcsv + ',csv,3,f'])

            gen = SolutionGenerator(theargs)
            self.assertEqual(0, gen.run())

            outdir = os.path.join(temp_dir, 'input_solution')
            self.assertTrue(os.path.isdir(outdir))

            # check system sizes
            with open(os.path.join(outdir, 'test_systemsizes.json'), 'r') as f:
                data = json.load(f)
                self.assertTrue('test179' in data)
                self.assertEqual(4, data['test179'])
                self.assertEqual(1, len(data))

            df = pd.read_csv(os.path.join(outdir, 'test_solution.csv'))

            self.assertEqual({'test179'}, set(df['solution'].values))
            self.assertEqual({'orig_a', 'orig_b', 'orig_c', 'orig_d'},
                             set(df['xxx'].values))

            df = pd.read_csv(os.path.join(outdir, 'csv_solution.csv'))
            self.assertEqual({'csv0', 'csv2'},
                             set(df['solution'].values))
            df_csv0 = df[df['solution'] == 'csv0']
            self.assertEqual({'orig_a', 'orig_b', 'orig_c',
                              'orig_d', 'orig_e', 'orig_f'},
                             set(df_csv0['xxx'].values))
            df_csv2 = df[df['solution'] == 'csv2']
            self.assertEqual({'orig_b', 'orig_c', 'orig_d'},
                             set(df_csv2['xxx'].values))

            df = pd.read_csv(os.path.join(outdir, 'combined_sol.csv'))
            self.assertEqual({'csv0', 'csv2', 'test179'},
                             set(df['solution'].values))
            self.assertEqual({0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12},
                             set(df['id'].values))
            df_csv0 = df[df['solution'] == 'csv0']
            self.assertEqual({'orig_a', 'orig_b', 'orig_c',
                              'orig_d', 'orig_e', 'orig_f'},
                             set(df_csv0['xxx'].values))
            df_csv2 = df[df['solution'] == 'csv2']
            self.assertEqual({'orig_b', 'orig_c', 'orig_d'},
                             set(df_csv2['xxx'].values))

            df_test179 = df[df['solution'] == 'test179']
            self.assertEqual({'orig_a', 'orig_b', 'orig_c', 'orig_d'},
                             set(df_test179['xxx'].values))

            self.assertEqual(13, len(df))
        finally:
            shutil.rmtree(temp_dir)

    def test_full_run_on_example_repls_keep_partials(self):
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
            solcsv = os.path.join(testdatadir, 'testsolution.csv')

            theargs = self._parser.parse_args([SolutionGenerator.COMMAND,
                                               temp_dir,
                                               '--input', input_dir,
                                               '--standards',
                                               solcx + ',genes,test,4,f',
                                               solcsv + ',csv,3,f'])

            gen = SolutionGenerator(theargs)
            self.assertEqual(0, gen.run())

            outdir = os.path.join(temp_dir, 'input_solution')
            self.assertTrue(os.path.isdir(outdir))

            # check system sizes
            with open(os.path.join(outdir, 'test_systemsizes.json'), 'r') as f:
                data = json.load(f)
                self.assertTrue('test179' in data)
                self.assertEqual(4, data['test179'])
                self.assertEqual(2, len(data))

            df = pd.read_csv(os.path.join(outdir, 'test_solution.csv'))

            self.assertEqual({'test179', 'test182'}, set(df['solution'].values))
            df_test179 = df[df['solution'] == 'test179']
            self.assertEqual({'orig_a', 'orig_b', 'orig_c', 'orig_d'},
                             set(df_test179['xxx'].values))

            df_test182 = df[df['solution'] == 'test182']
            self.assertEqual({'orig_a', 'orig_b', 'orig_d', 'orig_f'},
                             set(df_test182['xxx'].values))

            df = pd.read_csv(os.path.join(outdir, 'csv_solution.csv'))
            self.assertEqual({'csv0', 'csv2'},
                             set(df['solution'].values))
            df_csv0 = df[df['solution'] == 'csv0']
            self.assertEqual({'orig_a', 'orig_b', 'orig_c',
                              'orig_d', 'orig_e', 'orig_f'},
                             set(df_csv0['xxx'].values))
            df_csv2 = df[df['solution'] == 'csv2']
            self.assertEqual({'orig_b', 'orig_c', 'orig_d'},
                             set(df_csv2['xxx'].values))

            df = pd.read_csv(os.path.join(outdir, 'combined_sol.csv'))
            self.assertEqual({'csv0', 'csv2', 'test179', 'test182'},
                             set(df['solution'].values))
            self.assertEqual(set(range(17)),
                             set(df['id'].values))
            df_csv0 = df[df['solution'] == 'csv0']
            self.assertEqual({'orig_a', 'orig_b', 'orig_c',
                              'orig_d', 'orig_e', 'orig_f'},
                             set(df_csv0['xxx'].values))
            df_csv2 = df[df['solution'] == 'csv2']
            self.assertEqual({'orig_b', 'orig_c', 'orig_d'},
                             set(df_csv2['xxx'].values))

            df_test179 = df[df['solution'] == 'test179']
            self.assertEqual({'orig_a', 'orig_b', 'orig_c', 'orig_d'},
                             set(df_test179['xxx'].values))


            df_test182 = df[df['solution'] == 'test182']
            self.assertEqual({'orig_a', 'orig_b', 'orig_d', 'orig_f'},
                             set(df_test182['xxx'].values))

            self.assertEqual(17, len(df))
        finally:
            shutil.rmtree(temp_dir)


if __name__ == '__main__':
    unittest.main()
