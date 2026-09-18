# ADPS Documentation

[中文文档目录](publications/zh/README.md) · [English documentation](publications/en/README.md) · [协作规范](CONTRIBUTING.zh-CN.md) · [Contributing](CONTRIBUTING.md)

This repository contains the ADPS reference code and the editable sources for the website's pattern specifications, module overviews, engineering case reports, workshops, concepts and topics. The code remains in its existing top-level directories. Website articles are maintained in `docs/publications/`.

The initial document import preserves the published website as of 18 September 2026, including its figures, citations and source dates. Nine existing Chinese case excerpts have no English counterpart yet; they are listed in `publications/catalogue.json`. This import does not replace earlier publication dates with the import date.

## Reading and Editing

- Start with the [Chinese](publications/zh/README.md) or [English](publications/en/README.md) index.
- Use the GitHub edit button to propose a change on a branch or fork, then open a pull request.
- For a question about one passage, use the discussion button on the [website](https://adpsagent.com/). A maintainer can link a public discussion to an issue and the resulting PR.
- Merging a PR accepts a revision. Publishing it is a separate step. The website links to the exact source commit it displays, not an unspecified latest version.

Most prose uses Markdown. Figures, styled tables and publication headers retain HTML where conversion would lose layout or paragraph identities. Edit their text in place; do not remove those structures just to change the format.

## Other References

- [Code interface registry](INTERFACE-REGISTRY.md)
- [Document licensing and attribution](publications/LICENSE.md)
- [Website collaboration guide](https://adpsagent.com/contribute/guide/)
