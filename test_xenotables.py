
import unittest
from xenotables import XenoTable

class TestXenoTable(unittest.TestCase):
    def test_connection_error_handling(self):
        with self.assertRaises(ConnectionError):
            # Attempt to create a XenoTable instance with an invalid IP and port
            XenoTable(ip='192.0.2.0', port=9999)

if __name__ == '__main__':
    unittest.main()
