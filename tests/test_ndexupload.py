import os
import unittest
from unittest.mock import MagicMock

from ndex2.cx2 import CX2Network

from cellmaps_utils.exceptions import CellMapsError
from cellmaps_utils.ndexupload import NDExHierarchyUploader


class TestHierarchyToHiDeFConverter(unittest.TestCase):
    def test_password_in_file(self):
        path = os.path.join(os.path.dirname(__file__), 'data', 'test_password')
        myobj = NDExHierarchyUploader(ndexserver='server', ndexuser='user', ndexpassword=path)
        self.assertEqual(myobj._password, 'password')

    def test_visibility(self):
        myobj = NDExHierarchyUploader(ndexserver='server', ndexuser='user', ndexpassword='password', visibility=True)
        self.assertEqual(myobj._visibility, 'PUBLIC')

    def test_save_network(self):
        net = MagicMock()
        mock_ndex_client = MagicMock()
        mock_ndex_client.save_new_cx2_network.return_value = 'http://some-url.com/uuid12345'
        myobj = NDExHierarchyUploader(ndexserver='server', ndexuser='user', ndexpassword='password')
        myobj._ndexclient = mock_ndex_client
        result = myobj._save_network(net)
        self.assertEqual(result, ("uuid12345", 'http://some-url.com/uuid12345'))

    def test_save_network_uuid_is_none(self):
        net = MagicMock()
        mock_ndex_client = MagicMock()
        mock_ndex_client.save_new_cx2_network.return_value = None
        myobj = NDExHierarchyUploader(ndexserver='server', ndexuser='user', ndexpassword='password')
        myobj._ndexclient = mock_ndex_client

        try:
            result = myobj._save_network(net)
        except CellMapsError as he:
            self.assertTrue('Expected a str, but got this: ' in str(he))

    def test_save_network_ndexclient_exception(self):
        net = MagicMock()
        mock_ndex_client = MagicMock()
        mock_ndex_client.save_new_cx2_network.side_effect = Exception('NDEx throws exception')
        myobj = NDExHierarchyUploader(ndexserver='server', ndexuser='user', ndexpassword='password')
        myobj._ndexclient = mock_ndex_client

        try:
            myobj._save_network(net)
            self.fail('Expected exception')
        except CellMapsError as he:
            self.assertTrue('An error occurred while saving the network to NDEx: ' in str(he))

    def test_update_hcx_annotations(self):
        mock_hierarchy = CX2Network()
        mock_hierarchy._network_attributes = {'HCX::interactionNetworkName': 'mock_name'}
        interactome_id = "test-uuid"
        myobj = NDExHierarchyUploader(ndexserver='server', ndexuser='user', ndexpassword='password')
        updated_hierarchy = myobj._update_hcx_annotations(mock_hierarchy, interactome_id)

        self.assertEqual(updated_hierarchy.get_network_attributes()['HCX::interactionNetworkUUID'], interactome_id)
        self.assertFalse('HCX::interactionNetworkName' in updated_hierarchy.get_network_attributes())
