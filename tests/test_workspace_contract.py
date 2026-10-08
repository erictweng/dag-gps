"""Phase 0 synthetic contract regressions, NOT real repo/agent evidence."""
import copy
import unittest
from unittest import mock

from app.contracts import (ContractError, MAX_PACKET_BYTES, default_controls,
                           require_agent_consent, validate_evidence_packet,
                           validate_snapshot)


def fixture():
    a = {'from': 'a.py', 'to': 'b.py', 'type': 'import'}
    snapshot = {
        'schema': 'dag-gps-workspace/v1', 'projectId': 'synthetic-unit',
        'snapshotId': 'synthetic-revision-a', 'mapSha256': 'c' * 64,
        'scorerSha256': 'd' * 64, 'syntheticUnitFixture': True,
        'source': {'kind': 'git-commit', 'repo': 'synthetic/unit', 'commit': 'a' * 40,
                   'worktreeId': None, 'manifestSha256': 'e' * 64},
        'state': 'dependency-preview', 'grouping': {'status': 'proposed', 'reviewed': False},
        'inventory': [{'path': 'a.py', 'sha256': 'a' * 64, 'lineCount': 3},
                      {'path': 'b.py', 'sha256': 'b' * 64, 'lineCount': 5}],
        'map': {'meta': {'repo': 'synthetic/unit', 'snapshot_commit': 'a' * 40}, 'nodes': [{'id': 'folder-root', 'kind': 'layer'},
                         {'id': 'a.py', 'kind': 'file', 'path': 'a.py', 'layer': 'folder-root'},
                         {'id': 'b.py', 'kind': 'file', 'path': 'b.py', 'layer': 'folder-root'}],
                'edges': [], 'file_edges': [a, {'from': 'b.py', 'to': 'a.py', 'type': 'import'}]}}
    packet = {
        'schema': 'dag-gps-evidence/v1', 'requestId': 'synthetic-request',
        'projectId': snapshot['projectId'], 'snapshotId': snapshot['snapshotId'],
        'mapSha256': snapshot['mapSha256'], 'scorerSha256': snapshot['scorerSha256'], 'manifestSha256': snapshot['source']['manifestSha256'],
        'operation': 'UPSTREAM', 'status': 'matched', 'highlightState': 'relevant',
        'selectedNodeIds': ['a.py', 'b.py'], 'selectedEdges': [copy.deepcopy(a)],
        'witnesses': [{'nodeIds': ['a.py', 'b.py'], 'edges': [copy.deepcopy(a)]}],
        'alternatives': [], 'sourceRefs': [{'path': 'a.py', 'snapshotId': snapshot['snapshotId'],
            'sha256': 'a' * 64, 'start': 1, 'end': 2, 'evidenceKind': 'observed-source'}],
        'truncated': False, 'continuation': None, 'limitations': ['Synthetic unit fixture only']}
    return snapshot, packet


