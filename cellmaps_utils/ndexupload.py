import os
import time

import ndex2
import logging
import copy
from cellmaps_utils import constants

from ndex2.cx2 import RawCX2NetworkFactory
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
        parent_uuid, parenturl = self._save_network(parent_ppi)
        hierarchy_for_ndex = self._update_hcx_annotations(hierarchy, parent_uuid)
        hierarchy_uuid, hierarchyurl = self._save_network(hierarchy_for_ndex)
        return parent_uuid, parenturl, hierarchy_uuid, hierarchyurl

    def upload_hierary_and_parent_network_from_files(self, outdir):
        """
        Uploads hierarchy and parent network to NDEx from CX2 files located in a specified directory.
        It first checks the existence of the hierarchy and parent network files, then loads them into
        network objects, and finally saves them to NDEx using `save_hierarchy_and_parent_network` method.

        :param outdir: The directory where the hierarchy and parent network files are located.
        :type outdir: str
        :return: UUIDs and URLs for both the hierarchy and parent network.
        :rtype: tuple
        :raises CellmapsGenerateHierarchyError: If the required hierarchy or parent network files do not exist
                                                in the directory.
        """
        hierarchy_path = os.path.join(outdir, constants.HIERARCHY_NETWORK_PREFIX + constants.CX2_SUFFIX)
        parent_network_path = os.path.join(outdir, 'hierarchy_parent' + constants.CX2_SUFFIX)

        if not os.path.exists(hierarchy_path) or not os.path.exists(parent_network_path):
            raise CellMapsError(f'Hierarchy or parent network file does not exist in dir {outdir}.')

        cx_factory = RawCX2NetworkFactory()
        hierarchy_network = cx_factory.get_cx2network(hierarchy_path)
        parent_network = cx_factory.get_cx2network(parent_network_path)

        return self.save_hierarchy_and_parent_network(hierarchy_network, parent_network)
