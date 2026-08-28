import importlib.machinery
import importlib.util
import os
import pathlib
import stat
import tempfile
import unittest
from unittest import mock


GMMAIL = pathlib.Path(__file__).parents[1] / "skills" / "gmail-imap" / "gmmail"


def load_gmmail():
    loader = importlib.machinery.SourceFileLoader("gmmail_test", str(GMMAIL))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


class LinuxCredentialFileTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = pathlib.Path(self.temp.name)
        self.env = mock.patch.dict(os.environ, {
            "HOME": str(root),
            "XDG_CONFIG_HOME": str(root / "config"),
            "GMMAIL_DATA": str(root / "data"),
        }, clear=True)
        self.env.start()
        self.gmmail = load_gmmail()

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

    def test_save_and_load_credentials(self):
        self.gmmail.save_file_credentials("person@gmail.com", "abcdefghijklmnop")

        path = pathlib.Path(self.gmmail.CREDENTIALS_PATH)
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(path.parent.stat().st_mode), 0o700)
        self.assertEqual(self.gmmail.account(), "person@gmail.com")
        self.assertEqual(self.gmmail.get_password(), "abcdefghijklmnop")

    def test_environment_password_takes_precedence(self):
        self.gmmail.save_file_credentials("person@gmail.com", "file-password")
        os.environ["GMMAIL_ACCOUNT"] = "person@gmail.com"
        os.environ["GMMAIL_PASSWORD"] = "environment-password"

        self.assertEqual(self.gmmail.get_password(), "environment-password")

    def test_refuses_world_readable_credentials(self):
        self.gmmail.save_file_credentials("person@gmail.com", "abcdefghijklmnop")
        os.chmod(self.gmmail.CREDENTIALS_PATH, 0o644)

        with self.assertRaises(SystemExit):
            self.gmmail.load_file_credentials()


if __name__ == "__main__":
    unittest.main()
