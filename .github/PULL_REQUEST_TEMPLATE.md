## summary

briefly describe your change.

## type of change

- [ ] new theme
- [ ] new template/target
- [ ] bug fix
- [ ] documentation
- [ ] other

## theme checklist (if adding a theme)

- [ ] manifest at `src/themes/{artist}/{album}/theme.yaml`
- [ ] schema validated against `schemas/theme.json`
- [ ] author field matches your github username
- [ ] `cover` link provided (or spotify/wikipedia fallback)
- [ ] ran `python main.py generate` and committed output

## template checklist (if adding a template)

- [ ] jinja2 template added to `src/jukebox/templates/{category}/`
- [ ] registered in `_discoverTargets()` in `generator.py`
- [ ] extension mapping added in `_writeExact()` with `EXTENSION_MAP`
- [ ] output verified
