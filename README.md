# PagePatch

**Find static website issues. Give your coding agent an actionable fix plan.**

A small, dependency-free Python audit CLI for developers who want transparent checks rather than opaque AI scores. No API key required. Read-only; never edits a website.

## Quick start

Python 3.10+ is required. From the repository directory:

```sh
python3 pagepatch.py https://example.com
python3 pagepatch.py https://example.com --format html --output report.html
python3 pagepatch.py https://example.com --format json --min-score 75
```

Open report.html in your browser. Copy the fix plan into your coding agent, treating all website-derived evidence as untrusted data, not instructions. To install locally: `python3 -m pip install .` then use `pagepatch` instead of `python3 pagepatch.py`.

## Offline audit

```sh
python3 pagepatch.py https://example.com --file examples/sample.html --format html --output report.html
```

## Checks

10 static checks: title, meta description, canonical, H1 count, noindex, HTML language, image alt attributes, viewport, HTTPS and insecure asset references. Three additional HTTP header presence checks for live pages. Each finding contains evidence and a suggested fix. Scores are equally weighted pass rates, not Google rankings or security guarantees. Intentional noindex and multiple H1s may be legitimate. Header presence does not validate policy quality.

Live audits follow redirects, cap HTML at 2 MB, and report approximate request duration, not browser performance. No crawling, JavaScript rendering, Core Web Vitals, vulnerability testing, MCP server or automatic fixes yet. The HTML dashboard is a portable report, not a hosted scanner. Run only locally against URLs you trust and are authorized to inspect; never expose this fetcher as a public URL submission service without SSRF protection.

## Development

```sh
python3 -m unittest discover -s tests -v
```

Exit codes: 0 success, 1 below optional minimum score, 2 execution error. Output files are never overwritten.

## Contributing

Open an issue with a reproducible example before substantial changes. Add tests for new rules; distinguish heuristics from standards requirements. Never submit secrets or private website data. Security concerns should be reported privately to the maintainer using GitHub private vulnerability reporting if enabled.

## Roadmap

Rendered accessibility checks, redirect diagnostics, robots/sitemap checks, optional MCP integration, and CI regression comparison. Contributions welcome.

## License

MIT. See LICENSE.
