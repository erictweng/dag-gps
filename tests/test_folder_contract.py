import copy
import unittest
from app.contracts import ContractError, validate_snapshot, validate_evidence_packet
from scripts.onboarding import group_files, folder_tree
from test_workspace_contract import fixture


def tree_fixture():
    snapshot, packet = fixture()
    paths = ['src/lib/a.py', 'src/lib/b.py', 'src/c.py', 'tests/test.py']
    groups = group_files(paths)
    groups += folder_tree(groups)
    layers = {p: g['id'] for g in groups for p in g['files']}
    snapshot['inventory'] = [{'path': p, 'sha256': 'a' * 64, 'lineCount': 3} for p in paths]
    snapshot['map'].update(nodes=[dict(g, kind='layer') for g in groups] +
        [dict(id=p, path=p, kind='file', layer=layers[p]) for p in paths],
        edges=[], file_edges=[dict(from_='unused')])
    snapshot['map']['file_edges'] = [{'from': paths[-1], 'to': paths[0], 'type': 'import'}]
    snapshot['map']['meta']['folderTree'] = 1
    return snapshot, packet


class FolderContractTests(unittest.TestCase):
    def test_index_and_legacy(self):
        validate_snapshot(fixture()[0])
        snapshot, _ = tree_fixture()
        index = validate_snapshot(snapshot)
        by_label = {n['label']: n['id'] for n in snapshot['map']['nodes'] if n['kind'] == 'layer'}
        src, lib = by_label['src'], by_label['src/lib']
        self.assertEqual(set(index['descendantFiles'][src]), {'src/lib/a.py', 'src/lib/b.py', 'src/c.py'})
        self.assertEqual(index['children'][src], [lib])
        self.assertEqual(index['ancestors'][lib], [src])
        self.assertEqual(index['ancestors']['src/lib/a.py'], [lib, src])

    def test_tampering_rejected(self):
        for change in ['missing', 'file', 'cycle', 'depth', 'fake', 'ownership', 'compact', 'flag']:
            with self.subTest(change=change):
                snapshot, _ = tree_fixture()
                layers = {n['label']: n for n in snapshot['map']['nodes'] if n['kind'] == 'layer'}
                src, lib = layers['src'], layers['src/lib']
                if change == 'missing': lib['parent'] = 'absent'
                if change == 'file': lib['parent'] = 'src/c.py'
                if change == 'cycle': src['parent'] = lib['id']
                if change == 'depth': lib['depth'] = True
                if change == 'fake': lib['label'] = 'src/fake'
                if change == 'ownership': snapshot['map']['nodes'][-4]['layer'] = src['id']
                if change == 'compact': src['compactLabel'] = 'tests'
                if change == 'flag': snapshot['map']['meta']['folderTree'] = True
                with self.assertRaises(ContractError): validate_snapshot(snapshot)

    def test_folder_impact_witness_ends_at_real_descendant(self):
        snapshot, packet = tree_fixture()
        src = next(n['id'] for n in snapshot['map']['nodes'] if n.get('label') == 'src')
        edge = snapshot['map']['file_edges'][0]
        packet.update(operation='DOWNSTREAM', highlightState='potential-impact', seedNodeId=src,
                      selectedNodeIds=[src, 'tests/test.py'], selectedEdges=[], sourceRefs=[],
                      witnesses=[{'nodeIds': ['tests/test.py', 'src/lib/a.py'], 'edges': [edge]}])
        validate_evidence_packet(packet, snapshot)
        packet['selectedNodeIds'].append('src/lib/b.py')
        with self.assertRaises(ContractError): validate_evidence_packet(packet, snapshot)
