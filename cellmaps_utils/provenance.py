import copy
import os
import sys
import subprocess
from pathlib import Path
import logging
import uuid
import getpass
from datetime import date
import json

try:
    from fairscape_cli.models.computation import GenerateComputation
    from fairscape_cli.models.dataset import GenerateDataset
    from fairscape_cli.models.software import GenerateSoftware
    from fairscape_cli.models.rocrate import (
        GenerateROCrate,
        ReadROCrateMetadata,
        AppendCrate
    )
    FAIRSCAPE_LOADED = True
except ImportError as ie:
    FAIRSCAPE_LOADED = False
    logger.debug('Unable to import fairscape_cli. Relying on fairscape_cli command line' + str(ie))


from cellmaps_utils import constants
from cellmaps_utils.exceptions import CellMapsProvenanceError

logger = logging.getLogger(__name__)


class ROCrateProvenanceAttributes(object):
    """
    Wrapper object to hold subset of
    `RO-Crate <https://www.researchobject.org/ro-crate/>`__ provenance attributes
    """

    def __init__(self, name='Please enter a name',
                 organization_name='Please enter an organization',
                 project_name='Please enter a project',
                 description='Please enter a description',
                 keywords=['']):
        """
        Constructor

        :param name: name for `RO-Crate <https://www.researchobject.org/ro-crate/>`__
        :type name: str
        :param organization_name: what lab or group
        :type organization_name: str
        :param project_name: usually funding source
        :type project_name: str
        :param description: describes `RO-Crate <https://www.researchobject.org/ro-crate/>`__
        :type description: str
        :param keywords: keywords to identify `RO-Crate <https://www.researchobject.org/ro-crate/>`__
                         usually set with these values
                         in order:
                         `project, data_release_name, cell_line,
                         treatment, name_of_computation`

        :type keywords: list
        """
        self._name = name
        self._organization_name = organization_name
        self._project_name = project_name
        self._description = description
        self._keywords = keywords

    def get_name(self):
        """
        Gets name for `RO-Crate <https://www.researchobject.org/ro-crate/>`__

        :return: name for `RO-Crate <https://www.researchobject.org/ro-crate/>`__
        :rtype: str
        """
        return self._name

    def get_organization_name(self):
        """
        Gets organization name for `RO-Crate <https://www.researchobject.org/ro-crate/>`__

        :return: organization name
        :rtype: str
        """
        return self._organization_name

    def get_project_name(self):
        """
        Gets project name for `RO-Crate <https://www.researchobject.org/ro-crate/>`__

        :return: project name
        :rtype: str
        """
        return self._project_name

    def get_description(self):
        """
        Gets description for `RO-Crate <https://www.researchobject.org/ro-crate/>`__

        :return: description
        :rtype: str
        """
        return self._description

    def get_keywords(self):
        """
        Gets keywords for `RO-Crate <https://www.researchobject.org/ro-crate/>`__

        :return: keywords
        :rtype: list
        """
        return self._keywords


