# LingTai release log template

Use this template before publishing a LingTai release log. It exists to prevent
three repeated mistakes: publishing to the wrong surface, omitting release-window
statistics, and dropping contributors whose issue/PR did not ship.

## Publish destination checklist

Current canonical website destination:

- repo: `lingtai-web`
- source file: `src/data/releases.ts`
- renderer: `src/components/ReleaseDetail.astro`
- generated live pages:
  - `https://lingtai.ai/zh/releases/<id>/`
  - `https://lingtai.ai/en/releases/<id>/`
  - `https://lingtai.ai/wen/releases/<id>/`
  - `https://lingtai.ai/releases/<id>/`
- index pages to verify:
  - `https://lingtai.ai/zh/releases/`
  - `https://lingtai.ai/en/releases/`

Do **not** use `src/content/blog/release-day-*.md` as the release log. A blog post
can be a companion only if the current website structure explicitly calls for it.

## Required statistics block

Fill these fields before drafting prose. Use `TBD` only while still gathering
facts; never publish with `TBD`.

```text
Release id: <YYYYMMDD-N>
Date: <YYYY-MM-DD>
Public versions: <Kernel vX.Y.Z · TUI/Portal vA.B.C>
Repos covered: <repo list>
Tag/range stats:
  - <repo>: <base>..<head>; <commit_count> commits; <merged_pr_count> merged PRs;
    <issue_count> issue records in the release window; <files_changed> files;
    +<insertions> / -<deletions> lines
Combined totals:
  - commits: <N>
  - merged PRs: <N>
  - issue records: <N> (<date/window and query basis>)
  - files changed: <N>
  - insertions/deletions: +<N> / -<N>
  - net lines: <+/-N>
Contributor evidence classes:
  - commit authors/co-authors
  - merged PR authors
  - rejected/closed/unmerged PR authors
  - issue authors/reporters, including rejected/closed/duplicate/not-planned items
  - reviewers/commenters/maintainers with substantive release-window participation
Validation:
  - <gate>: <result>
Links:
  - <GitHub release / tag / PyPI / Homebrew / commit / compare / live page>
```

## Collection commands

Use exact ranges from the release plan. Examples:

```bash
git -C <repo> log --oneline <base>..<head> | wc -l
git -C <repo> diff --shortstat <base>..<head>

gh pr list --repo <org/repo> --state all \
  --search 'updated:YYYY-MM-DD..YYYY-MM-DD' \
  --limit 500 --json number,title,state,author,createdAt,updatedAt,closedAt,mergedAt,url

gh issue list --repo <org/repo> --state all \
  --search 'updated:YYYY-MM-DD..YYYY-MM-DD' \
  --limit 500 --json number,title,state,author,createdAt,updatedAt,closedAt,url
```

State the query basis in the release log when issue counts come from a tracker
window rather than strict tag ancestry.

## `src/data/releases.ts` entry skeleton

```ts
const vX_Y_Z_kernel_vA_B_C_tui: Release = {
  id: '<YYYYMMDD-N>',
  version: 'Kernel vX.Y.Z · TUI/Portal vA.B.C',
  titleEn: '<short release title>',
  titleZh: '<中文标题>',
  date: '<YYYY-MM-DD>',
  pkg: 'LingTai kernel + TUI/Portal',
  tag: 'kernel vX.Y.Z · tui vA.B.C',
  install: 'brew update && brew upgrade lingtai-ai/lingtai/lingtai-tui && python -m pip install --upgrade lingtai==X.Y.Z',
  runtimeNoteEn: '<refresh / migration / compatibility note>',
  runtimeNoteZh: '<中文运行时说明>',
  summaryEn: '<include headline outcome and totals>',
  summaryZh: '<中文摘要，也包含统计口径>',
  features: [
    {
      titleEn: 'Release window at a glance',
      titleZh: '发布窗口概览',
      leadEn: '<N commits, M PRs, K issues, files and line counts>',
      leadZh: '<中文统计概览>',
      bulletsEn: [
        '<repo A stats: commits, PRs, issues, files, +insertions/-deletions>',
        '<repo B stats: commits, PRs, issues, files, +insertions/-deletions>',
      ],
      bulletsZh: [
        '<中文 repo A 统计>',
        '<中文 repo B 统计>',
      ],
      whyEn: '<why this window matters>',
      whyZh: '<中文说明>',
    },
  ],
  contributors: ['<human1>', '<human2>'],
  validation: {
    commit: '<primary commit/tag refs>',
    items: [
      { label: 'Release-window totals', result: '<commits; PRs; issues; files; +insertions/-deletions>' },
      { label: '<gate>', result: '<passed / link / evidence>' },
    ],
  },
  links: [
    { label: '<release/link label>', href: '<url>' },
  ],
};
```

Before pushing, prepend the new constant to `export const releases` and run the
site build. After pushing to GitHub, wait for automatic deploy and verify both the
detail pages and release index pages live.
