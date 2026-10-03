const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const root = path.join(__dirname, '..');
const model = JSON.parse(fs.readFileSync(path.join(root,'artifacts/model.json')));
const report = JSON.parse(fs.readFileSync(path.join(root,'reports/metrics.json')));
const core = require('../web/core.js');
let largestDifference = 0;
for (const sample of report.parity_samples) {
  const out = core.predict(sample.x,model).values;
  out.forEach((v,i) => {
    largestDifference = Math.max(largestDifference, Math.abs(v-sample.y[i]));
    assert.ok(Math.abs(v-sample.y[i]) < 1e-9, 'JS inference must agree with NumPy');
  });
}
assert.deepEqual(core.reference([500,30,25,69000,100]), [1.5458937198067633,16]);
for (const bad of [[NaN,30,25,69000,100],[100,30,25,69000,100],[200,30,60,69000,100],[1000,15,10,69000,500]]) {
  assert.ok(core.domain(bad,model));
  assert.throws(()=>core.predict(bad,model));
}
require('../web/model-data.js');
require('../web/report-data.js');
assert.deepEqual(globalThis.BEAM_MODEL,model);
assert.deepEqual(globalThis.BEAM_REPORT,report);
console.log(`Passed: 32 NumPy/JavaScript parity cases; maximum absolute difference ${largestDifference}; invalid-domain rejection; embedded-artifact consistency.`);
