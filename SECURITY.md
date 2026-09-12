# Security policy

BreedFrame is a single-user localhost prototype. It is not intended to be exposed as a network service. Model experiments are closed; security and maintenance changes can still be reviewed.

## Reporting a vulnerability

Use [GitHub private vulnerability reporting](https://github.com/lilabrooks/breedframe/security/advisories/new). Include the affected commit, reproduction steps and expected impact. Remove credentials and personal photographs from examples. Please keep vulnerability details out of public issues while they are being assessed.

Reports affecting the current public `main` branch are considered on a best-effort basis. There is no guaranteed response time or supported release schedule. Historical experiment snapshots are retained as evidence and are not maintained runtime versions.

## Maintenance boundary

Software CI and static security scanning do not validate breed accuracy. Dependency changes should pass the software checks and keep historical experiment inputs and source records identifiable. They do not automatically reopen model evaluation.
