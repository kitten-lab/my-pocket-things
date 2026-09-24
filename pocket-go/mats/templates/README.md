# Pocket Go thin templates

Boring layout skeletons. Each template is a folder with:

- `_shell.md` — HTML skeleton using class tokens + `{{paper}}` / `{{navbar}}` / `{{title}}` / `{{home}}`
- `base.css` — layout rules ONLY using CSS variables from `:root` (no hex in layout rules)

## Templates

| id | title | description |
|----|-------|-------------|
| blank | Blank | Minimal shell: just `{{paper}}` |
| stack | Header+nav | Header + navbar + body + footer |
| rail-left | Sidebar left | Header/footer + left sidebar + paper |
| rail-right | Sidebar right | Header/footer + right sidebar + paper |

## Apply

BIOS: New host → pick template, or Shell face → Apply template… (overwrite / fork / cancel).

API:

- `GET /api/templates` → `{id,title,description}[]`
- `POST /api/templates/apply` body `{pocket, template, mode: "new"|"overwrite"|"fork", env?}`

Do not hand-edit dramatic coats (Parabola etc.) — fork instead.
