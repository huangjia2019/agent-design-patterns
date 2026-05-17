# c · Progressive Discovery (placeholder)

> Column lecture **02-04** · pattern · perception × loop
>
> [中文 README](README.zh-CN.md)

## Status

Placeholder. Code and a runnable example will land alongside the publication
of lecture 02-04.

## Preview

Progressive Discovery is the agentic-search pattern. Given a codebase the
agent has never seen before, how does it go from total ignorance to "I know
which file holds the bug" without pre-embedding the whole repo? Three
phases — broad scan (grep for ~30 candidates), focused read (open ~5),
follow the chain (dependencies, tests, callers). One full forage-focus-deepen
cycle costs roughly 18K tokens on a typical 2,000-file repo.

See lecture 02-04 once published, or
[Boris Cherny's X note on why Claude Code dropped RAG for agentic search](https://x.com/bcherny/status/2017824286489383315)
for the engineering motivation.