class ProvenanceUtil(object):
    """
    Wrapper around `FAIRSCAPE-cli <https://github.com/fairscape/fairscape-cli>`__ calls
    """

    def __init__(self, fairscape_binary='fairscape-cli',
                 default_date_format_str='%Y-%m-%d', raise_on_error=False):
        """
        Constructor

        :param fairscape_binary: `FAIRSCAPE <https://github.com/fairscape/fairscape-cli>`__ command line binary
                                 If no path separators are included in this value
                                 (for example no ``/`` on Linux|mac) this code assumes the full
                                 path to the binary is the same directory where the python
                                 binary executing this script resides. To bypass this
                                 set the value to a full path with ex: ``/tmp/foo.py``
        :type fairscape_binary: str
                :param default_date_format_str: Default date format string
        :type default_date_format_str: str
        :param raise_on_error: Flag to determine if exceptions should be raised on errors
        :type raise_on_error: bool
        """
        self._python = sys.executable
        if os.sep not in fairscape_binary:
            self._binary = os.path.join(os.path.dirname(self._python),
                                        fairscape_binary)
        else:
            self._binary = fairscape_binary

        self._default_date_fmt_str = default_date_format_str
        self._raise_on_error = raise_on_error

    @staticmethod
    def _log_fairscape_error(cmd, exit_code, err,
                             reason='non zero exit code', cwd=None):
        """
        Logs fairscape error to provenance_errors.json file

        :param cmd:
        :type cmd: list
        :param exit_code:
        :type exit_code: int
        :param err: error message encoded
        :type err: str
        :param reason:
        :type reason: str
        :param cwd:
        :type cwd: str
        """
        logger.error('Error occurred, but not raising exception due to '
                     'raise_on_error flag set to False')
        err = str(err).strip()
        log_entry = {
            "cmd": cmd,
            "exit_code": exit_code,
            "reason": reason + " : " + err
        }
        if cwd is None:
            log_file = os.path.join(os.getcwd(), constants.PROVENANCE_ERRORS_FILE)
        else:
            log_file = os.path.join(cwd, constants.PROVENANCE_ERRORS_FILE)

        try:
            if not os.path.exists(log_file):
                with open(log_file, 'w') as file:
                    json.dump([log_entry], file, indent=4)
            else:
                with open(log_file, 'r+') as file:
                    data = json.load(file)
                    data.append(log_entry)
                    file.seek(0)
                    json.dump(data, file, indent=4)
        except Exception as e:
            logger.error('Failed to log provenance error: ' + str(e))
        logger.error('Provenance call failed: ' + json.dumps(log_entry))

    def _run_cmd(self, cmd, cwd=None, timeout=360):
        """
        Runs command as a command line process

        :param cmd: command to run
        :type cmd: list
        :param cwd: current working directory
        :type cwd: str
        :param timeout: timeout in seconds before killing process
        :type timeout: int or float
        :raises CellMapsProvenanceError: If **raise_on_error** passed
                                         into constructor is ``True`` and
                                         process times out before completing
        :return: (return code, standard out, standard error)
        :rtype: tuple
        """
        logger.debug('Running command under ' + str(cwd) +
                     ' path: ' + str(cmd))

        p = subprocess.Popen(cmd, cwd=cwd,
                             text=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)

        try:
            out, err = p.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            logger.warning('Timeout reached. Killing process')
            p.kill()
            out, err = p.communicate()
            if self._raise_on_error:
                raise CellMapsProvenanceError('Process timed out. '
                                              'exit code: ' +
                                              str(p.returncode) +
                                              ' stdout: ' + str(out) +
                                              ' stderr: ' + str(err))
            self._log_fairscape_error(cmd, p.returncode, err, cwd=cwd,
                                      reason='Process timed out.')
        else:
            if not self._raise_on_error and p.returncode != 0:
                self._log_fairscape_error(cmd, p.returncode, err, cwd=cwd)

        # Removing ending new line if value is not None
        if out is not None:
            out = out.rstrip()
        return p.returncode, out, err

    def _get_keywords(self, keywords=None):
        """
        Adds keywords to command

        :param keywords:
        :type keywords: list or str
        :raises CellMapsProvenanceError: if **keywords** is not of type
                                         str or list
        :return: keywords commandline flags
        :rtype: list
        """
        if keywords is None:
            return []
        if isinstance(keywords, str):
            return ['--keywords', keywords]
        if isinstance(keywords, list):
            retlist = []
            for k in keywords:
                retlist.extend(['--keywords', k])
            return retlist
        raise CellMapsProvenanceError('Keywords must be a list or a '
                                      'str, but got: ' + str(type(keywords)))

    def _generate_guid(self, data_type=None,
                       rocrate_path=None):
        """
        Gets unique id by appending a UUID to **data_type** and basename of **rocrate_path**

        :param data_type:
        :type data_type: str
        :param rocrate_path: Path to ro-crate meta data file
        :type rocrate_path: dict
        :return:  unique id with data type and path information appended
        :rtype: str
        """
        if data_type is not None:
            data_type_val = data_type
        else:
            data_type_val = ''

        return str(uuid.uuid4()) + ':' + str(data_type_val) + '::' + os.path.basename(str(rocrate_path))

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

    def get_default_date_format_str(self):
        """
        Gets default date format string set via constructor

        :return: default date format string usually something like %Y-%m-%d
        :rtype: str
        """
        return self._default_date_fmt_str

    def get_login(self):
        """
        Attempts to get login of user

        :return: login of user or empty string if unable to obtain
        :rtype: str
        """
        try:
            return getpass.getuser()
        except Exception as e:
            logger.error('Unable to get login for user: ' + str(e))
        return ''

    def get_rocrate_as_dict(self, rocrate_path):
        """
        Loads `RO-Crate <https://www.researchobject.org/ro-crate/>`__ as a dict

        :param rocrate_path: Directory containing `ro-crate-metadata.json` file or
                             path to file assumed to be ro-crate meta data file
        :type rocrate_path: str
        :raises CellMapsProvenanceError: If **rocrate_path** is ``None`` or
                                         if **raise_on_error** passed
                                         into constructor is ``True`` and
                                         there is an issue parsing the
                                         ro-crate meta data file
        :return: `RO-Crate <https://www.researchobject.org/ro-crate/>`__
        :rtype: dict
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
            return data
        except Exception as e:
            if self._raise_on_error:
                raise CellMapsProvenanceError('Error parsing ' + str(rocrate_file) +
                                              ' ' + str(e))
            return {'@id': None, 'name': '', 'description': '', 'keywords': [''],
                    'isPartOf': [{"@type": "Organization", "name": ""}, {"@type": "Project", "name": ""}]}

    def get_id_of_rocrate(self, rocrate):
        """
        Gets id of `RO-Crate <https://www.researchobject.org/ro-crate/>`__

        :param rocrate: `RO-Crate <https://www.researchobject.org/ro-crate/>`__ :py:class:`dict` or directory containing
                        `ro-crate-metadata.json` file or
                        path to file assumed to be `RO-Crate <https://www.researchobject.org/ro-crate/>`__ meta data
                        file
        :type rocrate: str or dict
        :return:
        """
        if isinstance(rocrate, dict):
            data = rocrate
        else:
            data = self.get_rocrate_as_dict(rocrate)
        return data['@id']

    def get_name_project_org_of_rocrate(self, rocrate):
        """
        Gets name, project, and organization name of `RO-Crate <https://www.researchobject.org/ro-crate/>`__

        :param rocrate: `RO-Crate <https://www.researchobject.org/ro-crate/>`__ :py:class:`dict` or directory containing
                        `ro-crate-metadata.json` file or
                        path to file assumed to be `RO-Crate <https://www.researchobject.org/ro-crate/>`__ meta data
                        file
        :type rocrate: str or dict
        :return: (name, project, organization-name)
        :rtype: tuple
        """
        prov_attrs = self.get_rocrate_provenance_attributes(rocrate)
        return prov_attrs.get_name(), prov_attrs.get_project_name(), prov_attrs.get_organization_name()

    def get_rocrate_provenance_attributes(self, rocrate):
        """
        Gets provenance attributes for an `RO-Crate <https://www.researchobject.org/ro-crate/>`__

        :param rocrate: `RO-Crate <https://www.researchobject.org/ro-crate/>`__ :py:class:`dict` or directory containing
                `ro-crate-metadata.json` file or
                path to file assumed to be `RO-Crate <https://www.researchobject.org/ro-crate/>`__ metadata
                file
        :type rocrate: str or dict
        :return:
        :rtype: :py:class:`~cellmaps_utils.provenance.ROCrateProvenanceAttributes`
        """
        if isinstance(rocrate, dict):
            data = rocrate
        else:
            data = self.get_rocrate_as_dict(rocrate)

        name = data['name']
        description = data['description']
        keywords = data['keywords']
        org_name = None
        proj_name = None
        for entry in data['isPartOf']:
            if '@type' in entry:
                if entry['@type'] == 'Organization':
                    org_name = entry['name']
                elif entry['@type'] == 'Project':
                    proj_name = entry['name']

        return ROCrateProvenanceAttributes(name=name, project_name=proj_name,
                                           organization_name=org_name,
                                           description=description,
                                           keywords=keywords)

    def get_merged_rocrate_provenance_attrs(self, rocrate=None,
                                            override_name=None,
                                            override_project_name=None,
                                            override_organization_name=None,
                                            extra_keywords=None,
                                            keywords_to_preserve=6,
                                            merged_delimiter='|'):
        """
        Creates a merged provenance attributes object when given
        one or more `RO-Crates <https://www.researchobject.org/ro-crate/>`__.
        It does this by the following rules:


        Values for *name*, *project_name*, and *organization_name*
        are put into respective sets for uniqueness sorted alphabetically
        and joined together using value of **merged_delimiter**

        If **override_name, override_project,** or **override_organization**
        is not ``None`` then those values will be used in leiu of the
        merged data mentioned earlier.

        For *keywords*, the first **keywords_to_preserve** elements are put into respective
        sets for uniqueness and joined together using value of **merge_delimiter**
        and put back into a list. Any extra entries in **extra_keywords** is appended
        to this list.

        The *description* is a merging of the keywords list with a space delimiter

        :param rocrate: :py:class:`dict` or directory containing
                        `ro-crate-metadata.json` file or
                        path to file assumed to be `RO-Crate <https://www.researchobject.org/ro-crate/>`__
                        meta data
                        file or a list of either of the previously
                        mentioned items
        :type rocrate: str or dict or list
        :param override_name: If not ``None``, overrides name returned
        :type override_name: str
        :param override_project_name: If not ``None``, overrides project name returned
        :type override_project_name: str
        :param override_organization_name: If not ``None``, overrides organization-name
        :type override_organization_name: str
        :param extra_keywords: Any extra keywords to append
        :type extra_keywords: list or str
        :param keywords_to_preserve: Denotes number of keywords to preserve. A value of 5
                                     means keep the 1st 5. ``None`` means preserve all keywords
        :type keywords_to_preserve: int
        :param merged_delimiter: default is '|'
        :type merged_delimiter: str
        :raises CellMapsProvenanceError: If **rocrate**, **extra_keywords**
        :return: Merged rocrate provenance attributes
        :rtype: :py:class:`~cellmaps_utils.provenance.ROCrateProvenanceAttributes`
        """
        name_set = set()
        proj_set = set()
        org_set = set()
        keyword_set_dict = {}
        new_keywords = []

        if rocrate is None:
            raise CellMapsProvenanceError('rocrate is None')

        if isinstance(rocrate, str) or isinstance(rocrate, dict):
            rocrate_list = [rocrate]
        elif isinstance(rocrate, list):
            if len(rocrate) == 0:
                raise CellMapsProvenanceError('No rocrates in list')
            rocrate_list = rocrate
        else:
            raise CellMapsProvenanceError('rocrate must be type str, list or dict, received: ' + str(type(rocrate)))

        for entry in rocrate_list:
            prov_attrs = self.get_rocrate_provenance_attributes(entry)

            if prov_attrs.get_name() is not None:
                name_set.add(prov_attrs.get_name())
            else:
                logger.error(f'The name for RO-Crate {str(rocrate)} is missing from the metadata. Please '
                             f'provide a name to uphold FAIR principles. Execution will proceed without the  name.')
            if prov_attrs.get_project_name() is not None:
                proj_set.add(prov_attrs.get_project_name())
            else:
                logger.error(f'The project name for RO-Crate {str(rocrate)} is missing from the metadata. Please '
                             f'provide a name to uphold FAIR principles. Execution will proceed without the  name.')
            if prov_attrs.get_organization_name() is not None:
                org_set.add(prov_attrs.get_organization_name())
            else:
                logger.error(f'The organization name for RO-Crate {str(rocrate)} is missing from the metadata. Please '
                             f'provide a name to uphold FAIR principles. Execution will proceed without the  name.')
            if prov_attrs.get_keywords() is not None:
                for index in range(len(prov_attrs.get_keywords())):
                    if index not in keyword_set_dict:
                        keyword_set_dict[index] = set()
                    if prov_attrs.get_keywords()[index] is not None:
                        keyword_set_dict[index].add(prov_attrs.get_keywords()[index])
        logger.debug('keyword_set_dict: ' + str(keyword_set_dict))

        if override_name is None:
            new_name = merged_delimiter.join(sorted(list(name_set)))
        else:
            new_name = override_name

        if override_organization_name is None:
            new_organization_name = merged_delimiter.join(sorted(list(org_set)))
        else:
            new_organization_name = override_organization_name

        if override_project_name is None:
            new_project_name = merged_delimiter.join(sorted(list(proj_set)))
        else:
            new_project_name = override_project_name

        # just grab 1st **keywords_to_preserve** elements assuming they are
        # project, data_release_name, cell line, treatment,
        # name_of_computation
        if keywords_to_preserve is not None and len(keyword_set_dict.keys()) >= keywords_to_preserve:
            for index in range(keywords_to_preserve):
                new_keywords.append(merged_delimiter.join(sorted(list(keyword_set_dict[index]))))
        else:
            for index in range(len(keyword_set_dict.keys())):
                new_keywords.append(merged_delimiter.join(sorted(list(keyword_set_dict[index]))))

        # add names to keywords
        if name_set is not None and len(name_set) > 0:
            new_keywords.extend(list(name_set))

        if extra_keywords is not None:
            if isinstance(extra_keywords, str):
                new_keywords.append(extra_keywords)
            elif isinstance(extra_keywords, list):
                new_keywords.extend(extra_keywords)
            else:
                raise CellMapsProvenanceError('extra_keywords must be of '
                                              'type list or str. '
                                              'Received: ' +
                                              str(type(extra_keywords)))

        new_description = ' '.join(new_keywords)

        split_keywords = set()
        for keyword in new_keywords:
            if merged_delimiter in keyword:
                split_keywords.update(keyword.split(merged_delimiter))
        new_keywords.extend(list(split_keywords))
        return ROCrateProvenanceAttributes(name=new_name, project_name=new_project_name,
                                           organization_name=new_organization_name,
                                           description=new_description,
                                           keywords=new_keywords)

    def register_rocrate(self, rocrate_path, name='',
                         organization_name='', project_name='',
                         description='Please enter a description',
                         keywords=[''],
                         guid=None,
                         timeout=30):

        """
        Creates/registers `RO-Crate <https://www.researchobject.org/ro-crate/>`__
        in directory specified by **rocrate_path**
        Upon completion a ``ro-crate-metadata.json``
        file will be created in the directory

        :param rocrate_path:
        :type rocrate_path: str
        :param name: Name for `RO-Crate <https://www.researchobject.org/ro-crate/>`__
        :type name: str
        :param organization_name: Name of organization
        :type organization_name: str
        :param project_name: Name of project
        :type project_name: str
        :param description: Description
        :type description: str
        :param keywords: keywords
        :type keywords: list
        :param guid: ID for `RO-Crate <https://www.researchobject.org/ro-crate/>`__
        :type guid: str
        :param timeout: Time in seconds to wait for registration of `RO-Crate <https://www.researchobject.org/ro-crate/>`__
                        to complete
        :type timeout: float
        """
        cmd = [self._python, self._binary, 'rocrate', 'init',
               '--name', name,
               '--organization-name', organization_name,
               '--project-name', project_name,
               '--description', description]

        cmd.extend(self._get_keywords(keywords=keywords))
        if guid is None:
            guid = self._generate_guid(data_type='rocrate',
                                       rocrate_path=rocrate_path)

        cmd.append('--guid')
        cmd.append(guid)
        try:
            exit_code, out_str, err_str = self._run_cmd(cmd, cwd=rocrate_path,
                                                        timeout=timeout)
            logger.debug('creation of crate stdout: ' + str(out_str))
            logger.debug('creation of crate stdout: ' + str(err_str))
            logger.debug('creation of crate exit code: ' + str(exit_code))
            if exit_code != 0 and self._raise_on_error:
                raise CellMapsProvenanceError('Error creating crate: ' +
                                              str(out_str) + ' : ' + str(err_str))
        except CellMapsProvenanceError as ce:
            raise ce
        except Exception as e:
            raise CellMapsProvenanceError('Caught Exception: ' + str(e))

    def register_computation(self, rocrate_path, name='',
                             run_by='', command='',
                             date_created=None,
                             description='Must be at least 10 characters', used_software=[],
                             used_dataset=[], generated=[],
                             keywords=[''],
                             guid=None,
                             timeout=60):

        """
        Registers computation adding information to
        ``ro-crate-metadata.json`` file stored in **rocrate_path**
        directory.

        :param rocrate_path: Path to existing `RO-Crate <https://www.researchobject.org/ro-crate/>`__
                             directory
        :type rocrate_path: str
        :param name:
        :type name: str
        :param run_by:
        :type run_by: str
        :param command:
        :type command: str
        :param date_created:
        :type date_created:
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
        :param keywords:
        :type keywords: list
        :param guid: ID for `RO-Crate <https://www.researchobject.org/ro-crate/>`__
        :type guid: str
        :param timeout: Time in seconds to wait for registration of computation to complete
        :type timeout: float
        """
        if date_created is None:
            date_created = date.today().strftime(self._default_date_fmt_str)
        if FAIRSCAPE_LOADED == False:
            return self._register_computation_via_cli(rocrate_path=rocrate_path,
                                                      name=name,
                                                      run_by=run_by,
                                                      date_created=date_created,
                                                      description=description,
                                                      used_software=used_software,
                                                      used_dataset=used_dataset,
                                                      generated=generated,
                                                      keywords=keywords,
                                                      guid=guid,
                                                      timeout=timeout)
        comp_metadata = {
            "guid": guid,  # Made more specific
            "name": name,
            "runBy": run_by,
            "dateCreated": date_created,
            "description": description,
            "keywords": self._get_list_version_of_value(keywords),
            "usedSoftware": self._get_list_version_of_value(used_software),
            "usedDataset": self._get_list_version_of_value(used_dataset),
            "generated": self._get_list_version_of_value(generated)
        }
        if comp_metadata['guid'] is None:
            comp_metadata['guid'] = self._generate_guid(rocrate_path=rocrate_path,
                                                        data_type='computation')
        try:
            AppendCrate(Path(rocrate_path),
                        [GenerateComputation(**comp_metadata)])
            return comp_metadata['guid']
        except Exception as e:
            logger.warning('Received exception trying to register computation. '
                           'Falling back to cli call: ' + str(e))
            return self._register_computation_via_cli(rocrate_path=rocrate_path,
                                                      name=name,
                                                      run_by=run_by,
                                                      date_created=date_created,
                                                      description=description,
                                                      used_software=used_software,
                                                      used_dataset=used_dataset,
                                                      generated=generated,
                                                      keywords=keywords,
                                                      guid=guid,
                                                      timeout=timeout)

    def _register_computation_via_cli(self, rocrate_path, name='',
                                      run_by='', command='',
                                      date_created=None,
                                      description='Must be at least 10 characters',
                                      used_software=[],
                                      used_dataset=[], generated=[],
                                      keywords=[''],
                                      guid=None,
                                      timeout=60):

        """
        Registers computation adding information to
        ``ro-crate-metadata.json`` file stored in **rocrate_path**
        directory.

        :param rocrate_path: Path to existing `RO-Crate <https://www.researchobject.org/ro-crate/>`__
                             directory
        :type rocrate_path: str
        :param name:
        :type name: str
        :param run_by:
        :type run_by: str
        :param command:
        :type command: str
        :param date_created:
        :type date_created:
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
        :param keywords:
        :type keywords: list
        :param guid: ID for `RO-Crate <https://www.researchobject.org/ro-crate/>`__
        :type guid: str
        :param timeout: Time in seconds to wait for registration of computation to complete
        :type timeout: float
        """
        cmd = [self._python, self._binary, 'rocrate', 'register',
               'computation',
               '--name', name,
               '--run-by', run_by,
               '--date-created', date_created,
               '--command', command,
               '--description', description]

        cmd.extend(self._get_keywords(keywords=keywords))

        if guid is None:
            guid = self._generate_guid(data_type='computation',
                                       rocrate_path=rocrate_path)

        cmd.append('--guid')
        cmd.append(guid)

        if used_software is not None:
            for entry in used_software:
                cmd.append('--used-software')
                cmd.append(entry)
        if used_dataset is not None:
            for entry in used_dataset:
                if entry is not None:
                    cmd.append('--used-dataset')
                    cmd.append(entry)

        if generated is not None:
            for entry in generated:
                cmd.append('--generated')
                cmd.append(entry)
        cmd.append(rocrate_path)
        exit_code, out_str, err_str = self._run_cmd(cmd, cwd=rocrate_path,
                                                    timeout=timeout)
        logger.debug('add dataset exit code: ' + str(exit_code))
        if exit_code != 0 and self._raise_on_error:
            raise CellMapsProvenanceError('Error adding dataset:\n' +
                                          str(cmd) + '\nStandard out:\n' +
                                          str(out_str) + '\n Standard err:\n' +
                                          str(err_str))

        logger.debug('add data set out_str: ' + str(out_str))
        logger.debug('add data set err_str: ' + str(err_str))
        return out_str

    def register_software(self, rocrate_path, name='unknown',
                          description='Must be at least 10 characters',
                          author='', version='', file_format='', url='',
                          date_modified=None,
                          keywords=[''],
                          guid=None,
                          timeout=30):

        """
        Registers software by adding information to
        ``ro-crate-metadata.json`` file stored in **rocrate_path**
        directory.

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
        :param date_modified:
        :type date_modified: str
        :param keywords:
        :type keywords: list
        :param guid: ID for `RO-Crate <https://www.researchobject.org/ro-crate/>`__
        :type guid: str
        :param rocrate_path: Path to directory with registered rocrate
        :type rocrate_path: str
        :param timeout: Time in seconds to wait for registration of ro-crate to complete
        :type timeout: float
        :raises CellMapsProvenanceError: If `FAIRSCAPE <https://fairscape.github.io>`__ call fails
        :return: guid of software from `FAIRSCAPE <https://fairscape.github.io>`__
        :rtype: str
        """
        if date_modified is None:
            date_modified = date.today().strftime(self._default_date_fmt_str)
        cmd = [self._python, self._binary, 'rocrate', 'register',
               'software',
               '--name', name,
               '--description', description,
               '--author', author,
               '--version', version,
               '--file-format', file_format,
               '--url', url,
               '--date-modified', date_modified]

        cmd.extend(self._get_keywords(keywords=keywords))

        if guid is None:
            guid = self._generate_guid(data_type='software',
                                       rocrate_path=rocrate_path)

        cmd.append('--guid')
        cmd.append(guid)

        cmd.append('--filepath')
        cmd.append(url)
        cmd.append(rocrate_path)
        exit_code, out_str, err_str = self._run_cmd(cmd, cwd=rocrate_path,
                                                    timeout=timeout)

        logger.debug('add software exit code: ' + str(exit_code))
        if exit_code != 0 and self._raise_on_error:
            raise CellMapsProvenanceError('Error adding software: ' +
                                          str(out_str) + ' : ' + str(err_str))
        logger.debug('add software out_str: ' + str(out_str))
        logger.debug('add software err_str: ' + str(err_str))
        return out_str

    def register_datasets_in_bulk(self, rocrate_path, datasets=None):
        """
        Registers datasets in bulk to existing rocrate specified
        by **rocrate_path** by adding information to
        ``ro-crate-metadata.json`` file.

        TODO: Attempting to use example here:
              https://github.com/fairscape/fairscape-cli/blob/main/tests/test_rocrate_api.py
              for implementation

        .. note::

           Copy is not available in this mode. This method will attempt
           to use fairscape-cli API call for speed, but will fall back
           to command line if API is unavailable.

        Expected format of **datasets**:

        .. code-block::

             [
              {'name': 'Name of dataset',
              'author': 'Author of dataset',
              'version': 'Version of dataset',
              'url': 'Url of dataset (optional)',
              'date-published': 'Date dataset was published MM-DD-YYYY',
              'description': 'Description of dataset',
              'data-format': 'Format of data',
              'associatedPublication': 'Publication',
              'additionalDocumentation': 'Additional documentation',
              'derivedFrom': ['list of ids'],
              'usedBy': ['list of ids'],
              'schema': Path or URL to schema file in JSON format,
              'keywords': ['keyword1','keyword2'],
              'guid': unique id for dataset
                      (set to None or omit to have one generated),
              'source_file': Path to source file of dataset}
             ]

        :param rocrate_path: Path to directory with registered rocrate
        :type rocrate_path: str
        :param datasets: list of dicts representing datasets
                         to register. See above for format of dict
        :type datasets: list
        :return: dataset ids
        :rtype: list
        """
        if rocrate_path is None:
            raise CellMapsProvenanceError('rocrate_path is None')
        if datasets is None:
            raise CellMapsProvenanceError('No datasets to register')
        if FAIRSCAPE_LOADED is False:
            logger.debug('Fairscape-cli unavailable. Falling back to CLI')
            return self._register_datasets_in_bulk_via_cli(rocrate_path,
                                                           datasets=datasets)
        try:
            dset_list = []
            dsets = []
            for entry in datasets:
                dset_meta = {'guid': entry.get('guid'),
                             'name': entry.get('name'),
                             'version': entry.get('version'),
                             'associatedPublication': entry.get('associatedPublication'),
                             'additionalDocumentation': entry.get('additionalDocumentation'),
                             'derivedFrom': self._get_list_version_of_value(entry.get('derivedFrom')),
                             'usedBy': self._get_list_version_of_value(entry.get('usedBy')),
                             'url': entry.get('url'),
                             'keywords': self._get_list_version_of_value(entry.get('keywords')),
                             'description': entry.get('description'),
                             'author': entry.get('author'),
                             'datePublished': entry.get('date-published'),
                             'dataFormat': entry.get('data-format'),
                             'schema': entry.get('schema'),
                             'filepath': entry.get('source_file'),
                             'cratePath': rocrate_path}
                if dset_meta['guid'] is None:
                    dset_meta['guid'] = self._generate_guid(rocrate_path=rocrate_path,
                                                            data_type='dataset')
                dsets.append(dset_meta['guid'])
                dset_list.append(GenerateDataset(**dset_meta))
            AppendCrate(Path(rocrate_path), dset_list)
            return dsets
        except Exception as e:
            logger.warning('Unable to register these datasets in fairscape: ' + str(dsets))
            raise CellMapsProvenanceError('Error registering datasets in bulk via api: ' +
                                          str(e))
            return []


    def _get_list_version_of_value(self, value):
        """
        Some attributes must be a in a list. and this
        :param value:
        :type str or list
        :return:
        :rtype: list
        """
        if value is None:
            return []
        if isinstance(value, list):
            return value
        return [str(value)]

    def _register_datasets_in_bulk_via_cli(self, rocrate_path, datasets=None):
        """

        :param rocrate_path:
        :param datasets:
        :return:
        """
        if not isinstance(datasets, list):
            raise CellMapsProvenanceError('datasets should be a list of dicts,'
                                          ' but got: ' + str(type(datasets)))
        dset_ids = []
        for entry in datasets:
            print(entry)
            data_dict = copy.deepcopy(entry)
            for key in ['guid', 'source_file']:
                if key in data_dict:
                    del data_dict[key]
            guidval = None
            if 'guid' in entry:
                guidval = entry['guidval']
            print(data_dict)
            dset_ids.append(self.register_dataset(rocrate_path=rocrate_path,
                                                  data_dict=data_dict,
                                                  source_file=entry['source_file'],
                                                  skip_copy=True, guid=guidval))
        return dset_ids


    def register_dataset(self, rocrate_path, data_dict=None,
                         source_file=None, skip_copy=True,
                         guid=None, timeout=30):

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
             'url': 'Url of dataset (optional)',
             'date-published': 'Date dataset was published MM-DD-YYYY',
             'description': 'Description of dataset',
             'data-format': 'Format of data',
             'schema': Path or URL to schema file in JSON format
             'keywords': ['keyword1','keyword2']}

        .. versionchanged:: 0.2.0

            Added support for ``schema`` in **data_dict** passed in


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
        :param guid: ID for `RO-Crate <https://www.researchobject.org/ro-crate/>`__
        :type guid: str
        :param timeout: Time in seconds to wait for registration of dataset to complete
        :type timeout: float
        :return: id of dataset from `FAIRSCAPE <https://fairscape.github.io>`__
        :rtype: str
        """
        operation_name = 'register'
        if skip_copy is not None and skip_copy is False:
            operation_name = 'add'

        cmd = [self._python, self._binary, 'rocrate', operation_name,
               'dataset',
               '--name', data_dict.get('name'),
               '--version', data_dict.get('version'),
               '--data-format', data_dict.get('data-format'),
               '--description', data_dict.get('description'),
               '--date-published', data_dict.get('date-published'),
               '--author', data_dict.get('author')]

        if 'url' in data_dict:
            cmd.extend(['--url', data_dict['url']])

        if 'keywords' not in data_dict:
            cmd.extend(self._get_keywords(keywords=''))
        else:
            cmd.extend(self._get_keywords(keywords=data_dict['keywords']))

        if 'schema' in data_dict:
            cmd.extend(['--schema', data_dict['schema']])

        if guid is None:
            guid = self._generate_guid(data_type='dataset',
                                       rocrate_path=rocrate_path)

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
        exit_code, out_str, err_str = self._run_cmd(cmd, cwd=rocrate_path,
                                                    timeout=timeout)
        logger.debug(operation_name + ' dataset exit code: ' + str(exit_code))
        if exit_code != 0 and self._raise_on_error:
            raise CellMapsProvenanceError('Error adding dataset: ' +
                                          str(out_str) + ' : ' + str(err_str))
        logger.debug(operation_name + ' data set out_str: ' + str(out_str))
        logger.debug(operation_name + ' data set err_str: ' + str(err_str))
        return out_str
