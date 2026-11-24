import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
const runtime=process.env.CODEX_ARTIFACT_RUNTIME;
if(!runtime) throw new Error('Set CODEX_ARTIFACT_RUNTIME to the Codex bundled dependencies directory');
const root=process.cwd();
process.env.RUNTIME_NODE_MODULES=path.join(runtime,'node/node_modules');
const {Presentation,PresentationFile}=await import(pathToFileURL(path.join(runtime,'node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs')).href);
const {slides,model,routing,test_count,coverage}=JSON.parse(await fs.readFile('docs/slide_content.json','utf8'));
const deck=Presentation.create({slideSize:{width:1280,height:720}});
const C={navy:'#0f2745',green:'#047857',blue:'#2563eb',text:'#182b3f',muted:'#475569',pale:'#e2e8f0',white:'#ffffff',red:'#b91c1c'};
function box(s,x,y,w,h,fill=C.pale,geometry='rect'){
 return s.shapes.add({geometry,position:{left:x,top:y,width:w,height:h},fill,line:{fill:'none',width:0}});
}
function text(s,value,x,y,w,h,size=20,color=C.text,bold=false){
 const t=box(s,x,y,w,h,'none','textbox');t.text=value;t.text.style={fontFamily:'Arial',fontSize:`${size}pt`,color,bold};return t;
}
function base(i){
 const s=deck.slides.add();s.background.fill=C.white;
 box(s,64,43,48,5,C.green);
 text(s,slides[i].title,64,65,1140,70,31,C.navy,true);
 box(s,64,654,1152,1,C.pale);
 text(s,'IIIT Lucknow · Software Engineering · Synthetic simulation',64,671,1030,25,11,C.muted);
 text(s,`${i+1} / 5`,1140,671,75,25,11,C.muted);
 s.speakerNotes.text=slides[i].notes+'\n\nPrimary evidence: results/model_metrics.json; results/routing_benchmark.csv; results/routing_summary.json; results/test_report.csv; results/coverage.json. Assumptions and references: docs/SRS.pdf.';
 return s;
}
{
 const s=base(0),d=slides[0];
 text(s,d.subtitle,64,155,1140,120,32,C.navy,true);
 text(s,'Indian Institute of Information Technology Lucknow',64,279,1100,32,14,C.muted);
 text(s,d.heading,64,315,650,55,26,C.green,true);
 text(s,d.body,64,390,650,200,22);
 text(s,'Student contributors',810,323,390,45,19,C.navy,true);
 text(s,d.authors,810,385,390,170,17,C.text);
 text(s,'Fictional network and generated history. Results describe a simulation.',64,610,1150,30,14,C.muted);
}
{
 const s=base(1),d=slides[1];
 const labels=['CSV validation\nHistory and topology','Prediction\nSelected regressor','Weighted routing\nStation/line state','Streamlit view\nRoutes and metrics'];
 labels.forEach((label,j)=>{const x=64+j*294;box(s,x,185,252,118,j===2?'#d1fae5':'#eff6ff');text(s,label,x+14,210,225,80,17,C.navy,true);if(j<3)box(s,x+262,225,25,26,C.green,'rightArrow');});
 text(s,d.left_heading,64,365,540,45,24,C.navy,true);
 text(s,d.left,64,430,540,180,20);
 text(s,d.right_heading,690,365,520,45,24,C.navy,true);
 text(s,d.right,690,430,520,180,20);
}
{
 const s=base(2),d=slides[2];
 box(s,64,160,1152,86,'#eff6ff');text(s,d.formula,82,180,1116,50,20,C.navy,true);
 text(s,d.left_heading,64,290,590,58,24,C.navy,true);
 text(s,d.left,64,365,590,205,20);
 text(s,d.right_heading,718,290,495,72,23,C.green,true);
 text(s,d.right,718,380,495,205,20);
 text(s,d.footer,64,605,1150,38,13,C.muted);
}
{
 const s=base(3),d=slides[3];
 const stats=[[String(test_count),'Passing automated cases'],[d.statement,'Statement coverage'],[d.branch,'Branch coverage']];
 stats.forEach(([value,label],j)=>{let x=64+j*394;text(s,value,x,162,365,70,33,C.green,true);text(s,label,x,238,365,35,17,C.muted);});
 text(s,d.left_heading,64,332,548,50,23,C.navy,true);
 text(s,d.left,64,402,548,205,19);
 text(s,d.right_heading,692,332,518,50,23,C.navy,true);
 text(s,d.right,692,402,518,205,19);
 text(s,d.footer,64,611,1150,35,12,C.muted);
}
{
 const s=base(4),d=slides[4];
 const stats=[[d.improved,'Lower mean exposure'],[d.unchanged,'Unchanged itineraries'],[d.worse,'Worse mean exposure']];
 stats.forEach(([value,label],j)=>{let x=64+j*394;text(s,value,x,155,365,65,34,j===2?C.red:C.green,true);text(s,label,x,225,365,35,17,C.muted);});
 text(s,d.example,64,300,1150,40,20,C.navy,true);
 text(s,'Mean predicted congestion',64,367,500,35,17,C.muted);
 const values=[routing.demo.baseline_mean,routing.demo.smart_mean];
 ['Baseline','Recommended'].forEach((label,j)=>{
   const y=425+j*66;text(s,label,64,y,185,36,18,C.text);
   box(s,260,y+4,values[j]*580,27,j===0?C.blue:C.green);
   text(s,values[j].toFixed(3),510,y-1,100,40,18,C.text,true);
 });
 text(s,d.demo,700,376,510,100,24,C.green,true);
 text(s,d.innovation,700,498,510,109,18,C.text);
 text(s,d.limitation,64,601,1150,40,13,C.muted);
}
await fs.mkdir('tmp/slides',{recursive:true});
// Export editable source and every final slide preview.
const candidate=path.join(root,'tmp/slides/candidate.pptx');
await (await PresentationFile.exportPptx(deck)).save(candidate);
for(let i=0;i<deck.slides.items.length;i++){
 const blob=await deck.export({slide:deck.slides.items[i],format:'png',scale:1});
 await fs.writeFile(`tmp/slides/slide-${i+1}.png`,new Uint8Array(await blob.arrayBuffer()));
}
const skill=process.env.CODEX_PRESENTATIONS_SKILL;
if(!skill) throw new Error('Set CODEX_PRESENTATIONS_SKILL to the presentations skill directory');
const {finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
const buildId=Date.now();
const finalPath=path.join(root,`tmp/slides/validated-${buildId}.pptx`);
const receiptPath=path.join(root,`tmp/presentation_validation-${buildId}.json`);
const result=await finalizePresentation({workspaceDir:root,candidatePath:candidate,finalPath,
 pythonExecutable:process.env.RUNTIME_PYTHON || path.join(runtime,process.platform==='win32'?'python/python.exe':'python/bin/python'),
 integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
 layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit'],
 explicitTotalSlideCount:5,requiredNativeTableOwnerSlides:[],requiredNativeChartOwnerSlides:[],
 fontPolicy:{basis:'design',families:['Arial']},verifyArtifactToolImport:true,
 receiptPath});
await fs.copyFile(finalPath,'docs/presentation.pptx');
await fs.copyFile(receiptPath,'results/presentation_validation.json');
console.log('Five-slide presentation exported and validated');

// All exports and validation have completed; the embedded WASM runtime may set a nonzero host exit code.
process.exit(0);
