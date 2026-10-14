"""Manual strict contract audit of measured folder packets and HTTP budgets."""
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.contracts import validate_snapshot, validate_evidence_packet_against
out = ROOT / 'artifacts/folder-tree'
for repo in ['honcho', 'salesroom']:
    snapshot = json.loads((out / repo / 'snapshot.json').read_text())
    index = validate_snapshot(snapshot)
    packets = json.loads((out / repo / 'folder-packets.json').read_text())
    for packet in packets:
        validate_evidence_packet_against(packet, index)
    print(repo, len(packets), 'folder packets validated')
