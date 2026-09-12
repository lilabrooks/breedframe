# Offline ViT processor fixture

`preprocessor_config.json` is a reformatted copy from
[`wesleyacheng/dog-breeds-multiclass-image-classification-with-vit`, revision `160ee8611d7974c550bbaaa108378fbe8be9ef9c`](https://huggingface.co/wesleyacheng/dog-breeds-multiclass-image-classification-with-vit/blob/160ee8611d7974c550bbaaa108378fbe8be9ef9c/preprocessor_config.json).
The model card declares MIT. Model and image notices are in
[THIRD_PARTY_NOTICES.md](../../../THIRD_PARTY_NOTICES.md).

| File | SHA-256 |
|---|---|
| Downloaded source | `a34861a24e781942424ad790b82bc99348404a2e64ea882de88c40905851698d` |
| Reformatted test fixture | `6bec8a158814f734fff770ffa16fd6709cc3ef539269f1dfc3fceff68eb0b8bf` |

Both JSON objects matched on 2026-09-12. Online setup runs
`scripts/check_processor.py` immediately after downloading the pinned classifier.
It compares every JSON field, ignores formatting, and fails on drift. The same
command can be run locally after setup, with an optional model-directory argument.
Required tests use only this committed configuration and generated weights.

When changing the model revision, review the downloaded configuration, update this
provenance and the normalization expectations together, and rerun both the offline
tests and an installed-checkpoint smoke check. Copying the new fixture alone does
not verify preprocessing behavior.
