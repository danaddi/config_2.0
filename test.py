import unittest
from unittest.mock import patch, mock_open, MagicMock
import zipfile
from io import BytesIO
import requests

from main import download_file, get_dependencies


class TestNugetFunctions(unittest.TestCase):

    @patch('requests.get')
    @patch('builtins.open', new_callable=mock_open)
    def test_download_file(self, mock_file, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = b'dummy content'

        download_file('http://example.com/file.nupkg', 'file.nupkg')

        mock_file.assert_called_with('file.nupkg', 'wb')
        mock_file().write.assert_called_once_with(b'dummy content')

    @patch('zipfile.ZipFile')
    def test_get_dependencies(self, mock_zipfile):
        # Mock .nuspec file content
        nuspec_content = b"""
        <package>
            <metadata>
                <dependencies>
                    <dependency id=\"Newtonsoft.Json.Bson\" version=\"1.0.3\" />
                </dependencies>
            </metadata>
        </package>
        """

        mock_zip_instance = MagicMock()
        mock_zipfile.return_value.__enter__.return_value = mock_zip_instance

        mock_zip_instance.namelist.return_value = ['test.nuspec']
        mock_zip_instance.open.return_value.__enter__.return_value.read.return_value = nuspec_content

        result = get_dependencies('file.nupkg')
        self.assertIn('Newtonsoft.Json.Bson', result)
        self.assertEqual(result['Newtonsoft.Json.Bson'], '1.0.3')

    @patch('zipfile.ZipFile')
    def test_get_dependencies_no_nuspec(self, mock_zipfile):
        mock_zip_instance = MagicMock()
        mock_zipfile.return_value.__enter__.return_value = mock_zip_instance

        mock_zip_instance.namelist.return_value = []  # No .nuspec file

        result = get_dependencies('file.nupkg')
        self.assertEqual(result, {})

    @patch('zipfile.ZipFile')
    def test_get_dependencies_invalid_zip(self, mock_zipfile):
        mock_zipfile.side_effect = zipfile.BadZipFile

        result = get_dependencies('file.nupkg')
        self.assertEqual(result, {})

if __name__ == '__main__':
    unittest.main()
