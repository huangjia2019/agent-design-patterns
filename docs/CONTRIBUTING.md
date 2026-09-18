# Document Collaboration and Publishing

ADPS maintains pattern specifications, module overviews, case reports, workshop records, concepts and topics in this repository. Readers can suggest changes to individual passages on the website or edit these documents through a pull request (PR).

## Propose a Change

1. Find the article in the [documentation index](publications/en/README.md) and use GitHub's edit button. Contributors without write access can submit from a fork.
2. Edit the relevant passage. Technical additions should explain the use case, mechanism and limits, with sources that can be shared publicly. A typo fix needs only a short explanation.
3. Check the Chinese counterpart. Update both languages when facts, classifications or examples change. A language-specific correction can leave the other version unchanged; explain this in the PR.
4. Open a PR describing the reason, affected articles and verification. Link the original website discussion when applicable.

For example, a reader may point out that approval should expire when tool arguments change. The proposed revision should specify which fields approval covers, what is checked when execution resumes, and which changes require fresh approval. Reviewers can then assess a concrete design.

## Review and Acceptance

Domain reviewers assess the technical claims and evidence. Jia Huang approves changes to the text. Automated checks cover files, references, figures and language pairs; they do not establish technical correctness. Expert-group membership does not grant merge or deployment rights.

Approval applies to a specific PR revision. Further edits require a new review. A merged revision becomes the accepted source, but may not yet be published on the website.

## Website Publication

The publisher selects an exact source commit and builds a preview. After checking both languages, figures, links and discussion anchors, Jia Huang approves publication. A separate website PR carries the generated pages. The source commit, website commit and release tag are recorded after successful deployment and live verification.

The website's "Published source" link identifies the exact commit used for that page. "Edit source" opens the maintained main branch. Accepted revisions can be ahead of the website, but the website does not maintain a separate editable article. Emergency corrections also start in the source documents.

## Website Discussions

Approving a discussion makes that comment public; it does not accept an article revision. Maintainers link public suggestions that need text changes to GitHub issues, then address them through PRs. The issue preserves the original page, passage and revision so a suggestion cannot silently attach to different text.

Unpublished submissions, raw chats, private review notes, personal contact details and unapproved material stay out of this public repository. If a published comment is withdrawn, contact the maintainer about its linked issue as well.

## Files and Credit

- Articles: `docs/publications/en/` and `docs/publications/zh/`.
- Figures: `docs/publications/assets/`. Preserve attribution and exclude credentials, customer data and private screenshots.
- Article-to-page mapping: `docs/publications/catalogue.json`.
- Existing authors and sources remain in the articles. New contributions are recorded in PRs, commits and release notes. Import dates do not replace original publication dates.
- Code retains the root license. Documents and third-party figures retain their [document licensing terms](publications/LICENSE.md) and existing notices.

Code and documents share a repository, not a change scope. A text-only PR should not modify runtime code, tests or deployment settings. Contributors using an agent to draft changes remain responsible for checking facts, sources and the scope of the diff.
