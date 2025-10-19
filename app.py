import os
import sys
import subprocess
from flask import Flask, request, jsonify, render_template_string

try:
    import spacy
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "spacy"])
    import spacy

MODEL = "en_core_web_sm"
try:
    nlp = spacy.load(MODEL)
except Exception:
    subprocess.check_call([sys.executable, "-m", "spacy", "download", MODEL])
    nlp = spacy.load(MODEL)

app = Flask(__name__)

HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Named Entity Recognition (NER)</title>
<style>
body {
  min-height: 100vh;
  margin: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 1s linear;
}
.app-container {
  width: 1000px;
  min-width: 350px;
  background: #fff;
  border-radius: 20px;
  box-shadow: 0 8px 32px rgba(43,29,97,0.12);
  padding: 44px 54px 38px 54px;
  margin: 38px 0;
  display: flex;
  flex-direction: column;
  align-items: stretch;
}
h1 { margin-bottom: 12px; font-size: 2.4rem; font-family: 'Segoe UI', Arial, sans-serif; font-weight: 700; color: #253442; text-align: center; }
label { font-size: 1.08rem; margin-bottom: 11px; color: #444; }
textarea { width: 100%; min-height: 110px; padding: 14px 12px; border-radius: 10px; font-size: 1.07rem; font-family: 'Consolas', monospace; border: 1.3px solid #b6b4e6; resize: vertical; margin-bottom: 15px; }
button { background-color: #306e90; color: white; font-weight: 600; border: none; border-radius: 8px; padding: 13px 36px; cursor: pointer; margin-right: 10px; margin-bottom: 10px; transition: background 0.23s; font-size: 1.07rem; }
button:hover { background-color: #253e66; }
button.clear-btn { background-color: #e8efff; color: #105280; }
button.clear-btn:hover { background-color: #c2d9fa; }
.section { margin-top: 24px; }
.section h2 { font-size: 1.17rem; margin-bottom: 7px; color: #384171; font-weight: 700; }
.highlighted-text { background: #f9fafb; min-height: 56px; border-radius: 11px; border: 1.27px solid #cdd4f0; padding: 16px 19px 10px 19px; font-size: 1.08rem; margin-bottom: 0; word-break: break-word; }
mark.entity { font-weight: 700; border-radius: 7px; padding: 3px 13px; margin: 0 5px 5px 5px; display: inline-block; color: #293144; box-shadow: 0 1.5px 8px 0 rgba(36,60,115,0.09); transition: box-shadow .18s; }
mark.entity.PERSON    { background: #ffe3e6; }
mark.entity.ORG       { background: #b0e1fa; }
mark.entity.GPE       { background: #e6ffe7; }
mark.entity.DATE      { background: #fffbe6; }
mark.entity.PRODUCT   { background: #fff0e2; }
mark.entity.EVENT     { background: #ffe2f8; }
mark.entity.TIME      { background: #e0fff5; }
mark.entity.MONEY     { background: #ebffe0; }
mark.entity.CARDINAL  { background: #e4fdd6; }
mark.entity.ORDINAL   { background: #f1e3fc; }
mark.entity.LOC       { background: #e2f8f7; }
mark.entity.FAC       { background: #ffe9dc; }
mark.entity.LAW       { background: #eae3ff; }
mark.entity.NORP      { background: #fff2e6; }
mark.entity.QUANTITY  { background: #f7fcdd; }
mark.entity.PERCENT   { background: #dcf2ff; }
mark.entity.LANGUAGE  { background: #f3faea; }
mark.entity.WORK_OF_ART{ background: #f7eaff; }
mark.entity:hover { box-shadow: 0 0 12px 3px #89b4f199; }
.table-section { background: #f6fafe; border-radius: 10px; padding: 13px 8px 7px 8px; margin-top: 15px; }
table { width: 100%; border-collapse: collapse; font-size: 16px; background: none; }
th, td { border-bottom: 1px solid #e4ebfa; padding: 14px 10px; }
th { background-color: #e7eaff; color: #26446f; font-weight: 700; }
tr:last-child td { border-bottom: none; }
.footer { margin-top: 20px; font-size: 13px; color: #6b74a6; text-align: center; }
@media (max-width: 1100px) { .app-container { width: 94vw; min-width: unset; padding: 12vw 3vw; } }
</style>
</head>
<body>
<div class="app-container">
  <h1>Named Entity Recognition (NER)</h1>
  <label for="inputText">Type or paste your text below:</label>
  <textarea id="inputText">Barack Obama was born in Hawaii. He was the 44th President of the United States. Apple is based in Cupertino, California.</textarea>
  <div>
    <button id="analyzeBtn">Analyze</button>
    <button id="clearBtn" class="clear-btn">Clear Entities</button>
  </div>
  <div class="section">
    <h2>Highlighted output</h2>
    <div id="highlightedOutput" class="highlighted-text"></div>
  </div>
  <div class="section table-section">
    <h2>Entities</h2>
    <table>
      <thead>
        <tr><th>Entity Text</th><th>Type</th><th>Span</th></tr>
      </thead>
      <tbody id="entitiesTableBody">
        <tr><td colspan="3" style="color:#6b74a6; padding:10px;">No entities detected.</td></tr>
      </tbody>
    </table>
  </div>
  <div class="footer">
    Backend: spaCy — model: <strong>en_core_web_sm</strong>
  </div>
</div>
<script>
function entityCssClass(label) {
  return {
    PERSON: 'PERSON', ORG: 'ORG', GPE: 'GPE', DATE: 'DATE', PRODUCT: 'PRODUCT',
    EVENT: 'EVENT', TIME: 'TIME', MONEY: 'MONEY', CARDINAL: 'CARDINAL',
    ORDINAL: 'ORDINAL', LOC: 'LOC', FAC: 'FAC', LAW: 'LAW', NORP: 'NORP',
    QUANTITY: 'QUANTITY', PERCENT: 'PERCENT', LANGUAGE: 'LANGUAGE',
    'WORK OF ART': 'WORK_OF_ART'
  }[label] || '';
}
async function analyze() {
  const text = document.getElementById('inputText').value;
  const resp = await fetch('/api/ner', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({text})
  });
  if (!resp.ok) { alert('Error during analysis'); return; }
  const data = await resp.json();
  let html = '', cursor = 0;
  const ents = data.entities.sort((a,b) => a.start - b.start);
  for (const ent of ents) {
    let entClass = entityCssClass(ent.label);
    html += text.slice(cursor, ent.start) + `<mark class="entity ${entClass}">${text.slice(ent.start, ent.end)}</mark>`;
    cursor = ent.end;
  }
  html += text.slice(cursor);
  document.getElementById('highlightedOutput').innerHTML = html;

  const tbody = document.getElementById('entitiesTableBody');
  tbody.innerHTML = '';
  if (ents.length === 0) {
    tbody.innerHTML = '<tr><td colspan="3" style="color:#6b74a6; padding:10px;">No entities detected.</td></tr>';
    return;
  }
  for (const ent of ents) {
    const row = document.createElement('tr');
    row.innerHTML = `<td>${ent.text}</td><td>${ent.label}</td><td>${ent.start}–${ent.end}</td>`;
    tbody.appendChild(row);
  }
}
document.getElementById('analyzeBtn').onclick = analyze;
document.getElementById('clearBtn').onclick = function() {
  document.getElementById('inputText').value = '';
  document.getElementById('highlightedOutput').innerHTML = '';
  document.getElementById('entitiesTableBody').innerHTML = '<tr><td colspan="3" style="color:#6b74a6; padding:10px;">No entities detected.</td></tr>';
};
window.onload = analyze;

// Bright but soft visible colors
const colors = ["#a2d2ff","#ffd6a5","#fdffb6","#caffbf","#9bf6ff","#ffc6ff","#f0c9ff"];
let colorIndex = 0;
function changeBackground() {
  document.body.style.background = colors[colorIndex];
  colorIndex = (colorIndex + 1) % colors.length;
}
setInterval(changeBackground, 1000);
</script>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def home():
    return render_template_string(HTML)

@app.route("/api/ner", methods=["POST"])
def ner():
    data = request.get_json() or {}
    text = data.get("text", "")
    doc = nlp(text)
    entities = [{"text": e.text, "label": e.label_, "start": e.start_char, "end": e.end_char} for e in doc.ents]
    return jsonify({"entities": entities})

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

