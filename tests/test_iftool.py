import os
import unittest
from unittest.mock import patch, MagicMock, call

import pandas as pd

import cellmaps_utils
from cellmaps_utils import constants
from cellmaps_utils.exceptions import CellMapsError
from cellmaps_utils.iftool import (download_file, download_file_skip_existing, FakeImageDownloader,
                                   MultiProcessImageDownloader, IFImageDataConverter)


class TestDownloadFile(unittest.TestCase):
    @patch('requests.get')
    def test_download_file_success(self, mock_get):
        download_url = 'http://example.com/image.jpg'
        dest_file = 'tests/data/image.jpg'
        try:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.iter_content.return_value = [b'test data']
            mock_get.return_value.__enter__.return_value = mock_response

            result = download_file((download_url, dest_file))

            self.assertIsNone(result)
            mock_get.assert_called_once_with(download_url, stream=True)
        finally:
            if os.path.exists(dest_file):
                os.remove(dest_file)

    @patch('requests.get')
    def test_download_file_failure(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = 'Not Found'
        mock_get.return_value = mock_response
        mock_get.return_value.__enter__.return_value = mock_response

        download_url = 'http://example.com/image.jpg'
        dest_file = '/tmp/image.jpg'

        result = download_file((download_url, dest_file))

        self.assertIsNotNone(result)
        self.assertEqual(result[0], 404)
        self.assertIn('Not Found', result[1])

    @patch('cellmaps_utils.iftool.download_file')
    @patch('os.path.getsize')
    @patch('os.path.isfile')
    def test_skip_existing_file(self, mock_isfile, mock_getsize, mock_download_file):
        mock_isfile.return_value = True
        mock_getsize.return_value = 100
        downloadtuple = ('http://example.com/image.jpg', 'tests/data/existing_image.jpg')
        result = download_file_skip_existing(downloadtuple)
        mock_download_file.assert_not_called()
        self.assertIsNone(result)


class TestFakeImageDownloader(unittest.TestCase):
    @patch('cellmaps_utils.iftool.download_file')
    @patch('os.path.basename')
    @patch('shutil.copy')
    @patch('cellmaps_utils.iftool.tqdm')
    def test_download_images(self, mock_tqdm, mock_copy, mock_basename, mock_download_file):
        downloader = FakeImageDownloader()
        download_list = [('url1', '/path/to/destination1.jpg'), ('url2', '/path/to/destination2.jpg')]
        mock_download_file.return_value = None
        mock_basename.side_effect = lambda x: x.split('/')[-1]
        mock_tqdm.return_value = MagicMock()
        result = downloader.download_images(download_list)

        self.assertEqual(result, [])
        self.assertEqual(mock_download_file.call_count, 2)


class TestMultiProcessImageDownloader(unittest.TestCase):

    def test_default_poolsize_and_download_function(self):
        downloader = MultiProcessImageDownloader()
        self.assertEqual(downloader._poolsize, 4)
        self.assertEqual(downloader._dfunc, download_file)

    def test_poolsize_custom_value(self):
        custom_poolsize = 2
        downloader = MultiProcessImageDownloader(poolsize=custom_poolsize)
        self.assertEqual(downloader._poolsize, custom_poolsize)

    def test_skip_existing_true(self):
        downloader = MultiProcessImageDownloader(skip_existing=True)
        self.assertEqual(downloader._dfunc, download_file_skip_existing)

    def test_override_dfunc(self):
        custom_function = lambda x: "custom function called"
        downloader = MultiProcessImageDownloader(override_dfunc=custom_function)
        self.assertEqual(downloader._dfunc, custom_function)

    @patch('cellmaps_utils.iftool.Pool')
    @patch('cellmaps_utils.iftool.tqdm')
    def test_download_images(self, mock_tqdm, mock_pool):
        def imap_unordered_side_effect(func, iterable, chunksize=None):
            return (func(item) for item in iterable)

        mock_pool.return_value.__enter__.return_value.imap_unordered.side_effect = imap_unordered_side_effect

        downloader = MultiProcessImageDownloader(poolsize=2)
        downloader._dfunc = MagicMock(side_effect=lambda x: (404, 'Not Found', x) if x[1].endswith('2.jpg') else None)

        download_list = [
            ('http://example.com/image1.jpg', '/tmp/image1.jpg'),
            ('http://example.com/image2.jpg', '/tmp/image2.jpg')
        ]

        failed_downloads = downloader.download_images(download_list=download_list)

        self.assertEqual(len(failed_downloads), 1)
        self.assertIn((404, 'Not Found', ('http://example.com/image2.jpg', '/tmp/image2.jpg')), failed_downloads)

        mock_pool.assert_called_once_with(processes=2)

        mock_tqdm.assert_called_once_with(total=2, desc='Download', unit='images')

        self.assertEqual(downloader._dfunc.call_count, 2)
        downloader._dfunc.assert_any_call(('http://example.com/image1.jpg', '/tmp/image1.jpg'))
        downloader._dfunc.assert_any_call(('http://example.com/image2.jpg', '/tmp/image2.jpg'))


class TestIFImageDataConverter(unittest.TestCase):

    def setUp(self):
        self.mock_args = MagicMock(outdir='/fakepath', input='fake_input.csv', name='Test Name',
                                   organization_name='Test Org', project_name='Test Project',
                                   release='1.0', cell_line='Test Line', treatment='Test Treatment',
                                   author='Test Author', slice='Test Slice', gene_set='Test Set')
        self.converter = IFImageDataConverter(self.mock_args)

    @patch('cellmaps_utils.provenance.ProvenanceUtil')
    @patch('cellmaps_utils.iftool.MultiProcessImageDownloader')
    def test_initialization(self, mock_downloader, mock_provenance_util):
        self.assertEqual(self.converter._outdir, os.path.abspath('/fakepath'))
        self.assertEqual(self.converter._input, 'fake_input.csv')

    @patch('cellmaps_utils.iftool.uuid.uuid4', return_value='123456')
    def test_get_fairscape_id(self, mock_uuid4):
        expected_id = '123456:fakepath'
        result = self.converter._get_fairscape_id()
        self.assertEqual(result, expected_id)

    def test_generate_rocrate_dir_path(self):
        self.converter._generate_rocrate_dir_path()
        expected_dir_name = '/fakepath/test_project_test_set_test_line_test_treatment_ifimage_1.0'
        self.assertEqual(self.converter._outdir, expected_dir_name)

    @patch('os.path.isdir', side_effect=lambda x: False)
    @patch('os.makedirs')
    def test_create_output_directory_success(self, mock_makedirs, mock_isdir):
        self.converter._outdir = '/fakepath/test_dir'
        self.converter._create_output_directory()
        expected_calls = [call('/fakepath/test_dir', mode=0o755)] + \
                         [call('/fakepath/test_dir/' + color, mode=0o755) for color in constants.COLORS]
        mock_makedirs.assert_has_calls(expected_calls, any_order=True)

    @patch('os.path.isdir', return_value=True)
    def test_create_output_directory_exists_error(self, mock_isdir):
        self.converter._outdir = '/fakepath/existing_dir'
        with self.assertRaises(CellMapsError):
            self.converter._create_output_directory()

    def test_get_color_download_map(self):
        expected_map = {color: os.path.join('/fakepath', color) for color in constants.COLORS}
        color_d_map = self.converter._get_color_download_map()
        self.assertEqual(color_d_map, expected_map)

    def test_get_download_tuples(self):
        baselinks = ['http://example.com/image']
        expected_tuples = [
            ('http://example.com/imagered.jpg', '/fakepath/red/imagered.jpg'),
            ('http://example.com/imageblue.jpg', '/fakepath/blue/imageblue.jpg'),
            ('http://example.com/imagegreen.jpg', '/fakepath/green/imagegreen.jpg'),
            ('http://example.com/imageyellow.jpg', '/fakepath/yellow/imageyellow.jpg')
        ]
        dtuples = self.converter._get_download_tuples(baselinks)
        self.assertEqual(dtuples, expected_tuples)

    @patch('cellmaps_utils.iftool.IFImageDataConverter._retry_failed_images', return_value=[])
    @patch('cellmaps_utils.iftool.MultiProcessImageDownloader.download_images', return_value=[])
    def test_download_data_success(self, mock_download_images, mock_retry_failed_images):
        baselinks = ['http://example.com/image']
        result, failed_downloads = self.converter._download_data(baselinks)
        self.assertEqual(result, 0)
        self.assertEqual(len(failed_downloads), 0)

    @patch('cellmaps_utils.iftool.IFImageDataConverter._retry_failed_images')
    @patch('cellmaps_utils.iftool.MultiProcessImageDownloader.download_images', side_effect=[[(404, 'Error', 'http://example.com/image.jpg')], []])
    def test_download_data_with_retry(self, mock_download_images, mock_retry_failed_images):
        mock_retry_failed_images.return_value = []
        baselinks = ['http://example.com/image']
        result, failed_downloads = self.converter._download_data(baselinks)
        self.assertEqual(result, 0)
        self.assertEqual(len(failed_downloads), 0)
        mock_retry_failed_images.assert_called_once()

    @patch('cellmaps_utils.iftool.MultiProcessImageDownloader.download_images', return_value=[])
    def test_retry_failed_images(self, mock_download_images):
        failed_downloads = [(404, 'Not Found', 'http://example.com/image.jpg')]
        result = self.converter._retry_failed_images(failed_downloads)
        self.assertEqual(result, [])
        mock_download_images.assert_called_once_with(['http://example.com/image.jpg'])

    @patch('pandas.read_csv')
    def test_filter_apms_data(self, mock_read_csv):
        mock_df = pd.DataFrame({
            'Slice': ['Test Slice', 'Other Slice'],
            'Treatment': ['Test Treatment', 'Other Treatment'],
            'OtherColumn': [1, 2]
        })
        mock_read_csv.return_value = mock_df
        expected_df = mock_df[(mock_df['Slice'] == 'Test Slice') & (mock_df['Treatment'].str.contains('Test Treatment', case=False))]
        filtered_df = self.converter._filter_apms_data()
        mock_read_csv.assert_called_once_with('fake_input.csv', sep=',')
        pd.testing.assert_frame_equal(filtered_df.reset_index(drop=True), expected_df.reset_index(drop=True), check_like=True)

    def test_add_subparser(self):
        mock_subparsers = MagicMock()
        mock_parser = MagicMock()
        mock_parser.add_argument = MagicMock()
        mock_subparsers.add_parser = MagicMock(return_value=mock_parser)
        IFImageDataConverter.add_subparser(mock_subparsers)
        mock_subparsers.add_parser.assert_called_with('ifconverter',
                                                      help='Loads IF Image data into a RO-Crate',
                                                      description='\n\n        '
                                                                  'Version 0.4.0a1\n\n        '
                                                                  'ifconverter Loads IF Image '
                                                                  'data into a RO-Crate\n        ',
                                                      formatter_class=cellmaps_utils.constants.ArgParseFormatter)
        mock_parser.add_argument.assert_called()

