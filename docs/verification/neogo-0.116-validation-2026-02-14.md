# NeoGo 0.116 TRY Delta Verification Snapshot (2026-02-14)

This note captures a point-in-time verification run for the known NeoGo TRY control-flow deltas.

## Release/version status

- Date checked: 2026-02-14
- NeoGo latest GitHub release: `v0.116.0` (published 2026-01-21)
- Release URL: https://github.com/nspcc-dev/neo-go/releases/tag/v0.116.0

## Public endpoint useragents checked

All tested public NSPCC endpoints reported `/NEO-GO:0.116.0/`:

- `http://rpc1.n3.nspcc.ru:10332`
- `http://rpc2.n3.nspcc.ru:10332`
- `http://rpc3.n3.nspcc.ru:10332`
- `http://rpc4.n3.nspcc.ru:10332`
- `http://rpc5.n3.nspcc.ru:10332`
- `http://rpc6.n3.nspcc.ru:10332`
- `http://rpc7.n3.nspcc.ru:10332`
- `http://rpc.t5.n3.nspcc.ru:20332` (TestNet)

## TRY delta probe

A targeted 4-vector probe was run for:

- `TRY_no_exception`
- `TRY_with_throw_catch`
- `TRY_L_no_exception`
- `TRY_finally_no_exception`

Results:

- C# reference (`http://seed1.neo.org:10332`): `4 passed / 0 failed`
- NeoGo endpoints above: `0 passed / 4 failed` on every endpoint

## Conclusion

As of 2026-02-14, the known NeoGo TRY divergence remains reproducible across public MainNet and TestNet NeoGo 0.116 endpoints. Keep `docs/verification/neogo-0.116-known-deltas.txt` in compatibility gates until upstream behavior changes.
