/* Offline Studio UI logic smoke, using a minimal deterministic DOM harness.
 * It executes the real shipped inline script, exercises user actions and
 * verifies explicitly downloaded JSON. No network or third-party npm deps.
 * This is NOT a substitute for manual accessibility/browser usability QA.
 */
"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const html = fs.readFileSync("studio-smoke.html", "utf8");
const start = html.indexOf("<script>"), end = html.lastIndexOf("</script>");
assert(start >= 0 && end > start, "Expected one inline script.");
const script = html.slice(start + "<script>".length, end);
const downloads = [];
let currentBlob = null;
let context;

class Element {
  constructor(tag, id = "") {
    this.tag = tag;
    this.id = id;
    this.children = [];
    this.listeners = {};
    this.value = "";
    this.checked = false;
    this.hidden = false;
    this.disabled = false;
    this.style = {};
    this.files = [];
    this._text = "";
  }
  set textContent(value) {
    this._text = String(value);
    this.children = [];
  }
  get textContent() {
    return this._text + this.children.map(x => x.textContent || "").join("");
  }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this.children = [...children]; }
  addEventListener(type, handler) { this.listeners[type] = handler; }
  dispatch(type) {
    if (this.listeners[type]) this.listeners[type]({target:this,preventDefault(){}});
  }
  click() {
    if (this.tag === "a") downloads.push({name:this.download,blob:currentBlob});
    this.dispatch("click");
  }
  remove() {}
  setAttribute(key, value) { this[key] = value; }
}

const ids = new Map();
const doc = {
  body: new Element("body"),
  getElementById(id) {
    if (!ids.has(id)) ids.set(id, new Element("div", id));
    return ids.get(id);
  },
  createElement(tag) { return new Element(tag); },
};
const $ = (id) => doc.getElementById(id);
class LocalReader {
  readAsText(file) {
    this.result = file.content;
    if (this.onload) this.onload();
  }
}
const page = {
  document:doc,
  window:{confirm(){return true}, addEventListener(){}},
  Blob:globalThis.Blob,
  URL:{createObjectURL(blob){currentBlob=blob;return "blob:local-only"},
       revokeObjectURL(){}},
  FileReader:LocalReader,
  setTimeout(){},
  console,
};
vm.runInNewContext(script, page, {timeout:5000});
assert.equal($("total-queries").textContent, "0");
$("load-sample").click();
assert.equal($("total-queries").textContent, "3");
assert.equal($("total-docs").textContent, "3");
assert.equal($("total-labeled").textContent, "3");
$("export-judgments").click();
$("export-policy").click();
$("download-draft").click();
assert.equal(downloads.length, 3, "Expect three explicit local JSON downloads.");
(async()=>{
  const judgments = JSON.parse(await downloads[0].blob.text());
  assert.equal(judgments.length, 3);
  for (const q of judgments) {
    assert.deepEqual(q.retrieved_ids, [], "No fabricated retrieval results.");
    assert.ok(q.relevant_ids.length > 0);
    assert.deepEqual(Object.keys(q.relevance_grades).sort(), q.relevant_ids);
    assert.ok(q.relevant_ids.every(id=>q.relevance_grades[id]>=1));
  }
  const critical = judgments.find(q=>q.query_id==="q-privacy");
  assert.equal(critical.critical,true);
  assert.equal(critical.relevance_grades.privacy,3);
  const policy = JSON.parse(await downloads[1].blob.text());
  assert.equal(policy.version,1);
  assert.ok(policy.rules.some(rule=>rule.select.type==="critical"
      && rule.metric==="hit_at_k" && rule.min_query_score===1));
  assert.ok(policy.rules.some(rule=>rule.select.type==="category"
      && rule.select.value==="privacy"));
  const draft = JSON.parse(await downloads[2].blob.text());
  assert.equal(draft.format,"openrag-studio-draft/v1");
  assert.equal(draft.documents[0].title,"Warranty policy");
  // A duplicate document ID must not silently corrupt any saved annotation.
  $("doc-id").value="privacy";
  $("add-doc").click();
  assert.equal($("total-docs").textContent,"3");
  assert.match($("message").textContent,/Duplicate document ID/);
  // Importing the exported labeled array remains valid and deterministic.
  const file=$("dataset-file");
  file.files=[{size:100,content:JSON.stringify(judgments)}];
  file.dispatch("change");
  assert.equal($("total-queries").textContent,"3");
  assert.equal($("total-labeled").textContent,"3");
  $("export-judgments").click();
  assert.equal(downloads.length,4);
  const roundtrip=JSON.parse(await downloads[3].blob.text());
  assert.deepEqual(roundtrip,judgments);
  fs.writeFileSync("studio-judgments-smoke.json",JSON.stringify(judgments));
  fs.writeFileSync("studio-policy-smoke.json",JSON.stringify(policy));
  process.stdout.write("Studio UI smoke: synthetic load, grading, JSON/policy/draft exports, duplicate validation and round-trip passed.\n");
})().catch(error=>{console.error(error);process.exitCode=1;});
