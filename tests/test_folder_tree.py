"""Folder-tree plumbing preserves direct ownership and every real path."""
import copy
import unittest
from scripts import onboarding


class FolderTreeTests(unittest.TestCase):
    def test_ancestors_ids_ownership_and_order(self):
        groups = onboarding.group_files(['src/lib/a.py', 'src/components/ui/b.ts', 'main.py'])
        original = copy.deepcopy(groups)
        ancestors = onboarding.folder_tree(groups)
        nodes = {g['label']: g for g in groups + ancestors}
        self.assertEqual(set(nodes), {'(root)', 'src', 'src/lib', 'src/components', 'src/components/ui'})
        self.assertEqual(nodes['src/lib']['parent'], nodes['src']['id'])
        self.assertEqual(nodes['src/components/ui']['depth'], 2)
        self.assertIsNone(nodes['(root)']['parent'])
        self.assertEqual(nodes['(root)']['depth'], 0)
        for before, after in zip(original, groups):
            self.assertEqual(before['id'], after['id'])
            self.assertEqual(before['files'], after['files'])
        self.assertTrue(all(g['files'] == [] for g in ancestors))
        again = onboarding.group_files(['main.py', 'src/components/ui/b.ts', 'src/lib/a.py'])
        self.assertEqual(ancestors, onboarding.folder_tree(again))
        self.assertEqual(groups, again)

    def test_compact_chains_keep_real_nodes_and_stop_at_files(self):
        groups = onboarding.group_files(['examples/crewai/python/src/a.py', 'examples/crewai/python/src/lib/b.py'])
        nodes = {g['label']: g for g in onboarding.folder_tree(groups) + groups}
        self.assertEqual(nodes['examples']['compactLabel'], 'examples/crewai/python/src')
        self.assertEqual(nodes['examples/crewai/python/src']['compactLabel'], 'examples/crewai/python/src')
        self.assertEqual(len(nodes), 5)

    def test_empty(self):
        self.assertEqual(onboarding.folder_tree([]), [])
