"""Tour schema and source validation against real, immutable Git fixture commits."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
import subprocess
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from tours import compile_tours
from render import render, DEFAULT_TEMPLATE, main as render_main
from build_project import build_project, repo_identity

class TourTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.repo = self.root / 'repo'; self.repo.mkdir()
        def git(*args):
            return subprocess.check_output(['git','-C',str(self.repo),*args],text=True).strip()
        self.git = git
        git('init','-q');git('config','user.name','Fixture');git('config','user.email','fixture@example.invalid')
        (self.repo/'a.js').write_text("import './b.js';\nexport const a = '</script><script>alert(1)</script>';\n")
        (self.repo/'b.js').write_text('export const b = 1;\n')
        git('add','.');git('commit','-qm','snapshot');self.sha=git('rev-parse','HEAD')
        self.layers=self.root/'layers.json'
        self.layers.write_text(json.dumps({'layers':[{'id':'core','label':'Core','globs':['*.js']}],'manual_edges':[]}))
        self.out=self.root/'out'
        build_project(self.repo,self.sha,self.layers,self.out)
        self.map=json.loads((self.out/'map.json').read_text())
        e=dict(path='a.js',start=1,end=2,symbol='a')
        s=dict(nodeIds=['a.js'],title='Entry',does='Calls dependency',receives='Input',passes='Output',explanation='Source audit',evidence=[e])
        self.spec=dict(version=1,repo=repo_identity(self.repo),commit=self.sha,tours=[dict(id='entry',title='Entry',overview='Source walkthrough',queries=['tour entry'],steps=[s],links=[])])
    def compile(self): return compile_tours(self.spec,self.map,self.repo)
    def test_real_excerpt_and_worktree_isolation(self):
        (self.repo/'a.js').write_text('MUTABLE WRONG SOURCE')
        got=self.compile()['tours'][0]['steps'][0]['evidence'][0]['excerpt']
        self.assertIn("import './b.js'",got);self.assertNotIn('MUTABLE',got)
    def test_unknown_ids(self):
        self.spec['tours'][0]['steps'][0]['nodeIds']=['ghost']
        with self.assertRaises(ValueError):self.compile()
    def test_missing_evidence(self):
        self.spec['tours'][0]['steps'][0]['evidence']=[]
        with self.assertRaises(ValueError):self.compile()
    def test_bad_line_bounds(self):
        for a,b in [(0,1),(2,1),(1,3),(True,2),(1,1.5)]:
            with self.subTest(a=a,b=b):
                e=self.spec['tours'][0]['steps'][0]['evidence'][0];e.update(start=a,end=b)
                with self.assertRaises(ValueError):self.compile()
    def test_stale_commit(self):
        (self.repo/'b.js').write_text('export const b=2;\n');self.git('add','.');self.git('commit','-qm','later')
        self.spec['commit']=self.git('rev-parse','HEAD')
        with self.assertRaisesRegex(ValueError,'Stale'):self.compile()
    def test_exact_commit_and_repo_required(self):
        self.spec['commit']=self.sha[:7]
        with self.assertRaises(ValueError):self.compile()
        self.spec['commit']=self.sha;self.spec['repo']='wrong/repo'
        with self.assertRaises(ValueError):self.compile()
    def test_forged_excerpt(self):
        self.spec['tours'][0]['steps'][0]['evidence'][0]['excerpt']='wrong'
        with self.assertRaises(ValueError):self.compile()
    def test_source_path_and_symbol_required(self):
        e=self.spec['tours'][0]['steps'][0]['evidence'][0]
        e['path']='../a.js'
        with self.assertRaises(ValueError):self.compile()
        e['path']='a.js';e['symbol']=''
        with self.assertRaises(ValueError):self.compile()
    def test_runtime_does_not_mutate_import_graph(self):
        self.spec['tours'][0]['steps'][0]['nodeIds'].append('b.js')
        self.spec['tours'][0]['links']=[dict(**{'from':'b.js','to':'a.js'},type='data',direction='from-to',status='inferred',label='Inference',evidence=[dict(path='b.js',start=1,end=1,symbol='b')])]
        before=copy.deepcopy(self.map);self.compile();self.assertEqual(self.map,before)
        self.spec['tours'][0]['links'][0]['type']='import'
        with self.assertRaisesRegex(ValueError,'Import link'):self.compile()
    def test_bad_link_and_duplicate_queries(self):
        t=self.spec['tours'][0];t['links']=[dict(**{'from':'ghost','to':'a.js'},type='data')]
        with self.assertRaises(ValueError):self.compile()
        t['links']=[];t['queries'].append(' TOUR ENTRY ')
        with self.assertRaisesRegex(ValueError,'Ambiguous'):self.compile()
    def test_malicious_text_is_literal_and_only_cited_source_bundled(self):
        self.spec['tours'][0]['title']='</script><img src=x onerror=alert(1)>'
        html=render(Path(DEFAULT_TEMPLATE).read_text(),self.map,self.compile())
        self.assertNotIn('</script><img',html);self.assertNotIn('</script><script>alert',html)
        self.assertIn('\\u003c/script>',html)
        self.assertNotIn('export const b = 1;',html)
    def test_invalid_refresh_preserves_previous_artifacts(self):
        before={p.name:p.read_bytes() for p in self.out.iterdir()}
        self.spec['tours'][0]['steps'][0]['evidence'][0]['end']=999
        source=self.root/'tours.json';source.write_text(json.dumps(self.spec))
        with self.assertRaises(ValueError):build_project(self.repo,self.sha,self.layers,self.out,tours=source)
        self.assertEqual(before,{p.name:p.read_bytes() for p in self.out.iterdir()})
    def test_stale_refresh_and_render_preserve_previous_artifacts(self):
        (self.repo/'b.js').write_text('export const b=3;\n');self.git('add','.');self.git('commit','-qm','stale tour snapshot')
        self.spec['commit']=self.git('rev-parse','HEAD')
        source=self.root/'tours.json';source.write_text(json.dumps(self.spec))
        before={p.name:p.read_bytes() for p in self.out.iterdir()}
        with self.assertRaises((ValueError,subprocess.CalledProcessError)):build_project(self.repo,self.sha,self.layers,self.out,tours=source)
        with self.assertRaises((ValueError,subprocess.CalledProcessError)):render_main(['--map',str(self.out/'map.json'),'--out',str(self.out/'index.html'),'--repo',str(self.repo),'--tours',str(source)])
        self.assertEqual(before,{p.name:p.read_bytes() for p in self.out.iterdir()})
    def test_zero_tours_default(self):
        html=(self.out/'index.html').read_text()
        self.assertIn('var TOUR_DATA = null;',html)
        self.assertNotIn('walk me through submitting code',html)
    def test_valid_refresh_attaches_inline_evidence(self):
        source=self.root/'tours.json';source.write_text(json.dumps(self.spec))
        build_project(self.repo,self.sha,self.layers,self.out,tours=source)
        html=(self.out/'index.html').read_text();self.assertIn(self.sha,html);self.assertIn('Source walkthrough',html)

if __name__=='__main__':unittest.main()
