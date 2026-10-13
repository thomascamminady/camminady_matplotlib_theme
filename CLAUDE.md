# CLAUDE.md

## Keeping the style in line with the Altair theme

This package mirrors `camminady_altair_theme`. The tokens in `Config` must keep
the names and defaults of that theme's `Config`
(`test_tokens_match_the_altair_theme` checks this against the installed
version), and the tick placement and default palette are checked against
renders by Vega (`vl-convert`). When the Altair theme changes a token, change
it here too.

The two `.mplstyle` files are generated from `Config` by `rc_params` and
`to_mplstyle`; `test_style_files_match_the_tokens` fails until they are
rewritten (see the README's Development section).

## Releasing to PyPI

Releases are published by `.github/workflows/publish.yml` when a tag starting
with `v` is pushed. Do not upload from a local machine.

```sh
uv version --bump patch   # or minor / major
git commit -am "Release X.Y.Z"
git tag -a vX.Y.Z -m "Release X.Y.Z"
git push && git push --tags
```

The workflow checks that the tag matches `version` in `pyproject.toml`, runs
pytest, then runs `uv build --no-sources` and `uv publish`. Follow it with
`gh run watch`, then confirm the upload at
https://pypi.org/pypi/camminady-matplotlib-theme/X.Y.Z/json (the project-level JSON
and page are cached and can lag behind by a few minutes).

### Trusted publishing

PyPI accepts uploads only from this workflow through trusted publishing, so no
API token is stored anywhere. The publisher registered on PyPI (project
settings → Publishing) is:

| Field       | Value                        |
|-------------|------------------------------|
| Owner       | `thomascamminady`            |
| Repository  | `camminady_matplotlib_theme` |
| Workflow    | `publish.yml`                |
| Environment | `pypi`                       |

Renaming the workflow file or the environment breaks publishing until the
publisher on PyPI is updated to match.

### Notes

- A tag only triggers a release if the commit it points to contains
  `publish.yml`.
- PyPI never accepts the same version twice, even after a release is deleted.
  If a release fails after the upload, bump the version rather than reusing it.
