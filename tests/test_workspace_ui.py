"""M2.3 real-browser workspace UI test against a live loopback server and a
local fixture repository (no network). Skips when Playwright is unavailable."""
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tests'))

from app.repositories import RepositoryAcquisitionError, _acquire_repository_for_test  # noqa: E402
from app.server import WorkspaceServer  # noqa: E402
from test_workspace_snapshot import repository  # noqa: E402

NODE = shutil.which('node')
PLAYWRIGHT = os.environ.get('PLAYWRIGHT_DIR', '/Users/aibert/projects/quest-coder-assist/node_modules/playwright')
URL = 'https://github.com/example/ui-fixture'
MISSING = 'https://github.com/example/does-not-exist'
FILES = {
    'app/__init__.py': '', 'lib/__init__.py': '', 'tools/__init__.py': '',
    'app/main.py': 'from lib import core\nfrom app import helpers\n',
    'app/helpers.py': 'X = 1\n',
    'lib/helpers.py': 'Y = 1\n',
    'lib/core.py': 'from lib import util\n',
    'lib/util.py': 'Z = 1\n',
    'tools/cli.py': 'from lib import core\n',
    'lib/x onerror=globalThis.__dagInjected=1 &amp;.py': 'W = 1\n',
    'README.md': '# fixture\n',
}


@unittest.skipUnless(NODE and Path(PLAYWRIGHT).exists(), 'node + Playwright required for the browser smoke')
class WorkspaceUiTests(unittest.TestCase):
    def test_real_browser_import_ask_highlight_choose_clear_select_and_recover(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            repo, _ = repository(root / 'fixture', FILES)

            def acquire(url, cache_root, commit=None, *, progress=None, cancel=None):
                if url != URL:
                    raise RepositoryAcquisitionError('Repository is unavailable, private or empty')
                return _acquire_repository_for_test(url, cache_root, str(repo), commit, progress=progress, cancel=cancel)

            server = WorkspaceServer(root / 'workspace', port=0, acquire=acquire)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            out = Path(os.environ.get('DAG_GPS_UI_SMOKE_OUT', str(root / 'smoke')))
            try:
                done = subprocess.run([NODE, str(ROOT / 'scripts/smoke_workspace.cjs'), server.url, URL, MISSING, str(out)],
                                      capture_output=True, text=True, timeout=300, cwd=str(ROOT))
            finally:
                server.shutdown()
            self.assertEqual(0, done.returncode, done.stdout[-3000:] + done.stderr[-3000:])
            self.assertIn('"ok":true', done.stdout)


if __name__ == '__main__':
    unittest.main()
