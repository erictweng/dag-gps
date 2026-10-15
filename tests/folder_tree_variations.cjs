'use strict';
// Extend (never edit) the frozen variation grid with a separate folder axis.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {generate,classify,counts}=require('../scripts/bench_variations.cjs');
const out=path.resolve(__dirname,'../artifacts/folder-tree'), config=require('../eval/variation_templates.json');
const read=p=>JSON.parse(fs.readFileSync(p)), report={};
for(const repo of ['honcho','salesroom']) {
  const before=read(path.resolve(__dirname,'../artifacts/question-parser',repo,'snapshot.json'));
  const after=read(path.join(out,repo,'snapshot.json'));
  const rows=generate(config,repo,before);
  const folderRows=read(path.join(out,repo,'folder-questions.json')).map(r=>({id:r.id,question:r.question,axis:'folder',value:r.folder,
    operation:r.operation,targets:[after.map.nodes.find(n=>n.label===r.folder&&n.kind==='layer').id],negative:false}));
  const versions={};
  for(const [version,snapshot,code] of [['before',before,path.join(out,'base/web')],['after',after,path.resolve(__dirname,'../web')]]) {
    const service=require(path.join(code,'query-service.js')).createQueryService(snapshot);
    const scorer=require(path.join(code,'scorer.js')).createScorer(snapshot.map);
    versions[version]=[...rows,...folderRows].map(r=>{
      const p=service.query({requestId:r.id,query:r.question});
      const op=p.operation==='NOT_SURE'&&p.status==='needs-choice'?scorer.score(r.question).requestedOperation:p.operation;
      const legacyOutcome=classify(r,p,op);
      let outcome=legacyOutcome;
      // New contract: folder PATH witnesses are real files, never invented
      // folder hops. Retain raw old-grader output alongside this explicit audit.
      if(snapshot.map.meta.folderTree===1 && r.operation==='PATH' && r.targets.length===2 &&
          p.status==='matched' && p.operation==='PATH') {
        const endpoints=r.targets.map(id=>snapshot.map.nodes.find(n=>n.id===id));
        if(endpoints.every(n=>n?.kind==='layer') && p.witnesses.some(w=>{
          const ends=[w.nodeIds[0],w.nodeIds.at(-1)].map(id=>snapshot.map.nodes.find(n=>n.id===id));
          return ends.every((n,i)=>n?.kind==='file' && (endpoints[i].label==='(root)'?
            !n.path.includes('/'):n.path.startsWith(endpoints[i].label+'/')));
        })) outcome='correct';
      }
      return {...r,outcome,legacyOutcome,status:p.status,actualOperation:p.operation};
    });
    fs.writeFileSync(path.join(out,repo,'variation-'+version+'.jsonl'),versions[version].map(r=>JSON.stringify(r)).join('\n')+'\n');
  }
  const summarize=predicate=>{
    const a=versions.before.filter(predicate), b=versions.after.filter(predicate);
    return {cases:a.length,before:counts(a),after:counts(b),rawOldGraderAfter:counts(b.map(r=>({...r,outcome:r.legacyOutcome}))),
      newWrong:b.filter((r,i)=>r.outcome==='wrong'&&a[i].outcome!=='wrong').length};
  };
  report[repo]={gridSha256:crypto.createHash('sha256').update(JSON.stringify(rows)).digest('hex'),
    frozenGrid:summarize(r=>r.axis!=='folder'),folderAxis:summarize(r=>r.axis==='folder'),
    axes:Object.fromEntries([...new Set(versions.after.map(r=>r.axis))].map(axis=>[axis,summarize(r=>r.axis===axis)]))};
  console.log(repo,JSON.stringify({frozenGrid:report[repo].frozenGrid,folderAxis:report[repo].folderAxis}));
}
fs.writeFileSync(path.join(out,'variation.json'),JSON.stringify(report,null,2));
