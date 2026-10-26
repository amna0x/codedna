# Failure-conditional conformal stopping (B12f), exploratory

Protocol: `docs/CRC_CONDITIONAL_PROTOCOL.md`, committed (76daf9f) before this
run. Command:
`OMP_NUM_THREADS=1 python scripts/run_crc_check.py <data> --conditional`.
Same four datasets as the rolling-origin study. Numbers come from
`summary.json` and the per-project JSON.

**Disclosed rerun.** The first run's `summary.md` header named the wrong
policy and protocol (a label bug in the script, no number affected). The
label was fixed (commit "CRC check: name the policy…"), the folder was
deleted, and the check was rerun. Every number was identical.

## Results

| Project | B10 safety / time | B12f safety / time | Gated product safety / time | Chosen λ per block |
|---|---|---|---|---|
| HikariCP | 0.827 / 0.339 | **1.000** / 1.000 | 1.000 / 1.000 | full, 0.01, 0.005, 0.01, 0.005 |
| jade4j | 1.000 / 0.915 | 1.000 / 0.965 | 1.000 / 0.984 | full, 0.1, full, full, full |
| LittleProxy | 0.711 / 0.913 | **1.000** / 0.998 | 1.000 / 0.998 | full, 0.02, 0.02, full, full |
| wicket-bootstrap | 0.992 / 0.941 | 0.976 / **0.774** | 0.992 / 0.941 | 0.05, 0.3, 0.5, 0.5, 0.2 |

(HikariCP's B12f time rounds to 1.000; it is 0.9995.)

- **Safety target (0.95 among failing commits):** B12f keeps it on 4 of 4
  projects, B10 on 2 of 4, and the gated product on 4 of 4.
- **B12f minus gated product**, equal project weight, 2000 draws: time
  −0.047 [−0.054, −0.040], safety −0.004 [−0.008, −0.001], recall −0.0003.
  Rule outcome: **B12f saves time**.

## Plain reading

- Bounding misses *among failing commits* fixes the weakness the first CRC
  run exposed. B12f kept 95 % commit safety on every project, which B10 did
  not.
- It is close to the gated product: as safe, and slightly cheaper. Almost
  all of the saving is on wicket-bootstrap (0.774 against 0.941 of the time),
  the one project with many failing commits. Elsewhere B12f runs nearly the
  whole suite, because 19 or more failing audit commits are needed before any
  skipping is allowed.
- So B12f replaces the ad-hoc gate with a stated, assumption-light rule that
  behaves at least as well here. It does not make test selection cheap on
  projects with few failures. Nothing could, honestly, with this little
  evidence.

## Limits

Four previously inspected projects, exploratory. Time-ordered commits are
not exchangeable. The failing-commit populations are small (5 to 137 audit
commits per block). One fit per block; the bootstrap ignores serial
dependence.
