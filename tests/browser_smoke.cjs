/* Optional visual/interaction checks: install playwright, or set PLAYWRIGHT_MODULE.
   On Windows this uses installed Edge; set BROWSER_CHANNEL for another browser.
   node tests/browser_smoke.cjs [URL] */
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const root = path.join(__dirname,'..');
const url = process.argv[2] || pathToFileURL(path.join(root,'index.html')).href;
(async () => {
  const browser = await chromium.launch({ channel: process.env.BROWSER_CHANNEL || 'msedge', headless:true });
  try {
    const context = await browser.newContext({ viewport:{width:1440,height:1100}, reducedMotion:'reduce', acceptDownloads:true });
    const page = await context.newPage();
    const errors = []; page.on('pageerror',e=>errors.push(e.message));
    await page.goto(url); await page.locator('#deflection').filter({hasText:'1.546'}).waitFor();
    assert.equal(await page.locator('#stress').innerText(),'16.006');
    await page.getByRole('button',{name:'Taller section',exact:true}).click();
    assert.ok(Number(await page.locator('#deflection').innerText()) < .4);
    await page.getByRole('button',{name:'Reset',exact:true}).click();
    await page.getByRole('spinbutton',{name:'Length L',exact:true}).fill('100');
    assert.match(await page.locator('#status').innerText(), /outside its training range/);
    assert.equal(await page.locator('#export').isDisabled(),true);
    assert.equal(await page.locator('#deflection').innerText(),'—');
    await page.getByRole('spinbutton',{name:'Length L',exact:true}).fill('');
    assert.match(await page.locator('#status').innerText(),/number in every field/);
    await page.getByRole('button',{name:'Reset',exact:true}).click();
    await page.getByRole('spinbutton',{name:'Length L',exact:true}).fill('200');
    await page.getByRole('spinbutton',{name:'Height h',exact:true}).fill('60');
    assert.match(await page.locator('#status').innerText(),/too short relative/);
    await page.getByRole('button',{name:'Reset',exact:true}).click();
    const slider = page.getByRole('slider',{name:'Length L slider in mm',exact:true});
    await slider.focus(); await page.keyboard.press('ArrowRight');
    assert.equal(await page.getByRole('spinbutton',{name:'Length L',exact:true}).inputValue(),'501');
    await page.getByRole('button',{name:'Reset',exact:true}).click();
    const downloadEvent = page.waitForEvent('download');
    await page.getByRole('button',{name:'Export this case ↓',exact:true}).click();
    const download = await downloadEvent;
    const exported = JSON.parse(fs.readFileSync(await download.path(),'utf8'));
    assert.equal(exported.inputs.length_mm,500);
    assert.ok(exported.neural_prediction.tip_deflection_mm>1.5);
    await page.getByRole('link',{name:'Model validation',exact:true}).click();
    assert.equal(await page.locator('#metric-rows tr').count(),4);
    assert.equal(await page.locator('#ansys-rows tr').count(),6);
    assert.equal(await page.title(),'Model validation · BeamLab');
    await page.screenshot({path:path.join(root,'reports/browser-validation.png'),fullPage:true});
    await page.getByRole('link',{name:'How it works',exact:true}).click();
    assert.equal(await page.locator('#learn').isVisible(),true);
    await page.getByRole('link',{name:'Design explorer',exact:true}).click();
    await page.getByRole('button',{name:'Reset',exact:true}).click();
    await page.screenshot({path:path.join(root,'reports/demo-desktop.png'),fullPage:true});
    await page.setViewportSize({width:390,height:844});
    for(const view of ['explore','validation','learn']) {
      await page.goto(url.split('#')[0]+'#'+view);
      const overflow = await page.evaluate(()=>document.documentElement.scrollWidth>document.documentElement.clientWidth+1);
      assert.equal(overflow,false,`Page overflow on mobile ${view}`);
    }
    await page.goto(url.split('#')[0]+'#explore');
    await page.screenshot({path:path.join(root,'reports/browser-mobile.png'),fullPage:true});
    if(url.startsWith('http')) {
      await context.setOffline(true);
      await page.getByRole('button',{name:'Taller section',exact:true}).click();
      assert.ok(Number(await page.locator('#deflection').innerText())<.4);
      await context.setOffline(false);
      const failedPage = await context.newPage();
      await failedPage.route('**/model-data.js',route=>route.abort());
      await failedPage.goto(url.split('#')[0]);
      assert.match(await failedPage.locator('#status').innerText(),/could not be loaded/);
      assert.equal(await failedPage.locator('#export').isDisabled(),true);
      await failedPage.close();
    }
    assert.deepEqual(errors,[]);
    fs.writeFileSync(path.join(root,'reports/browser-verification.json'),JSON.stringify({status:'passed',url,checks:['default inference','preset','bounds rejection','empty input','coupled domain','reset','keyboard range','JSON export','validation','learning view','390px all views','reduced motion','no page errors',...(url.startsWith('http')?['offline inference','missing model state']:[])]},null,2));
    console.log('Passed browser interactions, JSON export, keyboard, all mobile views and page-error checks.');
  } finally { await browser.close(); }
})().catch(e=>{console.error(e);process.exit(1);});
