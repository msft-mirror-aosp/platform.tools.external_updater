import unittest

import updater_utils


class GetLatestVersionTest(unittest.TestCase):
    """Tests for updater_utils.get_latest_stable_release_tag.

    We don't care which branch a tag belongs to because we look for the latest
    tag in a list of all references of a remote repository.
    """
    def test_float_sort(self) -> None:
        """ Tests if updater_utils.get_latest_stable_release_tag return the latest tag.

        This is the most common case where tags are in lexicographical order.
        """
        self.assertEqual(
            updater_utils.get_latest_stable_release_tag("v1.0.0", ["v1.0.0", "v2.0.0"]), "v2.0.0")
        self.assertEqual(
            updater_utils.get_latest_stable_release_tag("1.10", ["1.10", "1.2"]), "1.10")

    def test_mixed_tag(self) -> None:
        self.assertEqual(
            updater_utils.get_latest_stable_release_tag("1.0", ["1.0", "foobar"]), "1.0")
        self.assertEqual(
            updater_utils.get_latest_stable_release_tag("1.0", ["1.0", "v1.1"]), "1.0")
        self.assertEqual(
            updater_utils.get_latest_stable_release_tag("v1.0", ["v1.0", "1.1"]), "v1.0")
        self.assertEqual(
            updater_utils.get_latest_stable_release_tag("1.0", ["1.0", "v1.0"]), "1.0")
        self.assertEqual(
            updater_utils.get_latest_stable_release_tag("v3.11.4", ["v3.11.4", "v3.12.2", "v3.13.0a4"]), "v3.12.2")

    def test_non_release_prefix(self) -> None:
        self.assertEqual(
            updater_utils.get_latest_stable_release_tag("v32.1.3", ["v32.1.3", "v33.0.0", "failureaccess-v1.0.2"]), "v33.0.0")
        self.assertEqual(
            updater_utils.get_latest_stable_release_tag("1.0", ["1.0", "test-1.1 "]), "1.0")

    def test_reject_rc_tags(self) -> None:
        self.assertEqual(
            updater_utils.get_latest_stable_release_tag("v3.27.0", ["v3.27.0", "v3.28.0-rc1"]), "v3.27.0")

    def test_ndk_scheme(self) -> None:
        self.assertEqual(
            updater_utils.get_latest_stable_release_tag("r26", ["r26", "r27"]), "r27")
        self.assertEqual(
            updater_utils.get_latest_stable_release_tag("r26", ["r26", "r26-beta1"]), "r26")
        self.assertEqual(
            updater_utils.get_latest_stable_release_tag("r26", ["r26", "r27-beta1"]), "r26")

    @unittest.expectedFailure
    def test_ndk_scheme_fail(self) -> None:
        # The actual latest tag is r26b but since r26b doesn't match the pattern
        # of current tag, get_latest_stable_release_tag returns r26. Although
        # get_latest_stable_release_tag doesn't return the answer we are looking
        # for, we're going to keep this test case anyway.
        self.assertEqual(
            updater_utils.get_latest_stable_release_tag("r26", ["r26", "r26b"]), "r26b")


if __name__ == "__main__":
    unittest.main(verbosity=2)
