import os
import time
import uuid

import ndex2
import logging
import copy
from cellmaps_utils import constants

from ndex2.cx2 import RawCX2NetworkFactory, CX2Network
from requests import RequestException

from cellmaps_utils.exceptions import CellMapsError

logger = logging.getLogger(__name__)


class NDExHierarchyUploader(object):
    """
    Base class for uploading hierarchy and its parent network to NDEx.
    """

    def __init__(self, ndexserver, ndexuser, ndexpassword, visibility=None):
        """
        Constructor

        :param ndexserver:
        :type ndexserver: str
        :param ndexuser:
        :type ndexuser: str
        :param ndexpassword:
        :type ndexpassword: str
        :param visibility: If set to ``public``, ``PUBLIC`` or ``True`` sets hierarchy and interactome to
                           publicly visibility on NDEx, otherwise they are left as private
        :type visibility: str or bool
        """
        self._server = ndexserver
        self._user = ndexuser
        if ndexpassword is not None and os.path.isfile(ndexpassword):
            with open(ndexpassword, 'r') as file:
                self._password = file.readline().strip()
        else:
            self._password = ndexpassword
        self._visibility = None
        if visibility is not None:
            if isinstance(visibility, bool):
                if visibility is True:
                    self._visibility = 'PUBLIC'
            elif isinstance(visibility, str):
                if visibility.lower() == 'public':
                    self._visibility = 'PUBLIC'
        self._ndexclient = None
        self._initialize_ndex_client()

    def _initialize_ndex_client(self):
        """
        Creates NDEx client
        :raises CellmapsGenerateHierarchyError: If the NDEx server URL or user credentials are not specified.
        """
        logger.debug('Connecting to NDEx server: ' + str(self._server) +
                     ' with user: ' + str(self._user))
        if self._server is None or self._user is None or self._password is None:
            raise CellMapsError('NDEx server or credentials were not specified. '
                                'NDEx client connection cannot be established.')
        self._ndexclient = ndex2.client.Ndex2(host=self._server,
                                              username=self._user,
                                              password=self._password,
                                              skip_version_check=True)

    def _save_network(self, network, max_retries=3, retry_wait=10):
        """
        This method saves a network to the NDEx server and returns the unique NDEx UUID for the network
        along with its URL. The visibility of the saved network is determined by the variable `self._visibility`.

        :param network: Network to save
        :type network: :py:class:`~ndex2.cx2.CX2Network`
        :return: NDEX UUID of network
        :rtype: str
        """
        logger.debug('Saving network named: ' + str(network.get_name()) +
                     ' to NDEx with visibility set to: ' + str(self._visibility))
        retry_num = 1
        while retry_num <= max_retries:
            try:
                res = self._ndexclient.save_new_cx2_network(network.to_cx2(),
                                                            visibility=self._visibility)
                if not isinstance(res, str):
                    raise CellMapsError('Expected a str, but got this: ' + str(res))

                ndexuuid = res[res.rfind('/') + 1:]

                return ndexuuid, res.replace('v3', 'viewer')
            except RequestException as re:
                if retry_num == max_retries:
                    raise CellMapsError(str(max_retries) + 'attempts to save the network failed.')
                logger.debug(str(re.response.text))
                retry_num += 1
                time.sleep(retry_wait)
            except Exception as e:
                raise CellMapsError('An error occurred while saving the network to NDEx: ' + str(e))

    def get_cytoscape_url(self, ndexurl):
        """
        Generates a Cytoscape URL for a given NDEx network URL.

        :param ndexurl: The URL of the NDEx network.
        :type ndexurl: str
        :return: The URL pointing to the network's view on the Cytoscape platform.
        :rtype: str
        """
        ndexuuid = ndexurl[ndexurl.rfind('/') + 1:]
        network_url = (f"https://{self._server.replace('https://', '').replace('http://', '')}"
                       f"/cytoscape/0/networks/{ndexuuid}")
        return network_url

    def _update_hcx_annotations(self, hierarchy, interactome_id):
        """
        This method updates the given network hierarchy with specific HCX annotations. These annotations
        are associated with the interactome ID and the NDEx server where the interactome resides.

        :param hierarchy: The network hierarchy that needs to be updated with HCX annotations.
        :type hierarchy: `~ndex2.cx2.CX2Network`
        :param interactome_id: The unique ID (UUID) of the interactome that is associated with the hierarchy.
        :type interactome_id: str
        :return: The updated hierarchy with the HCX annotations.
        :rtype: `~ndex2.cx2.CX2Network`
        """
        hierarchy_copy = copy.deepcopy(hierarchy)
        hierarchy_copy.add_network_attribute('HCX::interactionNetworkUUID', str(interactome_id))
        hierarchy_copy.remove_network_attribute('HCX::interactionNetworkName')
        return hierarchy_copy

    def save_hierarchy_and_parent_network(self, hierarchy, parent_ppi):
        """
        Saves both the hierarchy and its parent network to the NDEx server. This method first saves the parent
        network, then updates the hierarchy with HCX annotations based on the parent network's UUID, and
        finally saves the updated hierarchy. It returns the UUIDs and URLs for both the hierarchy and
        the parent network.

        :param hierarchy: The hierarchy network to be saved.
        :type hierarchy: :py:class:`~ndex2.cx2.CX2Network`
        :param parent_ppi: The parent protein-protein interaction network associated with the hierarchy.
        :type parent_ppi: :py:class:`~ndex2.cx2.CX2Network`
        :return: UUIDs and URLs for both the parent network and the hierarchy.
        :rtype: tuple
        """
        parent_url = None
        if isinstance(parent_ppi, CX2Network):
            parent_uuid, parent_url = self._save_network(parent_ppi)
        else:
            try:
                _ = uuid.UUID(parent_ppi, version=4)
                parent_uuid = parent_ppi
            except ValueError:
                raise CellMapsError(f'Invalid UUID format for parent_ppi: {parent_ppi}')

        hierarchy_for_ndex = self._update_hcx_annotations(hierarchy, parent_uuid)
        hierarchy_uuid, hierarchy_url = self._save_network(hierarchy_for_ndex)
        return parent_uuid, parent_url, hierarchy_uuid, hierarchy_url

    def upload_hierarchy_and_parent_network_from_files(self, hier_dir=None, hierarchy_path=None, parent_path=None):
        """
        Uploads hierarchy and parent network to NDEx from CX2 files.
        It first checks if hierarchy_path and parent_path are provided.
        If not provided, it tries to get them from hier_dir directory.
        If none is specified or cannot find hierarchy and parent in hier_dir, it raises an exception.

        :param hier_dir: The directory where the hierarchy and parent network files are located.
        :type hier_dir: str
        :param hierarchy_path: The path to the hierarchy network file.
        :type hierarchy_path: str, optional
        :param parent_path: The path to the parent network file.
        :type parent_path: str, optional
        :return: UUIDs and URLs for both the hierarchy and parent network.
        :rtype: tuple
        :raises CellMapsError: If the required hierarchy or parent network files do not exist.
        """
        if not hierarchy_path and hier_dir:
            hierarchy_path = os.path.join(hier_dir, constants.HIERARCHY_NETWORK_PREFIX + constants.CX2_SUFFIX)
        if not parent_path and hier_dir:
            parent_path = os.path.join(hier_dir, constants.HIERARCHY_PARENT_NETWORK_PREFIX + constants.CX2_SUFFIX)

        if not hierarchy_path or not os.path.exists(hierarchy_path):
            raise CellMapsError(f'Hierarchy network file does not exist at {hierarchy_path}.')

        if not parent_path or not os.path.exists(parent_path):
            raise CellMapsError(f'Parent network file does not exist at {parent_path}.')

        cx_factory = RawCX2NetworkFactory()
        hierarchy_network = cx_factory.get_cx2network(hierarchy_path)
        parent_network = cx_factory.get_cx2network(parent_path)

        return self.save_hierarchy_and_parent_network(hierarchy_network, parent_network)