class WorkspaceContractTests(unittest.TestCase):
    def setUp(self):
        self.snapshot, self.packet = fixture()

    def reject_packet(self):
        with self.assertRaises(ContractError):
            validate_evidence_packet(self.packet, self.snapshot)

    def reject_snapshot(self):
        with self.assertRaises(ContractError):
            validate_snapshot(self.snapshot)

    def test_valid_source_bound_packet_is_pure_and_cycles_are_retained(self):
        before = copy.deepcopy((self.snapshot, self.packet))
        with mock.patch('builtins.open', side_effect=AssertionError('No contract IO')):
            self.assertIs(validate_evidence_packet(self.packet, self.snapshot), self.packet)
        self.assertEqual((self.snapshot, self.packet), before)
        self.assertEqual(len(validate_snapshot(self.snapshot)['edges']), 2)

    def test_project_snapshot_map_and_scorer_drift_rejected(self):
        for field in ['projectId', 'snapshotId', 'mapSha256', 'scorerSha256']:
            with self.subTest(field=field):
                original = self.packet[field]
                self.packet[field] = 'wrong'
                self.reject_packet()
                self.packet[field] = original

    def test_source_manifest_drift_rejected_even_if_revision_id_is_reused(self):
        self.snapshot['source']['manifestSha256'] = 'f' * 64
        self.reject_packet()

    def test_source_revision_and_file_hash_drift_rejected(self):
        for field in ['snapshotId', 'sha256']:
            with self.subTest(field=field):
                original = self.packet['sourceRefs'][0][field]
                self.packet['sourceRefs'][0][field] = 'wrong'
                self.reject_packet()
                self.packet['sourceRefs'][0][field] = original

    def test_old_schemas_rejected(self):
        self.packet['schema'] = 'old'
        self.reject_packet()
        self.snapshot['schema'] = 'old'
        self.reject_snapshot()

    def test_duplicate_and_unknown_nodes_rejected(self):
        for ids in [['a.py', 'a.py'], ['unknown.py']]:
            self.packet['selectedNodeIds'] = ids
            self.reject_packet()

    def test_old_map_cannot_be_wrapped_as_new_source(self):
        self.snapshot['map']['meta']['snapshot_commit'] = 'b' * 40
        self.reject_snapshot()

    def test_file_owner_must_exist_as_a_layer(self):
        self.snapshot['map']['nodes'][1]['layer'] = 'absent'
        self.reject_snapshot()
        self.snapshot['map']['nodes'][1]['layer'] = 'b.py'
        self.reject_snapshot()

    def test_duplicate_snapshot_nodes_rejected(self):
        self.snapshot['map']['nodes'].append(copy.deepcopy(self.snapshot['map']['nodes'][1]))
        self.reject_snapshot()

    def test_unknown_and_mixed_kind_graph_edges_rejected(self):
        for target in ['unknown', 'folder-root']:
            self.snapshot['map']['file_edges'][0]['to'] = target
            self.reject_snapshot()

    def test_duplicate_graph_edges_rejected(self):
        self.snapshot['map']['file_edges'].append(copy.deepcopy(self.snapshot['map']['file_edges'][0]))
        self.reject_snapshot()

    def test_file_graph_edges_cannot_be_layer_edges(self):
        self.snapshot['map']['edges'] = [self.snapshot['map']['file_edges'].pop()]
        self.reject_snapshot()

    def test_generic_nodes_cannot_masquerade_as_code_nodes(self):
        self.snapshot['map']['nodes'][0]['kind'] = 'generic'
        self.reject_snapshot()

    def test_file_node_requires_inventory(self):
        self.snapshot['inventory'].pop()
        self.reject_snapshot()

    def test_duplicate_inventory_rejected(self):
        self.snapshot['inventory'].append(copy.deepcopy(self.snapshot['inventory'][0]))
        self.reject_snapshot()

    def test_paths_are_literal_safe_and_not_silently_normalized(self):
        for path in ['/etc/passwd', '../a.py', 'folder/../a.py', 'folder//a.py', 'C:/a.py', 'folder\\a.py']:
            with self.subTest(path=path):
                self.packet['sourceRefs'][0]['path'] = path
                self.reject_packet()

    def test_unknown_source_rejected(self):
        self.packet['sourceRefs'][0]['path'] = 'absent.py'
        self.reject_packet()

    def test_unknown_ranges_are_explicit_null(self):
        ref = self.packet['sourceRefs'][0]
        ref['start'] = ref['end'] = None
        validate_evidence_packet(self.packet, self.snapshot)
        ref['start'] = 1
        self.reject_packet()

    def test_ranges_are_inclusive_known_in_bounds_and_not_boolean(self):
        for start, end in [(0, 1), (2, 1), (1, 4), (True, 2)]:
            with self.subTest(start=start, end=end):
                self.packet['sourceRefs'][0].update(start=start, end=end)
                self.reject_packet()

    def test_unknown_line_count_cannot_certify_specific_range(self):
        self.snapshot['inventory'][0]['lineCount'] = None
        self.reject_packet()
        self.packet['sourceRefs'][0].update(start=None, end=None)
        validate_evidence_packet(self.packet, self.snapshot)

    def test_unreviewed_grouping_is_not_validated_architecture(self):
        self.snapshot['state'] = 'validated-map'
        self.reject_snapshot()
        self.snapshot['grouping'] = {'status': 'reviewed', 'reviewed': True}
        validate_snapshot(self.snapshot)

    def test_review_marker_cannot_contradict_status(self):
        self.snapshot['grouping']['reviewed'] = True
        self.reject_snapshot()

    def test_short_commit_and_worktree_cannot_claim_exact_commit(self):
        self.snapshot['source']['commit'] = 'a' * 7
        self.reject_snapshot()
        self.snapshot['source']['commit'] = 'a' * 40
        self.snapshot['source']['worktreeId'] = 'live'
        self.reject_snapshot()

    def test_live_source_kind_is_reserved_not_implicitly_accepted(self):
        self.snapshot['source']['kind'] = 'worktree'
        self.reject_snapshot()

    def test_wrong_typed_enum_fields_fail_with_contract_error(self):
        for field in ['status', 'operation', 'highlightState']:
            with self.subTest(field=field):
                original = self.packet[field]
                self.packet[field] = []
                self.reject_packet()
                self.packet[field] = original

    def test_uncertainty_cannot_highlight_a_guessed_route(self):
        for status in ['needs-choice', 'no-match', 'stale']:
            self.packet['status'] = status
            self.reject_packet()

    def test_no_path_does_not_claim_route(self):
        self.packet.update(status='no-path', operation='PATH')
        self.reject_packet()
        self.packet['selectedEdges'] = self.packet['witnesses'] = []
        validate_evidence_packet(self.packet, self.snapshot)

    def test_alternatives_reference_real_ids(self):
        self.packet['alternatives'] = [{'nodeId': 'unknown', 'reason': 'No invented candidate'}]
        self.reject_packet()

    def test_witness_must_be_contiguous_and_not_reversed(self):
        self.packet['witnesses'][0]['edges'][0].update(**{'from': 'b.py', 'to': 'a.py'})
        self.reject_packet()

    def test_selected_edges_need_observed_evidence_not_agent_invention(self):
        self.packet['selectedEdges'][0]['type'] = 'guessed-runtime'
        self.reject_packet()

    def test_realtime_is_not_default_traversal(self):
        realtime = {'from': 'a.py', 'to': 'b.py', 'type': 'realtime'}
        self.snapshot['map']['file_edges'].append(realtime)
        self.packet['selectedEdges'] = [realtime]
        self.reject_packet()

    def test_potential_impact_requires_relationship_witness(self):
        self.packet['highlightState'] = 'potential-impact'
        self.reject_packet()
        self.packet['operation'] = 'IMPACT'
        self.packet['seedNodeId'] = 'b.py'
        validate_evidence_packet(self.packet, self.snapshot)
        self.packet['witnesses'] = []
        self.reject_packet()

    def test_question_match_cannot_claim_actually_changed(self):
        self.packet['highlightState'] = 'changed'
        self.reject_packet()
        self.snapshot['changes'] = {'baselineSnapshotId': 'baseline', 'changedNodeIds': ['a.py']}
        self.packet['baselineSnapshotId'] = 'baseline'
        self.reject_packet()
        self.snapshot['changes']['changedNodeIds'].append('b.py')
        validate_evidence_packet(self.packet, self.snapshot)
        self.snapshot['changes']['baselineSnapshotId'] = None
        self.packet['baselineSnapshotId'] = None
        self.reject_packet()

    def test_limits_and_explicit_truncation(self):
        self.packet['truncated'] = True
        self.reject_packet()
        self.packet['continuation'] = 'opaque-revision-bound-cursor'
        validate_evidence_packet(self.packet, self.snapshot)
        self.packet['truncated'] = False
        self.reject_packet()

    def test_packet_byte_limit_and_nonfinite_json(self):
        self.packet['extra'] = 'x' * (MAX_PACKET_BYTES + 1)
        self.reject_packet()
        self.packet['extra'] = float('nan')
        self.reject_packet()

    def test_selected_limits_reject_not_silently_drop(self):
        self.packet['selectedNodeIds'] = ['a.py'] * 201
        self.reject_packet()

    def test_nullable_range_keys_must_be_present_even_when_null(self):
        for missing in [('start', 'end'), ('start',), ('end',)]:
            with self.subTest(missing=missing):
                self.snapshot, self.packet = fixture()
                ref = self.packet['sourceRefs'][0]
                ref.update(start=None, end=None)
                for field in missing: ref.pop(field)
                self.reject_packet()

    def test_required_nullable_snapshot_and_packet_fields_are_not_implicit(self):
        self.snapshot['source'].pop('worktreeId')
        self.reject_snapshot()
        self.snapshot, self.packet = fixture()
        self.snapshot['inventory'][1].pop('lineCount')
        self.reject_snapshot()
        self.snapshot, self.packet = fixture()
        self.packet.pop('continuation')
        self.reject_packet()

    def isolated_file(self):
        self.snapshot['inventory'].append({'path': 'isolated.py', 'sha256': 'f' * 64, 'lineCount': 1})
        self.snapshot['map']['nodes'].append({'id': 'isolated.py', 'kind': 'file', 'path': 'isolated.py', 'layer': 'folder-root'})

    def test_unrelated_witness_cannot_certify_isolated_impact_selection(self):
        self.isolated_file()
        self.packet.update(operation='IMPACT', highlightState='potential-impact',
                           seedNodeId='isolated.py', selectedNodeIds=['isolated.py'], selectedEdges=[])
        self.reject_packet()

    def test_every_selected_consumer_needs_directed_witness_to_explicit_seed(self):
        self.isolated_file()
        self.packet.update(operation='IMPACT', highlightState='potential-impact', seedNodeId='b.py',
                           selectedNodeIds=['a.py', 'b.py', 'isolated.py'])
        self.reject_packet()

    def test_potential_impact_seed_must_be_present_known_and_selected(self):
        self.packet.update(operation='IMPACT', highlightState='potential-impact')
        self.reject_packet()
        self.packet['seedNodeId'] = 'unknown'
        self.reject_packet()
        self.packet['seedNodeId'] = 'folder-root'
        self.reject_packet()

    def test_snapshot_extras_must_be_finite_json_and_not_circular(self):
        for value in [float('nan'), float('inf'), float('-inf')]:
            with self.subTest(value=value):
                self.snapshot['extra'] = value
                self.reject_snapshot()
                self.reject_packet()
        self.snapshot['extra'] = self.snapshot
        self.reject_snapshot()
        self.reject_packet()

    def test_packet_and_snapshot_metadata_require_json_native_types(self):
        for value in [(1, 2), {1: 'x'}, {1, 2}]:
            with self.subTest(value=value):
                self.snapshot, self.packet = fixture()
                self.snapshot['extra'] = value
                self.reject_snapshot()
                self.snapshot, self.packet = fixture()
                self.packet['extra'] = value
                self.reject_packet()

    def test_finite_shared_json_metadata_is_allowed_but_depth_is_bounded(self):
        shared = {'note': 'same native value used twice'}
        self.snapshot['extra'] = [shared, shared]
        validate_evidence_packet(self.packet, self.snapshot)
        nested = []
        for _ in range(70): nested = [nested]
        self.snapshot['extra'] = nested
        self.reject_snapshot()

    def test_unsupported_can_show_observed_context_but_needs_a_limitation(self):
        self.packet['status'] = 'unsupported'
        validate_evidence_packet(self.packet, self.snapshot)
        self.packet['limitations'] = []
        self.reject_packet()

    def test_query_history_and_agents_default_off_with_fresh_controls(self):
        controls = default_controls()
        self.assertEqual(controls, {'recordQueries': False, 'agentEnabled': False})
        controls['recordQueries'] = True
        self.assertFalse(default_controls()['recordQueries'])

    def test_agent_consent_is_explicit_not_truthy(self):
        with self.assertRaises(PermissionError):
            require_agent_consent(False)
        for value in [1, 'true', None]:
            with self.assertRaises(ContractError):
                require_agent_consent(value)
        require_agent_consent(True)


if __name__ == '__main__':
    unittest.main()
