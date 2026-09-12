# Publication readiness after cleanup

**Ready to publish as a prototype and experimentation record.** Cleanup completed on 2026-09-12 following the assessment of `2164e430544c4e3628d300100328362372da9434`. No model settings, reporting policies or saved predictions changed. No new model experiment ran.

The public repository [lilabrooks/breedframe](https://github.com/lilabrooks/breedframe) is configured as `origin`. The initial public `main` commit is `38f603877a381e73b5f1d2e3837c2d84be474350`, published from the separate, parentless `public-main` snapshot. The original local `main` history remains available privately and contains the excluded page captures.

## Resolved findings

- **The repository gate passes.** Both experiment runners were formatted after their exact measured versions were archived. Python syntax-tree comparisons found no semantic change from formatting.
- **Historical sources are recoverable and checked.** The two measured runners and original UI are in the [source archive](evidence/frozen-sources/README.md), with hashes matching their registrations. Restoring them in a disposable checkout passed both original input guards and reproduced all 26 saved new-identity case outcomes without inference. Original protocols, predictions and verification records remain unchanged. The maintained runners still reject mismatched historical sources; their guards were not bypassed.
- **Review navigation is repaired.** All 28 colon-suffixed file-line targets now use line fragments. References into formatted runners point to their archived measured versions. The final review links directly to its factual qualifications in the findings page.
- **Full external page captures are excluded.** Three complete third-party HTML pages were copied into ignored local storage and removed from the publication tree. Their hashes, source URLs and factual photo metadata remain documented. The clean publication commit has no ancestors, so the removed page contents are also absent from its history. Existing local commits were not rewritten or deleted.

## Verification

| Check | Result |
|---|---|
| `make check` | Passed: Ruff lint, formatting of 39 Python files, 33 tests and JavaScript syntax |
| Test warnings | Two dependency deprecation warnings concerning HTTPX/Starlette and AnyIO; no failures |
| Maintained versus measured runners | Both Python syntax trees identical |
| Historical restoration | Both original input guards passed; 26 saved case outcomes reproduced; zero model calls |
| Documentation | Local file targets and source-line fragments checked; no colon-suffixed targets remain |
| Git and ignore policy | Model weights, private case data, local page backups, runtime and virtual environment remain ignored; lockfile trackable |
| Publication history | Separate parentless snapshot; original history retained on local `main` |

The preceding assessment also passed the offline lockfile check and found no matches in either original commit for the checked private-key, GitHub-token, AWS-access-key and OpenAI-key patterns. The cleaned publication candidate was checked again for those patterns and excluded page contents. These are bounded checks, not a guarantee that every possible secret format is absent.

Runtime used: Python 3.11.16, Ruff 0.16.7, Node 26.8.2 and uv 0.12.13. The software gate used the existing local environment. At the initial publication assessment, no fresh-machine setup, alternate Python-version run, rendered UI check, dependency vulnerability scan or remote CI run was performed. A subsequent maintenance change added GitHub Actions CI, a security policy and repository security settings; current remote check results are recorded on GitHub. No dedicated secret scanner was installed. External links were not exhaustively revalidated.

## Publishing boundary

Initial publication used `public-main` as the source for remote `main`. Future maintenance must branch from the current remote `main` and use a pull request. A push of all local branches would expose the preserved private history and is outside this publication plan. Do not publish or merge the local historical `main` branch into the public history.

The public snapshot includes the prototype, source-photo attributions, screenshot licensing, archived measured sources and experiment records. It excludes weights, local user cases and full external page captures. This assessment is about publishing the implementation and its measured limits; it does not establish breed-report usefulness, production readiness or legal clearance for every third-party item.

Model work remains closed under the [findings and stopping decision](findings.md). Publication cleanup requires no further photo collection or inference.
