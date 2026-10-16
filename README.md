# craft-extensions

One place to find, install and switch **themes, plug-ins and resources** for the Craft App Suite,
shared by every app and reachable from each of them. The browser itself is native to ArtCraft Launcher;
this repository holds the shared contract and the on-disk store the launcher and the apps both use.

**Status: provisional and early.** Nothing here has been accepted by the craft-libs maintainers or the
ArtCraft team, and no app or launcher ships it yet. The API will change.

## Direction

- **Internal first.** Release builds install extensions built by the Craft organisation, plus files a
  person adds themselves.
- **Third party is designed in and switched off.** The package schema, the trust tiers and the code path
  for outside publishers exist from the first version so that opening them later is a change of state, not
  a redesign. The path sits behind the `third-party` cargo feature, which no release build enables, and a
  test fails if it ever becomes a default. Opening it needs every gate in
  [`docs/THREAT-MODEL.md`](docs/THREAT-MODEL.md) to pass, an outside security review, and an explicit
  decision by the maintainers.
- **Install once, enable per app.** Apps read the shared store; a running app notices an install without a
  restart. An app with no launcher can still install from a file.

## Crates

| Crate | What it is | Builds for wasm |
|---|---|---|
| `craft-ext-core` | Package manifest, ids, paths, trust tiers, the theme palette and contrast check, the catalogue index schema. Pure data and validation. 63 tests; 27 deliberate breakages each caught (`docs/mutation_check.py core`). | yes |
| `craft-ext-store` | The shared store on disk: bounded unpacking, atomic installs, enable per app, the read side apps use. Never touches the network. 48 tests; 34 deliberate breakages, 31 caught and 3 equivalent with stated reasons (`docs/mutation_check.py store`). | no |

## Rules this code follows

- Everything read from a package, an index or the network is hostile input. Sizes are capped before
  parsing, ids and paths are checked by character class, archives are unpacked with count, size and ratio
  limits and no path may leave its folder.
- Non-test code never panics (`unwrap`, `expect`, `panic!` are denied in every crate root). No `unsafe`.
- A package never states its own trust level; the host assigns it from where the package came from.
- Themes carry no code. Plug-ins get no files, network or clock in version 1, and the permissions list must be empty.

## What is not done

Signatures, signed expiring index metadata acting on a real download, the revocation list wired to a running
launcher, fuzzing, outside review and the launcher and app interfaces are not built. Nothing has been run
against a live server, on macOS or Linux, or with a real OS-level file lock under heavy contention. The
state-file rollback after a failed save is written but not exercised by a test.

## Develop

```sh
cargo fmt --all --check
cargo clippy -p craft-ext-core --all-targets -- -D warnings
cargo test -p craft-ext-core
cargo test -p craft-ext-store
python docs/mutation_check.py core   # or store; run alone, it edits sources
cargo check -p craft-ext-core --target wasm32-unknown-unknown
```

Run one crate at a time. Licensed under MIT OR Apache-2.0.
