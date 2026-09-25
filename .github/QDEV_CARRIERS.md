# Private QDev CI carrier lanes

This repository runs owner-dispatched verification for selected private QDev
revisions on the same controller-managed self-hosted runner pool used by other
projects. Use these lanes when a private-repository Actions event fails before
job creation.

| Workflow | Source repository | Runner profile | Exact-SHA input |
| --- | --- | --- | --- |
| `Qalam native carrier verify` | `belilovsky/qalam` | `qdev-ci-browser` | `head_sha` |
| `QDev control plane native carrier verify` | `belilovsky/qdev-runner-control-plane` | `qdev-ci` | `head_sha` |

Each workflow fetches the requested private commit through its own repository-
scoped read-only deploy key, verifies the checked-out SHA, runs the unchanged
project CI commands, and uploads a source-bound log and identity note to the
QDev artifact store. Keys are kept only in GitHub Actions secrets, written to a
mode-0600 runner temporary file for checkout, and removed at job end.

These runs prove execution of the listed source checks on QDev infrastructure.
They do not create a private-repository GitHub check, certify a native workflow
event, provide signed controller admission, or authorize deploy, migration,
registry publication, or release acceptance. Keep those states separate in
project status records.
