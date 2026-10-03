# GitHub Pages and portfolio integration

BeamLab is static HTML, CSS and JavaScript with embedded model weights. It
needs no build step, Supabase, API key or inference server. Relative asset paths
allow it to run at a project URL or beneath a portfolio subdirectory.

## Standalone GitHub Pages

Push this repository to GitHub, then choose **Settings → Pages → Deploy from a
branch → main → /(root)**. The `.nojekyll` file keeps the site as static files.
GitHub Pages will provide the published URL. The files are public on a public
repository; no credentials or private engineering data belong in the project.

See [GitHub's official publishing-source instructions](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site).

## Existing portfolio

Copy `index.html`, `web/`, `docs/`, `reports/metrics.json`,
`reports/test_predictions.csv`, `reports/ansys_verification.json`,
`ansys/verification.inp` and `README.md` into a public directory such as
`public/beamlab/` in a Vite portfolio. Keep their relative structure.

An ordinary “Try BeamLab” link to `/beamlab/` is the simplest option. To embed:

```html
<iframe
  src="/beamlab/"
  title="BeamLab neural-network beam design explorer"
  width="100%"
  height="1100"
  loading="lazy"
  style="border: 1px solid #ccd9e1; border-radius: 14px;"
></iframe>
<p><a href="/beamlab/">Open the full-size demo</a></p>
```

The full-size link supports smaller screens. No cross-origin messaging or
personal-data collection is necessary. Source, test dataset and Python scripts
can remain in the standalone project repository.

## Local demo and video fallback

Double-click `index.html` or serve this folder with
`python -m http.server 8765 --bind 127.0.0.1`. The demo works offline after the
files are available. Follow the 90-second script in `PORTFOLIO.md` for a video.
