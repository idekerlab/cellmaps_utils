import os
import shutil
import tempfile
import unittest
import uuid

import pandas as pd

import cellmaps_utils
from cellmaps_utils.challenge import *
from cellmaps_utils.crisprtool import CellMapsError


class TestChallengeModule(unittest.TestCase):

    def setUp(self):
        pass


    def tearDown(self):
        pass

    def test_get_set_of_all_values_of_column_from_dataframes_no_dataframe(self):
        try:
            get_set_of_all_values_of_column_from_dataframes(None, col_name='xx')
        except CellMapsError as e:
            self.assertTrue('dataframes cannot be None' in str(e))

    def test_get_set_of_all_values_of_column_from_dataframes_no_col_name(self):
        df = pd.DataFrame({'col1': ['val']})
        try:
            get_set_of_all_values_of_column_from_dataframes([df], col_name=None)
        except CellMapsError as e:
            self.assertTrue('Column name' in str(e))


    def test_get_set_of_all_values_of_column_from_dataframes_not_list(self):
        df = pd.DataFrame(data={'col1': ['val']})
        res = get_set_of_all_values_of_column_from_dataframes(dataframes=df,
                                                              col_name='col1')
        self.assertEqual({'val'}, res)

    def test_get_dataframe_and_write_tsv_file(self):
        temp_dir = tempfile.mkdtemp()
        try:
            dest_file = os.path.join(temp_dir, REPL_MAPPING)
            df = pd.DataFrame({'col1': ['val1'], 'col2': ['val2']})
            write_tsv_file(df=df, outfile=dest_file)

            check_df = get_dataframe(dest_file)
            self.assertTrue(len(check_df.columns) == 2)
            self.assertTrue('col1' in check_df.columns)
            self.assertTrue('col2' in check_df.columns)
            self.assertTrue('val1' in check_df['col1'].values)
            self.assertTrue('val2' in check_df['col2'].values)
        finally:
            shutil.rmtree(temp_dir)

    def test_write_mapping_file(self):
        temp_dir = tempfile.mkdtemp()
        try:
            dest_file = os.path.join(temp_dir, REPL_MAPPING)
            write_id_mapping_file(temp_dir, id_mapping={'hi': 'there'})
            with open(dest_file, 'r') as f:
                data = json.load(f)
            self.assertTrue(data['hi'] == 'there')
        finally:
            shutil.rmtree(temp_dir)

    def test_get_set_of_all_values_of_column_from_dataframes(self):
        df1 = pd.DataFrame(data={'col1': ['1', '2'], 'col2': ['3', '4']})
        df2 = pd.DataFrame(data={'col1': ['5', '2'], 'col2': ['6', '8']})
        res = get_set_of_all_values_of_column_from_dataframes([df1, df2],
                                                              col_name='col1')
        self.assertEqual({'1', '2', '5'}, res)

        res = get_set_of_all_values_of_column_from_dataframes([df1, df2],
                                                              col_name='col2')
        self.assertEqual({'3', '4', '6', '8'}, res)

    def test_generate_mapping(self):
        cvals = {'a', 'b', 'c', 'd'}

        res = generate_mapping(col_vals=cvals, num_chars=6, mapping_col_name='foo',
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


if __name__ == '__main__':
    unittest.main()
