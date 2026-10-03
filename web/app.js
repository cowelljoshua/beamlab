"use strict";
(() => {
  const $ = id => document.getElementById(id);
  const model = globalThis.BEAM_MODEL, report = globalThis.BEAM_REPORT;
  const fields = [
    { name: "Length L", unit: "mm", min: 200, max: 1000, step: 1, value: 500 },
    { name: "Width b", unit: "mm", min: 15, max: 60, step: 1, value: 30 },
    { name: "Height h", unit: "mm", min: 10, max: 60, step: 1, value: 25 },
    { name: "Young’s modulus E", unit: "GPa", min: 69, max: 210, step: 1, value: 69 },
    { name: "Tip force F", unit: "N", min: 10, max: 500, step: 1, value: 100 }
  ];
  let current = null;
  const format = (v, places = 3) => Number(v).toLocaleString("en-US", { minimumFractionDigits: places, maximumFractionDigits: places });
  function el(tag, props = {}, text) {
    const node = document.createElement(tag);
    Object.entries(props).forEach(([k,v]) => node.setAttribute(k,v));
    if (text !== undefined) node.textContent = text;
    return node;
  }
  function status(text, warning = false) { $("status").textContent = text; $("status").classList.toggle("warning", warning); }
  function navigate() {
    const requested = location.hash.slice(1), view = ["explore", "validation", "learn"].includes(requested) ? requested : "explore";
    document.querySelectorAll(".view").forEach(n => { n.hidden = n.id !== view; });
    document.querySelectorAll(".nav a").forEach(n => { if (n.hash === `#${view}`) n.setAttribute("aria-current", "page"); else n.removeAttribute("aria-current"); });
    document.title = { explore: "Explore the beam", validation: "Model validation", learn: "How it works" }[view] + " · BeamLab";
  }
  addEventListener("hashchange", navigate); navigate();
  if (!model || !report || !globalThis.BeamCore) {
    status("Model files could not be loaded. Keep the web folder beside index.html, then reload the page.", true);
    $("ansys-summary").textContent = "Model files unavailable. Restore the web folder and reload.";
    return;
  }
  fields.forEach((f, i) => {
    const group = el("div", { class: "input-group" });
    const top = el("div", { class: "input-top" });
    top.append(el("label", { for: `value-${i}` }, f.name));
    const numberWrap = el("div", { class: "input-number" });
    const number = el("input", { id: `value-${i}`, type: "number", min: f.min, max: f.max, step: "any", value: f.value, "aria-describedby": `limits-${i} status` });
    numberWrap.append(number, el("span", {}, f.unit)); top.append(numberWrap);
    const range = el("input", { id: `range-${i}`, type: "range", min: f.min, max: f.max, step: f.step, value: f.value, "aria-label": `${f.name} slider in ${f.unit}`, "aria-describedby": `limits-${i} status` });
    const limits = el("div", { class: "limits", id: `limits-${i}` }); limits.append(el("span", {}, `${f.min} ${f.unit}`), el("span", {}, `${f.max} ${f.unit}`));
    range.addEventListener("input", () => { number.value = range.value; update(); });
    number.addEventListener("input", () => { if (number.value !== "") range.value = number.value; update(); });
    group.append(top, range, limits); $("inputs").append(group);
  });
  $("inputs").addEventListener("submit", e => e.preventDefault());
  function setValues(values) {
    values.forEach((v,i) => { $(`value-${i}`).value = v; $(`range-${i}`).value = v; }); update();
  }
  $("reset").addEventListener("click", () => setValues(fields.map(f => f.value)));
  $("stiffer").addEventListener("click", () => setValues([500,30,40,69,100]));
  $("flexible").addEventListener("click", () => setValues([800,30,25,69,100]));
  function update() {
    const shown = fields.map((f,i) => $(`value-${i}`).value === "" ? NaN : Number($(`value-${i}`).value));
    const x = shown.map((v,i) => i === 3 ? v * 1000 : v);
    const problem = BeamCore.domain(x, model);
    fields.forEach((f,i) => $(`value-${i}`).setAttribute("aria-invalid", String(!Number.isFinite(shown[i]) || shown[i] < f.min || shown[i] > f.max)));
    current = null; $("export").disabled = !!problem;
    if (problem) {
      status(problem + " Neural prediction withheld.", true);
      ["deflection", "stress", "deflection-error", "stress-error", "deflection-reference", "stress-reference"].forEach(id => $(id).textContent = "—");
      if (x.every(v => Number.isFinite(v) && v > 0)) {
        const y = BeamCore.reference(x);
        $("deflection-reference").textContent = format(y[0]) + " mm";
        $("stress-reference").textContent = format(y[1]) + " MPa";
      }
      $("beam-svg").style.opacity = ".35";
      return;
    }
    $("beam-svg").style.opacity = "1";
    const predicted = BeamCore.predict(x, model).values, exact = BeamCore.reference(x);
    current = { inputs: Object.fromEntries(model.features.map((k,i) => [k,x[i]])), neural_prediction: Object.fromEntries(model.outputs.map((k,i) => [k,predicted[i]])), equation_reference: Object.fromEntries(model.outputs.map((k,i) => [k,exact[i]])), relative_error_pct: predicted.map((v,i) => Math.abs(v / exact[i] - 1) * 100), scope: "Educational surrogate; synthetic Euler-Bernoulli training data; not a design approval." };
    ["deflection", "stress"].forEach((name,i) => {
      $(name).textContent = format(predicted[i]);
      $(`${name}-reference`).textContent = format(exact[i]) + (i ? " MPa" : " mm");
      $(`${name}-error`).textContent = format(current.relative_error_pct[i],2) + "%";
    });
    status(`Within training envelope · L/h = ${format(x[0]/x[2],1)} · reference δ/L = ${format(exact[0]/x[0]*100,2)}%. This is not a strength check.`);
    drawBeam(x, predicted[0]);
  }
  function drawBeam(x, delta) {
    const depth = 12, thickness = 12 + x[2] * .35, bend = Math.min(60, 10 + delta * 7);
    const top = [], bottom = [], behind = [], center = [];
    for (let i = 0; i <= 40; i++) {
      const t = i / 40, px = 124 + 510*t, py = 156 + bend*t*t*(3-t)/2;
      top.push([px,py-thickness/2]); bottom.push([px,py+thickness/2]); behind.push([px+depth,py-thickness/2-depth]); center.push([px,py]);
    }
    const path = points => points.map((p,i) => (i ? "L" : "M") + p.join(",")).join(" ");
    $("beam-front").setAttribute("d", path([...top,...bottom.reverse()]) + "Z");
    $("beam-top").setAttribute("d", path([...top,...behind.reverse()]) + "Z");
    $("deflected").setAttribute("d", path(center));
    $("load-arrow").setAttribute("d", `M634 92V${156+bend-thickness/2-5}`);
    $("load-label").textContent = `${format(x[4],0)} N`;
    $("length-label").textContent = `L = ${format(x[0],0)} mm`;
    $("section-label").textContent = `b × h = ${format(x[1],1)} × ${format(x[2],1)} mm`;
  }
  $("export").addEventListener("click", () => {
    if (!current) return;
    const url = URL.createObjectURL(new Blob([JSON.stringify(current,null,2)], {type:"application/json"}));
    const link = el("a", {href:url,download:"beamlab-case.json"}); document.body.append(link); link.click(); link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    status("Case exported with inputs, predictions, reference values and scope notes.");
  });
  function row(target, cells) { const tr = el("tr"); cells.forEach((v,i) => tr.append(el(i ? "td" : "th", i ? {} : {scope:"row"}, String(v)))); $(target).append(tr); }
  model.outputs.forEach((name,i) => {
    ["neural_network", "linear_baseline"].forEach(key => {
      const m = report[key][name]; row("metric-rows",[(i ? "Stress" : "Deflection") + " · " + (key === "neural_network" ? "neural network" : "linear baseline"),format(m.mape_pct,2)+"%",format(m.p95_ape_pct,2)+"%",format(m.max_ape_pct,2)+"%",format(m.r2,5)]);
    });
  });
  $("headline-error").textContent = format(report.neural_network.tip_deflection_mm.mape_pct,2) + "%";
  $("learning-summary").textContent = `Saved epoch ${report.selected_epoch} · MSE in standardized log targets · logarithmic y-axis`;
  function svgNode(tag, attrs, text) { const n = document.createElementNS("http://www.w3.org/2000/svg",tag); Object.entries(attrs).forEach(([k,v]) => n.setAttribute(k,String(v))); if(text !== undefined)n.textContent = text; return n; }
  const colors = getComputedStyle(document.documentElement);
  const color = key => colors.getPropertyValue(`--color-${key}`).trim();
  function chartBase(id, xLabel, yLabel, maxX, minY, maxY, logY=false) {
    const svg = $(id), x = v => 65 + v/maxX*510, y = v => 220 - ((logY ? Math.log10(v) : v)-minY)/(maxY-minY)*180;
    for(let i=0;i<=4;i++) {
      const val = minY+(maxY-minY)*i/4, py = 220-i*45;
      svg.append(svgNode("line",{x1:65,y1:py,x2:575,y2:py,stroke:color("line")}));
      svg.append(svgNode("text",{x:55,y:py+4,"text-anchor":"end",fill:color("muted"),"font-size":11},logY ? (10**val).toExponential(0) : format(val,1)));
      svg.append(svgNode("text",{x:x(maxX*i/4),y:240,"text-anchor":"middle",fill:color("muted"),"font-size":11},format(maxX*i/4,0)));
    }
    svg.append(svgNode("text",{x:320,y:264,"text-anchor":"middle",fill:color("muted"),"font-size":12},xLabel));
    svg.append(svgNode("text",{x:65,y:22,fill:color("muted"),"font-size":12},yLabel));
    return {svg,x,y};
  }
  const losses = report.history.flatMap(h=>[h.train_loss,h.val_loss]);
  const c = chartBase("loss-chart","Epoch","Loss",report.epochs_run,Math.floor(Math.log10(Math.min(...losses))),Math.ceil(Math.log10(Math.max(...losses))),true);
  ["train_loss","val_loss"].forEach((key,i) => c.svg.append(svgNode("path",{d:report.history.map((h,j)=>(j?"L":"M")+c.x(h.epoch)+","+c.y(h[key])).join(" "),fill:"none",stroke:color(i?"accent":"primary"),"stroke-width":2,"stroke-dasharray":i?"5 3":"none"})));
  const limit = Math.ceil(Math.max(...report.scatter.flatMap(p=>[p.reference[0],p.prediction[0]])));
  const s = chartBase("scatter-chart","Equation reference (mm)","Neural prediction (mm)",limit,0,limit);
  s.svg.append(svgNode("line",{x1:s.x(0),y1:s.y(0),x2:s.x(limit),y2:s.y(limit),stroke:color("accent"),"stroke-dasharray":"5 4"}));
  report.scatter.forEach(p => s.svg.append(svgNode("circle",{cx:s.x(p.reference[0]),cy:s.y(p.prediction[0]),r:2.6,fill:color("primary"),opacity:.65})));
  const ansys = globalThis.BEAM_ANSYS;
  if(ansys?.status === "completed") {
    $("ansys-badge").textContent = `${ansys.solves} solves completed`;
    $("ansys-summary").textContent = `Six independent cases, each solved with 4, 8 and 16 elements. Largest deflection difference from the equation: ${format(ansys.max_deflection_vs_equation_pct,3)}%. Reaction forces were also checked.`;
    ansys.rows.filter(r=>r.elements===16).forEach(r=>row("ansys-rows",[r.case,format(r.ansys_deflection_mm,5),format(r.reference[0],5),format(r.neural[0],5),format(r.neural_vs_ansys_pct[0],2)+"%"]));
  } else { $("ansys-badge").textContent = "Not available"; $("ansys-summary").textContent = "No completed ANSYS verification report was loaded. The neural-network evaluation remains available above."; }
  update();
})();
