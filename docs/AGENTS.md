# Documentation maintenance

- `publications/catalogue.json` identifies the articles maintained here and their website URLs. `CONTRIBUTING.md` and `CONTRIBUTING.zh-CN.md` are also publication sources.
- Edit article sources, not generated website HTML. A merge accepts a source revision; website publication is a separate reviewed release pinned to an exact commit.
- Update both languages when changing facts, classifications or examples. Existing missing translations are explicitly listed in the catalogue; do not silently add new exceptions.
- Preserve original publication dates, attribution, licenses and evidence links. Do not convert examples into claims of verified production outcomes.
- Explain the application, actors, inputs, decisions and results. Avoid editorial commentary that praises the explanation or announces its structure.
- Keep private correspondence, unpublished manuscripts, internal reviewer notes, personal contact details and credentials out of this public repository.
- Keep changes scoped. A documentation PR must not modify runtime code or release permissions unless those changes are explicitly requested and reviewed.
- Validate with `python docs/tooling/check.py` and `python -m unittest discover -s docs/tooling -p 'test_*.py'`.
- Imported HTML blocks preserve figures, complex tables and existing discussion anchors. Leave them intact unless changing that content is part of the request. New prose should use Markdown.
