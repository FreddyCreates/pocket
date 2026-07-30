# Two products (do not mix)

## Founder POCKET (yours)

- Every founder has **their** install on **their** machine.
- Full **local** PC access + **virtual** space.
- Desktop embodiment, shell, capture = this edition only.
- Shortcut: **POCKET Owner**.

## Market POCKET (customers)

- Random users / paid users / invite funnel.
- They also get **local + virtual** — but **theirs**:
  - Virtual explorer: `~/.pocket/tenants/<user>/files`
  - Local sandbox: `~/.pocket/tenants/<user>/local`
  - Git / projects / deliverables under the same tree
- **Never** founder OneDrive, Parallax, pocket-os checkout, or operator desktop.
- Invite = marketing + seat mint, **not** “here are my files.”

## Hard rule

```text
Market job cwd  ⊂  ~/.pocket/tenants/<that_user>/
Market never resolves into founder deny list
Founder job cwd  =  real host product paths
```

APIs:

| | Founder | Market |
|--|---------|--------|
| Agents on their files | yes (host) | yes (tenant) |
| `/v1/space` | n/a (use host paths) | list/read/write their space |
| `/v1/desktop` | yes | **403** |
| Shared project / git | vault | their `git/` + projects |

## What the public URL is for

Marketing, download, **Create my seat** with invite — **not** a tour of the founder laptop.
