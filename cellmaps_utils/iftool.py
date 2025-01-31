import os
import re
import shutil
import uuid
from datetime import date
import warnings
import logging
import requests
from tqdm import tqdm
from multiprocessing import Pool
import pandas as pd
import cellmaps_utils
from cellmaps_utils.basecmdtool import BaseCommandLineTool
from cellmaps_utils.exceptions import CellMapsError
from cellmaps_utils import constants
from cellmaps_utils.provenance import ProvenanceUtil

logger = logging.getLogger(__name__)


def download_file_skip_existing(downloadtuple):
    """
    Downloads file in **downloadtuple** unless the file already exists
    with a size greater then 0 bytes, in which case function
    just returns

    :param downloadtuple: (download link, dest file path)
    :type downloadtuple: tuple
    :return: None upon success otherwise:
             (requests status code, text from request, downloadtuple)
    :rtype: tuple
    """
    if os.path.isfile(downloadtuple[1]) and os.path.getsize(downloadtuple[1]) > 0:
        return None
    return download_file(downloadtuple)


def download_file(downloadtuple):
    """
    Downloads file pointed to by 'download_url' to
    'destfile'

    .. note::

        Default download function used by :py:class:`~MultiProcessImageDownloader`

    :param downloadtuple: `(download link, dest file path)`
    :type downloadtuple: tuple
    :return: None upon success otherwise:
             `(requests status code, text from request, downloadtuple)`
    :rtype: tuple
    """
    logger.debug('Downloading ' + downloadtuple[0] + ' to ' + downloadtuple[1])
    try:
        with requests.get(downloadtuple[0], stream=True) as r:
            if r.status_code != 200:
                return r.status_code, r.text, downloadtuple
            with open(downloadtuple[1], 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:  # filter out keep-alive new chunks
                        f.write(chunk)
        return None
    except requests.exceptions.HTTPError as e:
        return -1, str(e), downloadtuple
    except requests.exceptions.ConnectionError as e:
        return -2, str(e), downloadtuple
    except requests.exceptions.Timeout as e:
        return -3, str(e), downloadtuple
    except requests.exceptions.RequestException as e:
        return -4, str(e), downloadtuple
    except Exception as e:
        return -5, str(e), downloadtuple


class ImageDownloader(object):
    """
    Abstract class that defines interface for classes that download images

    """
    def __init__(self):
        """

        """
        pass

    def download_images(self, download_list=None):
        """
        Subclasses should implement

        :param download_list: list of tuples where first element is
                              full URL of image to download and 2nd
                              element is destination path
        :type download_list: list
        :return:
        """
        raise CellMapsError('Subclasses should implement this')


class FakeImageDownloader(ImageDownloader):
    """
    Creates fake download by downloading
    the first image in each color from
    `Human Protein Atlas <https://www.proteinatlas.org/>`__
    and making renamed copies. The :py:func:`download_file` function
    is used to download the first image of each color

    """

    def __init__(self):
        """
        Constructor

        """
        super().__init__()
        warnings.warn('This downloader generates FAKE images\n'
                      'You have been warned!!!\n'
                      'Have a nice day')

    def download_images(self, download_list=None):
        """
        Downloads 1st image from server and then
        and makes renamed copies for subsequent images

        :param download_list:
        :type download_list: list of tuple
        :return:
        """
        num_to_download = len(download_list)
        logger.info(str(num_to_download) + ' images to download')
        t = tqdm(total=num_to_download, desc='Download',
                 unit='images')

        src_image_dict = {}
        # assume 1st four images are the colors for the first image
        for entry in download_list[0:4]:
            t.update()
            if download_file(entry) is not None:
                raise CellMapsError('Unable to download ' +
                                    str(entry))
            fname = os.path.basename(entry[1])
            color = re.sub(r'\..*$', '', re.sub('^.*_', '', fname))
            src_image_dict[color] = entry[1]

        for entry in download_list[5:]:
            t.update()
            fname = os.path.basename(entry[1])
            color = re.sub(r'\..*$', '', re.sub('^.*_', '', fname))
            shutil.copy(src_image_dict[color], entry[1])
        return []


class MultiProcessImageDownloader(ImageDownloader):
    """
    Uses multiprocess package to download images in parallel

    """

    def __init__(self, poolsize=4, skip_existing=False,
                 override_dfunc=None):
        """
        Constructor

        .. warning::

            Exceeding **poolsize** of ``4`` causes errors from Human Protein Atlas site

        :param poolsize: Number of concurrent downloaders to use.
        :type poolsize: int
        :param skip_existing: If ``True`` skip download if image file exists and has size
                              greater then ``0``
        :type skip_existing: bool
        :param override_dfunc: Function that takes a tuple `(image URL, download str path)`
                               and downloads the image. If ``None`` :py:func:`download_file`
                               function is used
        :type override_dfunc: :py:class:`function`
        """
        super().__init__()
        self._poolsize = poolsize
        if override_dfunc is not None:
            self._dfunc = override_dfunc
        else:
            self._dfunc = download_file
            if skip_existing is True:
                self._dfunc = download_file_skip_existing

    def download_images(self, download_list=None):
        """
        Downloads images returning a list of failed downloads

        .. code-block::

            from cellmaps_imagedownloader.runner import MultiProcessImageDownloader

            dloader = MultiProcessImageDownloader(poolsize=2)

            d_list = [('https://images.proteinatlas.org/992/1_A1_1_red.jpg',
                       '/tmp/1_A1_1_red.jpg')]
            failed = dloader.download_images(download_list=d_list)

        :param download_list: Each tuple of format `(image URL, dest file path)`
        :type download_list: list of tuple
        :return: Failed downloads, format of tuple
                 (`http status code`, `text of error`, (`link`, `destfile`))
        :rtype: list of tuple
        """
        failed_downloads = []
        logger.debug('Poolsize for image downloader set to: ' +
                     str(self._poolsize))
        with Pool(processes=self._poolsize) as pool:
            num_to_download = len(download_list)
            logger.info(str(num_to_download) + ' images to download')
            t = tqdm(total=num_to_download, desc='Download',
                     unit='images')
            for i in pool.imap_unordered(self._dfunc,
                                         download_list):
                t.update()
                if i is not None:
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug('Failed download: ' + str(i))
                    failed_downloads.append(i)
        return failed_downloads


class IFImageDataConverter(BaseCommandLineTool):
    """
    Converts IF Image data into format consumable
    by Cell Maps Pipeline
    """
    COMMAND = 'ifconverter'

    def __init__(self, theargs,
                 imgsuffix='.jpg',
                 provenance_utils=ProvenanceUtil(),
                 imagedownloader=None):
        """
        Constructor

        :param theargs: Command line arguments that at minimum need
                        to have the following attributes:
        :type theargs: :py:class:`~python.argparse.Namespace`
        """
        super().__init__()
        self._outdir = os.path.abspath(theargs.outdir)
        self._input = theargs.input
        self._name = theargs.name
        self._organization_name = theargs.organization_name
        self._project_name = theargs.project_name
        self._release = theargs.release
        self._cell_line = theargs.cell_line
        self._treatment = theargs.treatment
        self._tissue = theargs.tissue
        self._author = theargs.author
        self._slice = theargs.slice
        self._gene_set = theargs.gene_set
        self._imgsuffix = imgsuffix
        self._provenance_utils = provenance_utils
        if imagedownloader is not None:
            self._imagedownloader = imagedownloader
        else:
            self._imagedownloader = MultiProcessImageDownloader()
        self._softwareid = None
        self._image_dataset_ids = None

        self._input_data_dict = theargs.__dict__

    def run(self):
        """
        Runs the process of converting IF Image data into a format consumable by the Cell Maps Pipeline.
        This includes generating a directory path for the RO-Crate, creating the output directory, registering
        the RO-Crate, filtering the input data based on criteria, downloading and organizing the images.
        It also handles the registration of datasets and computations in the FAIRSCAPE ecosystem.

        :return:
        :rtype: int
        """
        self._generate_rocrate_dir_path()
        self._create_output_directory()

        keywords = [self._project_name, self._release,
                    self._cell_line, self._treatment, 'IF microscopy', 'images',
                    self._tissue]

        if self._gene_set is not None:
            keywords.append(self._gene_set)

        description = ' '.join(keywords)

        info_dict = {
            constants.DATASET_NAME: self._name,
            constants.DATASET_ORGANIZATION_NAME: self._organization_name,
            constants.DATASET_PROJECT_NAME: self._project_name,
            constants.DATASET_RELEASE: self._release,
            constants.DATASET_CELL_LINE: self._cell_line,
            constants.DATASET_TREATMENT: self._treatment,
            constants.DATASET_TISSUE: self._tissue,
            constants.DATASET_AUTHOR: self._author,
            constants.DATASET_SLICE: self._slice,
            constants.DATASET_GENE_SET: self._gene_set
        }

        self.save_dataset_info_to_json(self._outdir, info_dict, constants.DATASET_INFO_FILE)

        self._provenance_utils.register_rocrate(self._outdir,
                                                name=self._name,
                                                organization_name=self._organization_name,
                                                project_name=self._project_name,
                                                description=description,
                                                keywords=keywords,
                                                guid=self._get_fairscape_id())
        gen_dsets = []

        filtered_df = self._filter_apms_data()

        # copy over readme
        shutil.copy(os.path.join(os.path.dirname(__file__), 'ifimage_readme.txt'),
                    os.path.join(self._outdir, 'readme.txt'))

        # download the images
        if 'Baselink' in filtered_df:
            baselink_name = 'Baselink'
        else:
            baselink_name = 'base_web_link'

        self._download_data(filtered_df[baselink_name].values.tolist())

        # remove Baselink column
        filtered_df.drop(baselink_name, axis=1, inplace=True)

        # remove Slice column if set
        if self._slice is not None:
            if 'Slice' in filtered_df:
                filtered_df.drop('Slice', axis=1, inplace=True)

        file_path = os.path.join(self._outdir, constants.ANTIBODY_GENE_TABLE_FILE)

        filtered_df.to_csv(file_path, sep='\t', index=False)

        file_desc = description + ' file'
        file_keywords = keywords.copy()
        file_keywords.extend(['file'])
        dset_id = self._provenance_utils.register_dataset(rocrate_path=self._outdir, source_file=file_path,
                                                          skip_copy=True,
                                                          data_dict={'name': 'IF Image Gene file',
                                                                     'description': file_desc,
                                                                     'keywords': file_keywords,
                                                                     'data-format': 'tsv',
                                                                     'author': self._author,
                                                                     'version': self._release,
                                                                     'date-published': date.today().strftime('%Y-%m-%d')},
                                                          guid=self._get_fairscape_id())
        gen_dsets.append(dset_id)
        gen_dsets.extend(self._register_downloaded_images(description=description,
                                                          keywords=keywords))
        self._register_software(keywords=keywords, description=description)
        logger.info('Registering only 1st 1000 datasets into computation due to limitations of fairscape-cli')
        self._register_computation(generated_dataset_ids=gen_dsets[:1000],
                                   description=description,
                                   keywords=keywords)
        return 0

    def _get_fairscape_id(self):
        """
        Creates a unique id
        :return:
        """
        return str(uuid.uuid4()) + ':' + os.path.basename(self._outdir)

    def _generate_rocrate_dir_path(self):
        """
        Generates the directory path for the RO-Crate based on project-specific attributes such as project name,
        gene set, cell line, treatment, and release version.

        :return:
        """
        dir_name = self._project_name.lower() + '_'
        if self._gene_set is not None:
            dir_name += self._gene_set.lower() + '_'
        dir_name += self._cell_line.lower() + '_'
        dir_name += self._treatment.lower() + '_ifimage_'
        dir_name += self._release.lower()

        dir_name = dir_name.replace(' ', '_')
        self._outdir = os.path.join(self._outdir, dir_name)

    def _create_output_directory(self):
        """
        Creates output directory if it does not already exist

        :raises CellmapsDownloaderError: If output directory is None or if directory already exists
        """
        if os.path.isdir(self._outdir):
            raise CellMapsError(self._outdir + ' already exists')

        os.makedirs(self._outdir, mode=0o755)
        for cur_color in constants.COLORS:
            cdir = os.path.join(self._outdir, cur_color)
            if not os.path.isdir(cdir):
                logger.debug('Creating directory: ' + cdir)
                os.makedirs(cdir,
                            mode=0o755)

    def _get_color_download_map(self):
        """
        Creates a dict where key is color name and value is directory
        path for files for that color

        ``{'red': '/tmp/foo/red'}``

        :return: map of colors to directory paths
        :rtype: dict
        """
        color_d_map = {}
        for c in constants.COLORS:
            color_d_map[c] = os.path.join(self._outdir, c)
        return color_d_map

    def _get_download_tuples(self, baselinks=None):
        """
        Gets download list from **imageurlgen** object set via constructor

        :return: list of (image download URL prefix,
                          file path where image should be written)
        :rtype: list
        """
        dtuples = []
        color_map = self._get_color_download_map()
        for link in baselinks:
            for c in constants.COLORS:
                link_w_filename = link + c + '.jpg'
                dtuples.append((link_w_filename,
                                os.path.join(color_map[c],
                                             os.path.basename(link_w_filename))))
        logger.debug('Returning ' + str(len(dtuples)) + ' download tuples')
        logger.debug(str(dtuples))
        return dtuples

    def _download_data(self, baselinks=None,
                       max_retry=5):
        """
        Initiates the download of images based on a list of base URLs. It manages the download process, retries failed
        downloads up to a maximum number of attempts, and logs any errors encountered.

        :param baselinks: A list of base URLs for image download.
        :type baselinks: list
        :param max_retry: Maximum number of retries for failed downloads.
        :type max_retry: int
        :return: A tuple containing the status (0 for success) and a list of failed downloads.
        :rtype: tuple
        """
        dtuples = self._get_download_tuples(baselinks=baselinks)

        failed_downloads = self._imagedownloader.download_images(dtuples)
        retry_count = 0
        while len(failed_downloads) > 0 and retry_count < max_retry:
            retry_count += 1
            logger.error(str(len(failed_downloads)) +
                         ' images failed to download. Retrying #' + str(retry_count))

            # try one more time with files that failed
            failed_downloads = self._retry_failed_images(failed_downloads=failed_downloads)

        if len(failed_downloads) > 0:
            raise CellMapsError('Failed to download: ' +
                                str(len(failed_downloads)) + ' images')
        return 0, failed_downloads

    def _retry_failed_images(self, failed_downloads=None):
        """
        Attempts to re-download images that failed in the initial download attempt. It organizes the failed downloads
        based on error codes, logs the failure counts, and retries the downloads.

        :param failed_downloads: A list of failed downloads to retry.
        :type failed_downloads: list
        :return: A list of downloads that failed after retrying.
        :rtype: list
        """
        downloads_to_retry = []
        error_code_map = {}
        for entry in failed_downloads:
            if entry[0] not in error_code_map:
                error_code_map[entry[0]] = 0
            error_code_map[entry[0]] += 1
            downloads_to_retry.append(entry[2])
        logger.debug('Failed download counts by http error code: ' + str(error_code_map))
        return self._imagedownloader.download_images(downloads_to_retry)

    def _filter_apms_data(self):
        """
        Loads input, set via constructor, as :py:class:`pandas.DataFrame`
        and filters that :py:class:`pandas.DataFrame` to only
        keep rows matching the slice and treatment passed in via
        the constructor

        :return: Filtered rows
        :rtype: :py:class:`pandas.DataFrame`
        """
        df = pd.read_csv(self._input, sep=',')

        # keep only slice specified
        if self._slice is not None:
            if 'Slice' in df:
                logger.info('Keeping only slice: ' + str(self._slice))
                df = df[df['Slice'] == self._slice]
                logger.debug(str(len(df)) + ' rows remain after slice filter')
            else:
                # attempt to find slice from base_web_link
                if 'base_web_link' in df:
                    logger.info('Keeping only slice: ' + str(self._slice) + ' by parsing base_web_link')
                    df = df[df['base_web_link'].str.contains('_' + self._slice + '_', case=False)]
                    logger.debug(str(len(df)) + ' rows remain after slice filter')

        # keep only treatment specified
        logger.info('Keeping only treatment: ' + str(self._treatment))
        df = df[df['Treatment'].str.contains(self._treatment, case=False)]
        logger.debug(str(len(df)) + ' rows remain after treatment filter')

        # remove negative-ctrl rows
        logger.debug('Removing NEGATIVE rows')
        df = df[df["Antibody ID"].str.contains('NEGATIVE') == False]

        return df

    def _register_downloaded_images(self,
                                    description='',
                                    keywords=[]):
        """
        Registers all the downloaded images
        :return:
        """
        data_dict = {'name': cellmaps_utils.__name__ + ' downloaded image',
                     'description': description + ' IF image file',
                     'data-format': self._imgsuffix[1:],
                     'author': self._author,
                     'version': self._release,
                     'date-published': date.today().strftime('%Y-%m-%d')}

        dset_ids = []

        for c in constants.COLORS:
            for entry in tqdm(os.listdir(os.path.join(self._outdir, c)), desc='FAIRSCAPE ' + c + ' images registration'):
                if not entry.endswith(self._imgsuffix):
                    continue
                fullpath = os.path.join(self._outdir, c, entry)
                data_dict['name'] = entry + ' ' + c +\
                                    ' channel image'
                if len(data_dict['name']) >= 64:
                    data_dict['name'] = '...' + data_dict['name'][-60:]
                data_dict['keywords'] = keywords.copy()
                data_dict['keywords'].extend([c, 'IF', 'image', constants.COLOR_LABELS_MAP[c]])
                dset_ids.append(self._provenance_utils.register_dataset(self._outdir,
                                                                        source_file=fullpath,
                                                                        data_dict=data_dict,
                                                                        skip_copy=True,
                                                                        guid=self._get_fairscape_id()))

                del data_dict['keywords']

        return dset_ids

    def _register_computation(self, generated_dataset_ids=[],
                              description='',
                              keywords=[]):
        """
        Registers the computational process executed by this tool
        # Todo: added in used dataset, software and what is being generated
        :return:
        """
        logger.debug('Getting id of input rocrate')
        comp_keywords = keywords.copy()
        comp_keywords.extend(['computation'])
        description = description + ' run of ' + cellmaps_utils.__name__
        self._provenance_utils.register_computation(self._outdir,
                                                    name='IF images',
                                                    run_by=str(self._provenance_utils.get_login()),
                                                    command=str(self._input_data_dict),
                                                    description=description,
                                                    keywords=comp_keywords,
                                                    used_software=[self._softwareid],
                                                    generated=generated_dataset_ids,
                                                    guid=self._get_fairscape_id())

    def _register_software(self, description='',
                           keywords=[]):
        """
        Registers this tool

        :raises CellMapsImageEmbeddingError: If fairscape call fails
        """
        software_keywords = keywords.copy()
        software_keywords.extend(['tools', cellmaps_utils.__name__])
        software_description = description + ' ' + \
                               cellmaps_utils.__description__
        self._softwareid = self._provenance_utils.register_software(self._outdir,
                                                                    name=cellmaps_utils.__name__,
                                                                    description=software_description,
                                                                    author=cellmaps_utils.__author__,
                                                                    version=cellmaps_utils.__version__,
                                                                    file_format='py',
                                                                    keywords=software_keywords,
                                                                    url=cellmaps_utils.__repo_url__,
                                                                    guid=self._get_fairscape_id())

    def add_subparser(subparsers):
        """
        Adds command-line argument parsing for the IFImageDataConverter tool.

        :return:
        """
        desc = """

        Version {version}

        {cmd} Loads IF Image data into a RO-Crate
        """.format(version=cellmaps_utils.__version__,
                   cmd=IFImageDataConverter.COMMAND)

        parser = subparsers.add_parser(IFImageDataConverter.COMMAND,
                                       help='Loads IF Image data into a RO-Crate',
                                       description=desc,
                                       formatter_class=constants.ArgParseFormatter)
        parser.add_argument('outdir',
                            help='Directory where RO-Crate will be created')
        parser.add_argument('--input', required=True,
                            help='Table file with the following '
                                 'fields: [Antibody ID, ENSEMBL ID|ENSG, Treatment, Well, Region, Slice, Baselink|base_web_link] ')
        parser.add_argument('--author', default='Lundberg Lab',
                            help='Author that created this data')
        parser.add_argument('--name', default='IF images',
                            help='Name of this run, needed for FAIRSCAPE')
        parser.add_argument('--organization_name', default='Lundberg Lab',
                            help='Name of organization running this tool, needed '
                                 'for FAIRSCAPE. Usually set to lab')
        parser.add_argument('--project_name', default='CM4AI',
                            help='Name of project running this tool, needed for '
                                 'FAIRSCAPE. Usually set to funding source')
        parser.add_argument('--release', required=True,
                            help='Version of release. For example: 0.1 alpha')
        parser.add_argument('--treatment', default='untreated',
                            choices=['paclitaxel', 'vorinostat', 'untreated'],
                            help='Treatment of sample.')
        parser.add_argument('--cell_line', default='MDA-MB-468',
                            help='Name of cell line. For example MDA-MB-468')
        parser.add_argument('--gene_set', choices=['chromatin', 'metabolic'],
                            help='Gene set for dataset, standard names are '
                                 + 'chromatin, metabolic, or leave it unset')
        parser.add_argument('--tissue', choices=['undifferentiated', 'neuron',
                                                 'cardiomyocytes', ''],
                            default='breast; mammary gland',
                            help='Tissue for dataset. Since the default --cell_line '
                                 'is MDA-MB-468, this value is set to the tissue '
                                 'for that cell line')
        parser.add_argument('--slice',
                            help='Slice to keep. Example names are z01, z02. If unset '
                                 + 'all slices are kept')

        return parser

