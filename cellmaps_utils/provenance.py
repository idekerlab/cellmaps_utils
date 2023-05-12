
import os
import subprocess
import logging
import uuid
from datetime import date
import json

from cellmaps_utils import constants
from cellmaps_utils.exceptions import CellMapsProvenanceError
logger = logging.getLogger(__name__)


class ProvenanceUtil(object):
    """
    Wrapper around `FAIRSCAPE <https://fairscape.github.io>`__ calls
    """
    def __init__(self, fairscape_binary='fairscape-cli'):
        """
        Constructor

        :param fairscape_binary: `FAIRSCAPE <https://github.com/fairscape/fairscape-cli>`__ command line binary
        :type fairscape_binary: str
        """
        self._binary = fairscape_binary

    def _run_cmd(self, cmd, cwd=None, timeout=360):
        """
        Runs command as a command line process

        :param cmd_to_run: command to run as list
        :type cmd_to_run: list
        :return: (return code, standard out, standard error)
        :rtype: tuple
        """
        logger.debug('Running command under ' + str(cwd) +
                     ' path: ' + str(cmd))
        p = subprocess.Popen(cmd, cwd=cwd,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        try:
            out, err = p.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            logger.warning('Timeout reached. Killing process')
            p.kill()
            out, err = p.communicate()
            raise CellMapsProvenanceError('Process timed out. exit code: ' +
                                          str(p.returncode) +
                                          ' stdout: ' + str(out) +
                                          ' stderr: ' + str(err))

        return p.returncode, out, err

    @staticmethod
    def example_dataset_provenance(requiredonly=True, with_ids=False):
        """
        Returns example provenance dataset dict

        :param requiredonly: If ``True`` only output required fields,
                             otherwise output all fields. This is ignored
                             if **with_ids** parameter is ``True``
        :type requiredonly: bool
        :param with_ids: If ``True`` ignore **requiredonly** and just output
                         dict where caller has dataset id
        :type with_ids: bool
        :return: Example provenance dictionary
        :rtype: dict
        """
        if with_ids is not None and with_ids is True:
            return {'guid': 'ID of dataset'}

        field_dict = {'name': 'Name of dataset',
                      'author': 'Author of dataset',
                      'version': 'Version of dataset',
                      'date-published': 'Date dataset was published',
                      'description': 'Description of dataset',
                      'data-format': 'Format of data'}
        if requiredonly is None or requiredonly is False:
            field_dict.update({'url': 'URL of datset',
                               'used-by': '?',
                               'derived-from': '?',
                               'associated-publication': '?',
                               'additional-documentation': '?'})
        return field_dict


    def get_id_of_rocrate(self, rocrate_path):
        """

        :param rocrate_path:
        :return:
        """
        if rocrate_path is None:
            raise CellMapsProvenanceError('rocrate_path is None')

        if os.path.isdir(rocrate_path):
            rocrate_file = os.path.join(rocrate_path, constants.RO_CRATE_METADATA_FILE)
        else:
            rocrate_file = rocrate_path

        try:
            with open(rocrate_file, 'r') as f:
                data = json.load(f)
            return data['@id']
        except Exception as e:
            raise CellMapsProvenanceError('Error parsing ' + str(rocrate_file) +
                                          ' ' + str(e))

    def register_rocrate(self, rocrate_path, name='',
                         organization_name='', project_name='',
                         guid=None):
        """
        Creates/registers rocreate in directory specified by **rocrate_path**
        Upon completion a ``ro-crate-metadata.json`` file will be created
        in the directory

        :param rocrate_path:
        :type rocrate_path: str
        :param name:
        :param organization_name:
        :param project_name:
        :return:
        """
        cmd = [self._binary, 'rocrate', 'init',
               '--name', name,
               '--organization-name', organization_name,
               '--project-name', project_name]

        if guid is None:
            guid = str(uuid.uuid4())

        cmd.append('--guid')
        cmd.append(guid)

        exit_code, out_str, err_str = self._run_cmd(cmd, cwd=rocrate_path,
                                                    timeout=30)
        logger.debug('creation of crate stdout: ' + str(out_str))
        logger.debug('creation of crate stdout: ' + str(err_str))
        logger.debug('creation of crate exit code: ' + str(exit_code))
        if exit_code != 0:
            raise CellMapsProvenanceError('Error creating crate: ' +
                                          str(out_str) + ' : ' + str(err_str))

    def register_computation(self, rocrate_path, name='',
                             run_by='', command='',
                             date_created=date.today().strftime('%m-%d-%Y'),
                             description='Must be at least 10 characters', used_software=[],
                             used_dataset=[], generated=[],
                             guid=None):

        """
        Registers computation adding information to
        ``ro-crate-metadata.json`` file stored in **rocrate_path**
        directory.

        :param rocrate_path: Path to existing rocrate directory
        :type rocrate_path: str
        :param name:
        :type name: str
        :param author:
        :type author: str
        :param run_by:
        :type run_by: str
        :param command:
        :type command: str
        :param description:
        :type description: str
        :param used_software: list of `FAIRSCAPE <https://fairscape.github.io>`__ software ids
        :type used_software: list
        :param used_dataset: list of `FAIRSCAPE <https://fairscape.github.io>`__ dataset ids used
                             by this computation
        :type used_dataset: list
        :param generated: list of `FAIRSCAPE <https://fairscape.github.io>`__ dataset ids for datasets
                          generated by this computation
        :type generated: list
        :return:
        """
        cmd = [self._binary, 'rocrate', 'register', 'computation',
               '--name', name,
               '--run-by', run_by,
               '--date-created', date_created,
               '--command', command,
               '--description', description]
        if guid is None:
            guid = str(uuid.uuid4())

        cmd.append('--guid')
        cmd.append(guid)

        if used_software is not None:
            for entry in used_software:
                cmd.append('--used-software')
                cmd.append(entry)
        if used_dataset is not None:
            for entry in used_dataset:
                cmd.append('--used-dataset')
                cmd.append(entry)

        if generated is not None:
            for entry in generated:
                cmd.append('--generated')
                cmd.append(entry)
        cmd.append(rocrate_path)
        exit_code, out_str, err_str = self._run_cmd(cmd,
                                                    timeout=60)
        logger.debug('add dataset exit code: ' + str(exit_code))
        if exit_code != 0:
            raise CellMapsProvenanceError('Error adding dataset: ' +
                                          str(out_str) + ' : ' + str(err_str))

        logger.debug('add data set out_str: ' + str(out_str))
        logger.debug('add data set err_str: ' + str(err_str))
        return out_str

    def register_software(self, rocrate_path, name='unknown',
                          description='Must be at least 10 characters',
                          author='', version='', file_format='', url='',
                          date_modified='01-01-1969',
                          guid=None):
        """
        Registers software by adding information to
        ``ro-crate-metadata.json`` file stored in **rocrate_path**
        directory.

        .. warning::

            `fairscape-cli <https://github.com/fairscape>`__ 0.1.5 always fails this call
            `See Issue #7 <https://github.com/fairscape/fairscape-cli/issues/7>`__

        :param name: Name of software
        :type name: str
        :param description: Description of software
        :type description: str
        :param author: Author(s) of software
        :type author: str
        :param version: Version of software
        :type version: str
        :param file_format: Format of software file(s)
        :type file_format: str
        :param url: URL to repository for software
        :type url: str
        :param rocrate_path: Path to directory with registered rocrate
        :type rocrate_path: str
        :raises CellMapsProvenanceError: If `FAIRSCAPE <https://fairscape.github.io>`__ call fails
        :return: guid of software from `FAIRSCAPE <https://fairscape.github.io>`__
        :rtype: str
        """
        cmd = [self._binary, 'rocrate', 'register', 'software',
               '--name', name,
               '--description', description,
               '--author', author,
               '--version', version,
               '--file-format', file_format,
               '--url', url,
               '--date-modified', date_modified]
        if guid is None:
            guid = str(uuid.uuid4())

        cmd.append('--guid')
        cmd.append(guid)

        cmd.append('--filepath')
        cmd.append(url)
        cmd.append(rocrate_path)
        exit_code, out_str, err_str = self._run_cmd(cmd, timeout=30)

        logger.debug('add software exit code: ' + str(exit_code))
        if exit_code != 0:
            raise CellMapsProvenanceError('Error adding software: ' +
                                          str(out_str) + ' : ' + str(err_str))
        logger.debug('add software out_str: ' + str(out_str))
        logger.debug('add software err_str: ' + str(err_str))
        return out_str

    def register_dataset(self, rocrate_path, data_dict=None,
                         source_file=None, skip_copy=True,
                         guid=None):
        """
        Adds a dataset to existing rocrate specified by **rocrate_path**
        by adding information to ``ro-crate-metadata.json`` file

        Information about dataset should be specified in the **data_dict**
        dict passed in.

        Expected format of **data_dict**:

        .. code-block::

            {'name': 'Name of dataset',
             'author': 'Author of dataset',
             'version': 'Version of dataset',
             'date-published': 'Date dataset was published MM-DD-YYYY',
             'description': 'Description of dataset',
             'data-format': 'Format of data'}

        .. warning::

            `fairscape-cli <https://github.com/fairscape>`__ 0.1.5 fails when
            skipping copy is ``True`` or if performing copy where
            **source_file** is already in **rocrate_path** directory.
            `See Issue #6 <https://github.com/fairscape/fairscape-cli/issues/6>`__


        :param rocrate_path: Path to directory with registered rocrate
        :type rocrate_path: str
        :param data_dict: Information about dataset to add. See above
                          for expected data
        :type data_dict: dict
        :param source_file: Path to source file of dataset
        :type source_file: str
        :param skip_copy: If ``True`` skip the copy of source file into
                          **crate_path**. Use this when source file already
                          resides in **crate_path**
        :return: id of dataset from `FAIRSCAPE <https://fairscape.github.io>`__
        :rtype: str
        """
        operation_name = 'register'
        if skip_copy is not None and skip_copy is False:
            operation_name = 'add'

        cmd = [self._binary, 'rocrate', operation_name,
               'dataset',
               '--name', data_dict['name'],
               '--version', data_dict['version'],
               '--data-format', data_dict['data-format'],
               '--description', data_dict['description'],
               '--date-published', data_dict['date-published'],
               '--author', data_dict['author']]

        if guid is None:
            guid = str(uuid.uuid4())

        cmd.append('--guid')
        cmd.append(guid)

        if skip_copy is not None and skip_copy is False:
            cmd.append('--source-filepath')
            cmd.append(source_file)
            cmd.append('--destination-filepath')
            cmd.append(os.path.join(rocrate_path,
                                    os.path.basename(source_file)))
        else:
            cmd.append('--filepath')
            cmd.append(source_file)

        cmd.append(rocrate_path)
        exit_code, out_str, err_str = self._run_cmd(cmd, timeout=30)
        logger.debug(operation_name + ' dataset exit code: ' + str(exit_code))
        if exit_code != 0:
            raise CellMapsProvenanceError('Error adding dataset: ' +
                                          str(out_str) + ' : ' + str(err_str))
        logger.debug(operation_name + ' data set out_str: ' + str(out_str))
        logger.debug(operation_name + ' data set err_str: ' + str(err_str))
        return out_str
