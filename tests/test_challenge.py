import os
import shutil
import tempfile
import unittest
import uuid

import pandas as pd

import cellmaps_utils
from cellmaps_utils.challenge import *
from cellmaps_utils.challenge import _get_dataframe
from cellmaps_utils.challenge import _get_set_of_all_values_of_column_from_dataframes
from cellmaps_utils.challenge import _generate_mapping
from cellmaps_utils.crisprtool import CellMapsError


class TestChallengeModule(unittest.TestCase):

    def setUp(self):
        pass


    def tearDown(self):
        pass

    def test_get_set_of_all_values_of_column_from_dataframes_no_dataframe(self):
        try:
            _get_set_of_all_values_of_column_from_dataframes(None, col_name='xx')
        except CellMapsError as e:
            self.assertTrue('dataframes cannot be None' in str(e))

    def test_get_set_of_all_values_of_column_from_dataframes_no_col_name(self):
        df = pd.DataFrame({'col1': ['val']})
        try:
            _get_set_of_all_values_of_column_from_dataframes([df], col_name=None)
        except CellMapsError as e:
            self.assertTrue('Column name' in str(e))


    def test_get_set_of_all_values_of_column_from_dataframes_not_list(self):
        df = pd.DataFrame(data={'col1': ['val']})
        res = _get_set_of_all_values_of_column_from_dataframes(dataframes=df,
                                                               col_name='col1')
        self.assertEqual({'val'}, res)

    def test_get_dataframe_and_write_tsv_file(self):
        temp_dir = tempfile.mkdtemp()
        try:
            dest_file = os.path.join(temp_dir, REPL_MAPPING)
            df = pd.DataFrame({'col1': ['val1'], 'col2': ['val2']})
            write_tsv_file(df=df, outfile=dest_file)

            check_df = _get_dataframe(dest_file)
            self.assertTrue(len(check_df.columns) == 2)
            self.assertTrue('col1' in check_df.columns)
            self.assertTrue('col2' in check_df.columns)
            self.assertTrue('val1' in check_df['col1'].values)
            self.assertTrue('val2' in check_df['col2'].values)
        finally:
            shutil.rmtree(temp_dir)


    def test_get_set_of_all_values_of_column_from_dataframes(self):
        df1 = pd.DataFrame(data={'col1': ['1', '2'], 'col2': ['3', '4']})
        df2 = pd.DataFrame(data={'col1': ['5', '2'], 'col2': ['6', '8']})
        res = _get_set_of_all_values_of_column_from_dataframes([df1, df2],
                                                               col_name='col1')
        self.assertEqual({'1', '2', '5'}, res)

        res = _get_set_of_all_values_of_column_from_dataframes([df1, df2],
                                                               col_name='col2')
        self.assertEqual({'3', '4', '6', '8'}, res)

    def test_generate_mapping(self):
        cvals = {'a', 'b', 'c', 'd'}

        res = _generate_mapping(col_vals=cvals, num_chars=6, mapping_col_name='foo',
                                input_repl_one='first',
                                input_repl_two='second')
        self.assertTrue('forward' in res)
        self.assertTrue('reverse' in res)
        self.assertTrue(len(res['forward']) == 4)
        self.assertTrue(len(res['reverse']) == 4)
        self.assertTrue(res[REPL_ONE_TSV] == 'first')
        self.assertTrue(res[REPL_TWO_TSV] == 'second')

        self.assertTrue('mapped_column_name' in res)
        self.assertTrue(res['mapped_column_name'] == 'foo')
        val_set = set()
        for c in cvals:
            self.assertTrue(res['reverse'][res['forward'][c]] == c)
            self.assertTrue(len(res['forward'][c]) == 6)
            val_set.add(res['forward'][c])
        self.assertTrue(len(val_set) == 4)

    def test_set_id_col_and_rename_othercols(self):
        df = pd.DataFrame(data={'PG.ProteinGroups': ['x', 'y'], 'PG.Genes': ['zz', 'zz'],
                                'PG.UniProtIds': ['sd', 'asd'], 'PG.ProteinNames': ['h', 'i'],
                                'PG.ProteinAccessions': ['a', 'b'], 'col2': ['3', '4'],
                                'col4': ['2', '6']})

        res = set_id_col_and_rename_othercols(df=df, col_name='PG.ProteinAccessions',
                                              id_mapping={'forward': {'a': 'encode_a', 'b': 'encode_b'}},
                                              id_col_name='xxx')

        self.assertTrue(res.columns.tolist() == ['xxx', '1', '2'])
        self.assertTrue(list(res['xxx']) == ['encode_a', 'encode_b'])
        self.assertTrue(list(res['1']) == ['3', '4'])
        self.assertTrue(list(res['2']) == ['2', '6'])

    def test_get_col_repl_map_invalid_inputs(self):
        try:
            get_col_repl_map(prefix=None, columns=[])
            self.fail('Expected CellMapsError')
        except CellMapsError as e:
            self.assertTrue('prefix is' in str(e))

        try:
            get_col_repl_map(prefix='foo', columns=None)
            self.fail('Expected CellMapsError')
        except CellMapsError as e:
            self.assertTrue('columns is' in str(e))

        try:
            get_col_repl_map(prefix='foo', columns=[], idcol=None)
            self.fail('Expected CellMapsError')
        except CellMapsError as e:
            self.assertTrue('idcol is' in str(e))

    def test_get_col_repl_map(self):
        res = get_col_repl_map(prefix='repl1_', columns=['xxx','xxxy','z'])
        self.assertTrue(len(res.keys()) == 3)
        self.assertEqual(res['xxx'], 'xxx')
        self.assertEqual(res['xxxy'], 'repl1_xxxy')
        self.assertEqual(res['z'], 'repl1_z')

    def test_get_system_to_gene_count(self):
        gene_to_system_mapping = {'gene1': [1, 2, 3],
                                  'gene2': [1]}
        res = get_system_to_gene_count(gene_to_system_mapping)
        self.assertTrue(len(res) == 3)
        self.assertTrue(res[1] == 2)
        self.assertTrue(res[2] == 1)
        self.assertTrue(res[3] == 1)

    def test_merge_replicate_dataframes(self):
        repl1 = pd.DataFrame({'xxx': [1, 2, 3],
                              'r1a': [4, 5, 6],
                              'r1b': [7, 8, 9]})
        repl2 = pd.DataFrame({'xxx': [1, 2, 3],
                              'r2a': [10, 11, 12],
                              'r2b': [13, 14, 15]})
        df = merge_replicate_dataframes(repl1_df=repl1,
                                        repl2_df=repl2)

        self.assertEqual(len(df.columns), 5)
        self.assertEqual(list(df.columns), ['xxx', 'repl1_r1a', 'repl1_r1b',
                         'repl2_r2a', 'repl2_r2b'])
        self.assertEqual(list(df['xxx'].values),
                         list(repl1['xxx'].values))
        for orig in ['r1a', 'r1b']:
            colname = 'repl1_' + orig
            self.assertEqual(list(df[colname].values),
                             list(repl1[orig].values), 'repl1: ' + str(repl1.head()))
        for orig in ['r2a', 'r2b']:
            colname = 'repl2_' + orig
            self.assertEqual(list(df[colname].values),
                             list(repl2[orig].values), 'repl2: ' + str(repl2.head()))


if __name__ == '__main__':
    unittest.main()
