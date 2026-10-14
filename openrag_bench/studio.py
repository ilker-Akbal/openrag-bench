"""Generate an entirely self-contained, offline Golden Dataset Studio HTML editor.

All imported questions/documents stay in this browser tab until explicit download.
No HTTP server, cloud APIs, telemetry or remote assets. No auto-persistence.
"""
import argparse
from pathlib import Path

STUDIO_HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="referrer" content="no-referrer">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src 'none'; connect-src 'none'; form-action 'none'; base-uri 'none'">
<title>Golden Dataset Studio · OpenRAG Bench</title>
<style>
:root{color-scheme:light;font-family:system-ui,-apple-system,"Segoe UI",sans-serif;--ink:#132239;--soft:#51627b;--border:#dbe3ef;--paper:#fff;--accent:#225ab9}
*{box-sizing:border-box}
body{margin:0;background:#f3f6fb;color:var(--ink);line-height:1.5}
.wrap{max-width:1450px;margin:0 auto;padding:1.5rem}
h1{font-size:clamp(1.65rem,3vw,2.45rem);margin:.3rem 0;letter-spacing:-.03em}
h2{font-size:1.1rem;margin:.3rem 0 1rem}
h3{font-size:.98rem;margin:0}
p{margin:.5rem 0 1rem}
.eyebrow{letter-spacing:.13em;font-size:.72rem;font-weight:800;color:#43628b}
.muted{color:var(--soft);font-size:.9rem}
header{display:flex;gap:1.2rem;align-items:center;justify-content:space-between;flex-wrap:wrap}
header .meta{font-size:.81rem;background:#e5edf9;padding:.45rem .75rem;border-radius:30px}
.panel,.hero,.notice{background:var(--paper);border:1px solid var(--border);border-radius:15px;padding:1.2rem;min-width:0}
.hero{margin:1.1rem 0;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:.8rem;align-items:center}
.hero strong{display:block;font-size:1.4rem}
.notice{background:#fffdf5;border-color:#ead79b;margin:1rem 0;color:#6e5216;font-size:.9rem}
.grid{display:grid;grid-template-columns:minmax(230px,1fr) minmax(250px,1.05fr) minmax(360px,1.7fr);gap:1rem;align-items:start}
button,input,textarea,select{font:inherit}
input,textarea,select{width:100%;border:1px solid #9aaec7;border-radius:8px;padding:.58rem;background:#fff;color:var(--ink)}
textarea{resize:vertical;min-height:82px}
button{cursor:pointer;border-radius:9px;border:1px solid #8da2bd;background:#fff;padding:.52rem .72rem;font-weight:650;color:#183351}
button:hover{background:#eef3fa}
button.primary{background:#2057aa;color:#fff;border-color:#2057aa}
button.primary:hover{background:#16488c}
button.danger{color:#a42323;border-color:#e3b1b1}
button:disabled{opacity:.5;cursor:not-allowed}
:focus-visible{outline:3px solid #dd9300;outline-offset:2px}
.actions{display:flex;gap:.55rem;flex-wrap:wrap;margin:.7rem 0}
.field{display:block;margin:.7rem 0;font-weight:620;font-size:.84rem}
.field input,.field textarea,.field select{margin:.3rem 0;font-weight:400}
.check{display:flex;gap:.5rem;align-items:center;font-size:.88rem}
.check input{width:auto}
.list{display:flex;flex-direction:column;gap:.45rem;max-height:460px;overflow:auto}
.list button{text-align:left;width:100%;overflow-wrap:anywhere}
.list button.active{background:#e9f0fc;border-color:#3166b5;box-shadow:inset 3px 0 #3166b5}
.list small{display:block;font-weight:400;color:var(--soft);margin-top:.15rem}
.doc-choice{display:grid;grid-template-columns:minmax(0,1fr) 125px;gap:.5rem;align-items:center;border-bottom:1px solid #e5ebf3;padding:.65rem 0}
.doc-choice strong{overflow-wrap:anywhere}
.doc-choice small{display:block;color:var(--soft);overflow-wrap:anywhere}
.doc-choice select{font-size:.83rem}
.toolbar{display:flex;align-items:center;gap:.7rem;justify-content:space-between;flex-wrap:wrap}
.hint{font-size:.79rem;color:var(--soft)}
#message{min-height:1.7rem;color:#176044;font-size:.9rem;font-weight:600}
#message.error{color:#a42323}
.export{margin:1rem 0}
footer{padding:1.2rem 0;font-size:.8rem;color:var(--soft)}
code{font-family:ui-monospace,SFMono-Regular,Consolas,monospace;background:#edf2f8;padding:.08rem .26rem;border-radius:3px}
.sr-only{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0)}
@media(max-width:1050px){.grid{grid-template-columns:1fr 1fr}.editor{grid-column:1/-1}}
@media(max-width:650px){.wrap{padding:.7rem}.grid,.hero{grid-template-columns:1fr}.editor{grid-column:auto}.doc-choice{grid-template-columns:minmax(0,1fr) 120px}.panel{padding:.85rem}}
</style>
</head>
<body>
<main class="wrap">
<header>
<div><div class="eyebrow">OPENRAG BENCH · LOCAL TOOL</div><h1>Golden Dataset Studio</h1>
<p class="muted">Create trusted question → document relevance labels without editing JSON.</p></div>
<span class="meta">OFFLINE · NO CLOUD · NO AUTOMATIC SAVING</span>
</header>
<section class="hero" aria-label="Annotation progress">
<div><strong id="total-queries">0</strong><span class="muted">Queries</span></div>
<div><strong id="total-docs">0</strong><span class="muted">Document IDs</span></div>
<div><strong id="total-labeled">0</strong><span class="muted">Queries with positive judgments</span></div>
</section>
<p class="notice">Your questions and document metadata remain in this browser tab. <strong>Export a draft often</strong>: closing or reloading loses unsaved changes. This editor creates human-assigned relevance labels, not actual retrieval results. To measure quality, your retriever must subsequently supply ranked <code>retrieved_ids</code>.</p>
<section class="grid">
<div class="panel">
<div class="toolbar"><h2>1 · Document catalog</h2><span class="hint">Stable IDs</span></div>
<label class="field">Document ID<input id="doc-id" maxlength="128" autocomplete="off" placeholder="privacy-guide"></label>
<label class="field">Display title (local only)<input id="doc-title" maxlength="240" autocomplete="off" placeholder="Privacy policy"></label>
<div class="actions"><button id="add-doc" type="button">Add document</button><button id="import-docs" type="button">Import catalog JSON</button></div>
<input type="file" id="docs-file" class="sr-only" accept=".json,application/json">
<label class="field">Find document<input type="search" id="doc-search" placeholder="Search ID or title"></label>
<div id="docs-list" class="list" aria-live="polite"></div>
<p class="hint">Document titles never appear in exported retrieval evaluation rows. IDs must match your retriever's document IDs.</p>
</div>
<div class="panel">
<div class="toolbar"><h2>2 · Questions</h2><span class="hint">Human reviewed</span></div>
<div class="actions"><button class="primary" id="add-query" type="button">+ New question</button><button id="import-dataset" type="button">Import dataset or draft</button></div>
<input type="file" id="dataset-file" class="sr-only" accept=".json,application/json">
<label class="field">Find query<input id="query-search" type="search" placeholder="Search IDs and questions"></label>
<div id="query-list" class="list" aria-live="polite"></div>
</div>
<div class="panel editor">
<div class="toolbar"><h2>3 · Label selected question</h2><button class="danger" id="remove-query" type="button">Remove question</button></div>
<div id="empty-editor" class="muted">Create or import a question to start human relevance labeling.</div>
<div id="query-editor" hidden>
<label class="field">Query ID<input id="query-id" maxlength="128" autocomplete="off" placeholder="q-001"></label>
<label class="field">Question / prompt (kept local until explicit export)<textarea id="question" maxlength="4000" placeholder="What is the warranty duration?"></textarea></label>
<label class="field">Category<input id="category" maxlength="128" autocomplete="off" placeholder="general"></label>
<label class="check"><input id="critical" type="checkbox"> Critical query — block a release if a required hit is lost</label>
<div class="toolbar" style="margin-top:1rem"><h3>Relevant documents</h3><span id="positive-count" class="hint"></span></div>
<label class="field">Filter documents<input id="label-search" type="search" placeholder="Search catalog"></label>
<div id="label-list"></div>
<p class="hint">Choose 0 for irrelevant; 1, 2 or 3 for human-verified graded relevance. A query needs at least one positive judgment before export.</p>
</div>
</div>
</section>
<section class="panel export" aria-label="Export validated data">
<div class="toolbar"><div><h2>4 · Export and test</h2><p class="muted">Drafts preserve titles and incomplete work. Judgments and Guard rules are separate files.</p></div></div>
<div class="actions">
<button id="download-draft" type="button">Save editable draft</button>
<button id="export-judgments" class="primary" type="button">Export golden judgments</button>
<button id="export-policy" type="button">Export Guard policy</button>
<button id="load-sample" type="button">Load synthetic example</button>
</div>
<div id="message" role="status" aria-live="polite"></div>
<p class="hint">The judgments JSON intentionally contains empty <code>retrieved_ids</code>. Empty retrievals are <em>not</em> a valid measured benchmark. First run your actual retriever for the same query IDs to populate candidate and baseline rankings, then run <code>openrag-bench doctor</code> and <code>openrag-bench guard</code>. Auto-generated rules are defaults: review and tune the thresholds before relying on them in CI.</p>
</section>
<footer>No external scripts, images, fonts, requests, telemetry or cloud storage. Keep downloaded drafts and judgment files private when questions or document IDs are sensitive. Labels are human annotations, not automatically inferred ground truth.</footer>
</main>
<script>
"use strict";
(function(){
const $ = (id) => document.getElementById(id);
const LIMIT_DOCS = 2500, LIMIT_QUERIES = 1000, MAX_BYTES = 5*1024*1024;
let state={documents:[],queries:[]}, selected=-1;
function clean(v,max,label){
  if(typeof v!=="string" || !v.trim() || v.length>max) throw Error(label+" must be a nonempty string (max "+max+" chars).");
  return v.trim();
}
function warn(message,error){
  $("message").textContent=String(message);
  $("message").className=error?"error":"";
}
function el(tag,text,cls){
  const node=document.createElement(tag);
  if(text!==undefined)node.textContent=String(text);
  if(cls)node.className=cls;
  return node;
}
function validDocs(docs){
  if(!Array.isArray(docs)||docs.length>LIMIT_DOCS)throw Error("Catalog must contain up to "+LIMIT_DOCS+" documents.");
  const seen=new Set();
  return docs.map(doc=>{
    if(!doc||typeof doc!=="object"||Array.isArray(doc))throw Error("Invalid document object.");
    const id=clean(doc.id,128,"Document ID");
    if(seen.has(id))throw Error("Duplicate document ID: "+id);
    seen.add(id);
    return {id:id,title:typeof doc.title==="string"&&doc.title.trim()?clean(doc.title,240,"Title"):id};
  });
}
function validQueries(rows){
  if(!Array.isArray(rows)||rows.length>LIMIT_QUERIES)throw Error("Dataset must contain up to "+LIMIT_QUERIES+" queries.");
  const seen=new Set();
  return rows.map(row=>{
    if(!row||typeof row!=="object"||Array.isArray(row))throw Error("Invalid query object.");
    const id=clean(row.query_id,128,"Query ID");
    if(seen.has(id))throw Error("Duplicate query ID: "+id);
    seen.add(id);
    const grades=Object.create(null);
    if(row.grades && typeof row.grades==="object" && !Array.isArray(row.grades)){
      Object.entries(row.grades).forEach(([doc,grade])=>{
        clean(doc,128,"Document ID");
        if(!Number.isInteger(grade)||grade<1||grade>3)throw Error("Invalid grade for "+id);
        grades[doc]=grade;
      });
    }else{
      const relevant=row.relevant_ids||[];
      if(!Array.isArray(relevant))throw Error("relevant_ids must be a list for "+id);
      const unique=new Set();
      relevant.forEach(doc=>{clean(doc,128,"Document ID");if(unique.has(doc))throw Error("Duplicate relevant ID in "+id);unique.add(doc);grades[doc]=1;});
      if(row.relevance_grades!==undefined){
        if(!row.relevance_grades||typeof row.relevance_grades!=="object"||Array.isArray(row.relevance_grades)||Object.keys(row.relevance_grades).length!==relevant.length)throw Error("Relevance grades disagree with positive labels for "+id);
        relevant.forEach(doc=>{
          const grade=row.relevance_grades[doc];
          if(!Number.isInteger(grade)||grade<1||grade>3)throw Error("Relevance grade must be 1 to 3 in Studio.");
          grades[doc]=grade;
        });
      }
    }
    const retrieved=row.retrieved_ids||[];
    if(!Array.isArray(retrieved)||retrieved.some(x=>typeof x!=="string"||!x.trim())||new Set(retrieved).size!==retrieved.length)throw Error("Invalid retrieved IDs in "+id);
    if(row.critical!==undefined && typeof row.critical!=="boolean")throw Error("critical must be a boolean in "+id);
    if(row.question!==undefined&&typeof row.question!=="string")throw Error("Invalid question in "+id);
    if(row.category!==undefined&&typeof row.category!=="string")throw Error("Invalid category in "+id);
    return {query_id:id,question:row.question||"",category:row.category||"general",
      critical:row.critical===true,grades:grades,retrieved_ids:[...retrieved]};
  });
}
function validateRefs(){
 const ids=new Set(state.documents.map(doc=>doc.id));
 for(const row of state.queries){
  for(const id of Object.keys(row.grades))if(!ids.has(id))throw Error("Query "+row.query_id+" references missing document "+id);
 }
}
function validateForExport(){
 if(!state.queries.length)throw Error("Add at least one query.");
 if(!state.documents.length)throw Error("Add documents before exporting.");
 validDocs(state.documents);
 validQueries(state.queries);
 validateRefs();
 for(const row of state.queries){
   clean(row.question,4000,"Question "+row.query_id);
   clean(row.category,128,"Category "+row.query_id);
   if(!Object.keys(row.grades).length)throw Error("Label at least one relevant document for "+row.query_id);
 }
}
function displayCounts(){
 $("total-queries").textContent=state.queries.length;
 $("total-docs").textContent=state.documents.length;
 $("total-labeled").textContent=state.queries.filter(x=>Object.keys(x.grades).length).length;
}
function drawDocs(){
 const filter=$("doc-search").value.toLowerCase(),list=$("docs-list");
 list.replaceChildren();
 state.documents.forEach((doc,i)=>{
  if(!(doc.id+" "+doc.title).toLowerCase().includes(filter))return;
  const box=el("div"),title=el("strong",doc.title),id=el("small",doc.id);
  const remove=el("button","Remove","danger");
  remove.type="button";
  remove.addEventListener("click",()=>{
    if(!window.confirm("Remove document "+doc.id+" and all its query labels?"))return;
    state.documents.splice(i,1);
    state.queries.forEach(q=>{delete q.grades[doc.id];q.retrieved_ids=q.retrieved_ids.filter(d=>d!==doc.id);});
    refresh();warn("Document removed; affected labels were cleared.",false);
  });
  box.style.cssText="padding:.45rem 0;border-bottom:1px solid #e6ebf2";
  box.append(title,id,remove);list.append(box);
 });
}
function drawQueries(){
 const filter=$("query-search").value.toLowerCase(),list=$("query-list");
 list.replaceChildren();
 state.queries.forEach((q,i)=>{
  if(!(q.query_id+" "+q.question).toLowerCase().includes(filter))return;
  const b=el("button",undefined,i===selected?"active":"");
  b.type="button";
  b.append(el("strong",q.query_id),el("small",(q.critical?"Critical · ":"")+
   Object.keys(q.grades).length+" relevant · "+q.question.slice(0,90)));
  b.addEventListener("click",()=>{selected=i;drawQueries();drawEditor();});
  list.append(b);
 });
}
function drawEditor(){
 const valid=selected>=0&&selected<state.queries.length;
 $("query-editor").hidden=!valid;
 $("empty-editor").hidden=valid;
 $("remove-query").disabled=!valid;
 if(!valid)return;
 const q=state.queries[selected];
 $("query-id").value=q.query_id;$("question").value=q.question;
 $("category").value=q.category;$("critical").checked=q.critical;
 drawLabels();
}
function drawLabels(){
 if(selected<0)return;
 const q=state.queries[selected],out=$("label-list"),filter=$("label-search").value.toLowerCase();
 out.replaceChildren();
 $("positive-count").textContent=Object.keys(q.grades).length+" selected";
 state.documents.forEach(doc=>{
  if(!(doc.id+" "+doc.title).toLowerCase().includes(filter))return;
  const row=el("div",undefined,"doc-choice"),info=el("div");
  info.append(el("strong",doc.title),el("small",doc.id));
  const select=el("select");select.setAttribute("aria-label","Relevance grade for "+doc.id);
  [["0","Not relevant"],["1","Relevant · 1"],["2","High · 2"],["3","Highest · 3"]].forEach(([num,title])=>{
    const o=el("option",title);o.value=num;select.append(o);
  });
  select.value=String(q.grades[doc.id]||0);
  select.addEventListener("change",()=>{
    const grade=Number(select.value);
    if(grade)q.grades[doc.id]=grade;else delete q.grades[doc.id];
    $("positive-count").textContent=Object.keys(q.grades).length+" selected";
    displayCounts();
  });
  row.append(info,select);out.append(row);
 });
}
function refresh(){displayCounts();drawDocs();drawQueries();drawEditor();}
function output(name,data){
 const blob=new Blob([JSON.stringify(data,null,2)+"\n"],{type:"application/json;charset=utf-8"});
 const url=URL.createObjectURL(blob),link=el("a");
 link.href=url;link.download=name;document.body.append(link);link.click();link.remove();
 setTimeout(()=>URL.revokeObjectURL(url),2000);
 warn("Saved "+name+" locally. No network request was made.",false);
}
function datasetRows(){
 return state.queries.map(q=>{
   const ids=Object.keys(q.grades).sort();
   const grades=Object.create(null);ids.forEach(id=>grades[id]=q.grades[id]);
   return {query_id:q.query_id,question:q.question,category:q.category,
     critical:q.critical,retrieved_ids:[],relevant_ids:ids,relevance_grades:grades};
 });
}
function makePolicy(){
 const rules=[{id:"overall-quality",select:{type:"all"},metric:"ndcg_at_k",min_delta:0}];
 if(state.queries.some(q=>q.critical)){
   rules.push({id:"critical-coverage",select:{type:"critical"},metric:"hit_at_k",min_query_score:1,max_regressed_queries:0});
 }
 const categories=[...new Set(state.queries.map(q=>q.category.trim()))].sort();
 categories.forEach((category,i)=>{
   rules.push({id:"category-"+String(i+1),select:{type:"category",value:category},metric:"ndcg_at_k",min_delta:0});
 });
 return {version:1,rules:rules};
}
function importValue(value){
 let docs,queries;
 if(Array.isArray(value)){
   queries=validQueries(value);
   const ids=new Set();
   queries.forEach(q=>{
     Object.keys(q.grades).forEach(x=>ids.add(x));
     q.retrieved_ids.forEach(x=>ids.add(x));
   });
   docs=validDocs([...ids].map(id=>({id:id,title:id})));
 }else if(value&&typeof value==="object"&&value.format==="openrag-studio-draft/v1"){
   docs=validDocs(value.documents);queries=validQueries(value.queries);
 }else throw Error("Use an OpenRAG Bench JSON row array or Studio draft v1.");
 const known=new Set(docs.map(d=>d.id));
 queries.forEach(q=>Object.keys(q.grades).forEach(id=>{if(!known.has(id))throw Error("Unknown labeled document: "+id);}));
 state={documents:docs,queries:queries};selected=queries.length?0:-1;refresh();
 warn("Imported "+queries.length+" queries and "+docs.length+" document IDs. Review labels before exporting.",false);
}
function loadFile(input,callback){
 const file=input.files[0];input.value="";
 if(!file)return;
 if(file.size>MAX_BYTES){warn("Files must be smaller than 5 MiB.",true);return;}
 const reader=new FileReader();
 reader.onload=()=>{
  try{callback(JSON.parse(String(reader.result)));}
  catch(e){warn("Import rejected: "+e.message,true);}
 };
 reader.onerror=()=>warn("The selected file could not be read.",true);
 reader.readAsText(file,"utf-8");
}
$("add-doc").addEventListener("click",()=>{
 try{
  if(state.documents.length>=LIMIT_DOCS)throw Error("Catalog limit reached.");
  const id=clean($("doc-id").value,128,"Document ID");
  if(state.documents.some(d=>d.id===id))throw Error("Duplicate document ID "+id);
  const title=$("doc-title").value.trim()||id;
  state.documents.push(...validDocs([{id:id,title:title}]));
  $("doc-id").value="";$("doc-title").value="";refresh();warn("Document added.",false);
 }catch(e){warn(e.message,true);}
});
$("add-query").addEventListener("click",()=>{
 if(state.queries.length>=LIMIT_QUERIES){warn("Query limit reached.",true);return;}
 let n=state.queries.length+1,id;
 do{id="q-"+String(n).padStart(3,"0");n++;}while(state.queries.some(q=>q.query_id===id));
 state.queries.push({query_id:id,question:"",category:"general",
 critical:false,grades:Object.create(null),retrieved_ids:[]});
 selected=state.queries.length-1;refresh();warn("Set the question and verify relevant document labels.",false);
});
$("remove-query").addEventListener("click",()=>{
 if(selected<0||!window.confirm("Remove selected query and all its labels?"))return;
 state.queries.splice(selected,1);selected=Math.min(selected,state.queries.length-1);
 refresh();warn("Query removed.",false);
});
$("query-id").addEventListener("change",()=>{
 if(selected<0)return;
 try{
  const id=clean($("query-id").value,128,"Query ID");
  if(state.queries.some((q,i)=>i!==selected&&q.query_id===id))throw Error("Duplicate query ID "+id);
  state.queries[selected].query_id=id;drawQueries();warn("Query ID updated.",false);
 }catch(e){$("query-id").value=state.queries[selected].query_id;warn(e.message,true);}
});
$("question").addEventListener("input",()=>{if(selected>=0)state.queries[selected].question=$("question").value;});
$("question").addEventListener("change",drawQueries);
$("category").addEventListener("input",()=>{if(selected>=0)state.queries[selected].category=$("category").value;});
$("critical").addEventListener("change",()=>{if(selected>=0){state.queries[selected].critical=$("critical").checked;drawQueries();}});
$("query-search").addEventListener("input",drawQueries);
$("doc-search").addEventListener("input",drawDocs);
$("label-search").addEventListener("input",drawLabels);
$("import-docs").addEventListener("click",()=>$("docs-file").click());
$("import-dataset").addEventListener("click",()=>$("dataset-file").click());
$("docs-file").addEventListener("change",()=>loadFile($("docs-file"),value=>{
 const docs=validDocs(value);
 const existing=new Set(state.documents.map(d=>d.id));
 const added=docs.filter(d=>!existing.has(d.id));
 if(state.documents.length+added.length>LIMIT_DOCS)throw Error("Catalog limit exceeded.");
 state.documents.push(...added);refresh();warn("Imported "+added.length+" new document IDs.",false);
}));
$("dataset-file").addEventListener("change",()=>loadFile($("dataset-file"),value=>{
 if((state.documents.length||state.queries.length)&&
   !window.confirm("Replace the current work with imported data? Save a draft first."))return;
 importValue(value);
}));
$("download-draft").addEventListener("click",()=>{
 try{
  const docs=validDocs(state.documents),queries=validQueries(state.queries);
  output("openrag-studio-draft.json",{format:"openrag-studio-draft/v1",documents:docs,queries:queries});
 }catch(e){warn(e.message,true);}
});
$("export-judgments").addEventListener("click",()=>{
 try{validateForExport();output("openrag-golden-judgments.json",datasetRows());}
 catch(e){warn(e.message,true);}
});
$("export-policy").addEventListener("click",()=>{
 try{validateForExport();output("openrag-guard-policy.json",makePolicy());}
 catch(e){warn(e.message,true);}
});
$("load-sample").addEventListener("click",()=>{
 if((state.documents.length||state.queries.length)&&!window.confirm("Replace current data with a synthetic example? Save a draft first."))return;
 const docs=[{id:"warranty",title:"Warranty policy"},{id:"setup",title:"Installation guide"},{id:"privacy",title:"Privacy and deletion guide"}];
 const rows=[
 {query_id:"q-warranty",question:"What is the warranty duration?",category:"support",critical:false,retrieved_ids:[],relevant_ids:["warranty"],relevance_grades:{"warranty":2}},
 {query_id:"q-setup",question:"How do I install it?",category:"support",critical:false,retrieved_ids:[],relevant_ids:["setup"]},
 {query_id:"q-privacy",question:"How do I delete my data?",category:"privacy",critical:true,retrieved_ids:[],relevant_ids:["privacy"],relevance_grades:{"privacy":3}}
 ];
 state={documents:validDocs(docs),queries:validQueries(rows)};selected=0;refresh();
 warn("Loaded original synthetic example. Export and replace retrieval IDs with real results.",false);
});
window.addEventListener("beforeunload",event=>{
 if(state.documents.length||state.queries.length){event.preventDefault();event.returnValue="";}
});
refresh();
})();
</script>
</body></html>
"""


def studio(argv=None):
    """Safely create an offline HTML editor without opening a network server."""
    parser = argparse.ArgumentParser(
        prog="openrag-bench studio",
        description="Create a local, self-contained relevance-label editor",
    )
    parser.add_argument("--output", type=Path, default=Path("golden-dataset-studio.html"))
    parser.add_argument("--overwrite", action="store_true",
                        help="Explicitly replace an existing Studio HTML file")
    args = parser.parse_args(argv)
    try:
        target = args.output
        if target.exists() and not args.overwrite:
            raise ValueError(f"{target}: already exists; refusing overwrite")
        if target.is_symlink():
            raise ValueError(f"{target}: symlink targets are not permitted")
        with target.open("w" if args.overwrite else "x", encoding="utf-8") as output:
            output.write(STUDIO_HTML)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(f"Created offline Golden Dataset Studio: {args.output}")
    print("Open the HTML file in a browser. Nothing is uploaded or saved automatically.")
    return 0
