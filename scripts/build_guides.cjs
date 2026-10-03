/* Optional publishing tool. npm install --no-save marked, or set MARKED_MODULE.
   Generated HTML is committed; no Markdown runtime is required by the demo. */
const fs = require('node:fs');
const path = require('node:path');
const { marked } = require(process.env.MARKED_MODULE || 'marked');
const root = path.join(__dirname,'..');
const files = ['README.md', ...fs.readdirSync(path.join(root,'docs')).filter(f=>f.endsWith('.md')).map(f=>'docs/'+f)];
for (const file of files) {
  const relative = file.startsWith('docs/') ? '../' : '';
  const md = fs.readFileSync(path.join(root,file),'utf8');
  const title = md.split('\n')[0].replace(/^# /,'');
  // Only trusted, repository-authored Markdown is rendered here.
  const body = marked(md).replace(/href="([^":]+)\.md(#[^"]*)?"/g,'href="$1.html$2"');
  const html = `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>${title} · BeamLab</title><link rel="stylesheet" href="${relative}web/tokens.css"><link rel="stylesheet" href="${relative}web/style.css"><link rel="stylesheet" href="${relative}web/reading.css"></head>
<body><header class="masthead"><a class="brand" href="${relative}index.html">BeamLab</a><a href="${relative}index.html#learn">Back to the interactive demo</a></header>
<main class="reading"><p class="eyebrow">BEAMLAB / PROJECT NOTES</p>${body}</main><footer class="reading-footer"><span>Mechanics, code &amp; learned models</span><a href="${path.basename(file)}" download>Download Markdown source ↓</a></footer></body></html>`;
  fs.writeFileSync(path.join(root,file.replace(/\.md$/,'.html')),html);
}
console.log(`Rendered ${files.length} readable, printable project guides.`);
