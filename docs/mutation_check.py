"""Mutation check for craft-ext-core: break one safety rule at a time and confirm a test fails.

Run from the repository root:  python docs/mutation_check.py [--dry]
--dry only proves each pattern occurs exactly once. A mutant counts as caught only when a test FAILED
at run time (a mutant that does not compile proves nothing). Source is restored from the text read at
the start, and the file is touched afterwards so cargo never keeps a stale mutated build.
"""
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "crates" / "ext-core" / "src"

# (label, file, exact old text, new text)
MUTANTS = [
    ("id: uppercase accepted", "id.rs", "matches!(c, 'a'..='z' | '0'..='9' | '.' | '-' | '_')", "matches!(c, 'a'..='z' | 'A'..='Z' | '0'..='9' | '.' | '-' | '_')"),
    ("id: first-party prefix needs exact match", "id.rs", ".any(|p| self.0.starts_with(p))", ".any(|p| self.0 == *p)"),
    ("id: single segment allowed", "id.rs", "if segments < 2 {", "if segments < 1 {"),
    ("path: dot segments allowed", "path.rs", 'if segment == "." || segment == ".." {', "if false {"),
    ("path: reserved device names allowed", "path.rs", "if is_reserved_device(segment) {", "if false {"),
    ("path: folder spelling collision ignored", "path.rs", "Some(seen) if *seen != prefix =>", "Some(seen) if *seen != prefix && false =>"),
    ("path: depth unchecked", "path.rs", "if depth > MAX_DEPTH {", "if false {"),
    ("path: trailing dot allowed", "path.rs", "if segment.ends_with('.') {", "if false {"),
    ("text: invisible formatting allowed", "text.rs", "} else if is_invisible_formatting(c) {", "} else if false && is_invisible_formatting(c) {"),
    ("text: control characters allowed", "text.rs", "} else if c.is_control() {", "} else if false && c.is_control() {"),
    ("version: leading zero allowed", "version.rs", "(part.len() > 1 && part.starts_with('0'))", "false"),
    ("manifest: size cap off", "manifest.rs", "if bytes.len() > MAX_MANIFEST_BYTES {", "if false {"),
    ("manifest: permissions allowed", "manifest.rs", "if !self.permissions.is_empty() {", "if false {"),
    ("manifest: hash not checked", "manifest.rs", "if !is_sha256_hex(&file.sha256) {", "if false {"),
    ("manifest: total size unchecked", "manifest.rs", "if total > limits.max_total {", "if false {"),
    ("manifest: plug-in without interface allowed", "manifest.rs", "(Kind::Plugin, None) => false,", "(Kind::Plugin, None) => true,"),
    ("manifest: url user-info allowed", "manifest.rs", " && !authority.contains('@')", ""),
    ("palette: contrast never fails", "palette.rs", "if contrast_ratio(front, back) < need {", "if contrast_ratio(front, back) < 0.0 {"),
    ("palette: dark flag unchecked", "palette.rs", "if self.dark != (self.background.luminance() < self.text.luminance()) {", "if false {"),
    ("palette: token names unchecked", "palette.rs", "if !tokens.keys().all(|name| valid_token_name(name)) {", "if false {"),
    ("index: expiry boundary", "index.rs", "if index.expires_at <= now {", "if index.expires_at < now {"),
    ("index: same version counted as rollback", "index.rs", "if index.version < newest_seen {", "if index.version <= newest_seen {"),
    ("index: duplicates allowed", "index.rs", "if !seen.insert((&entry.id, entry.version)) {", "if !seen.insert((&entry.id, entry.version)) && false {"),
    ("index: file tier allowed", "index.rs", "&& self.tier != Tier::FromFile", ""),
    ("index: revocation limit inclusive", "index.rs", "version < limit", "version <= limit"),
    ("tier: third party always admitted", "tier.rs", 'if cfg!(feature = "third-party") =>', "if true =>"),
    ("tier: reserved names open to everyone", "tier.rs", "if tier != Tier::FirstParty && id.in_first_party_namespace() {", "if false {"),
]


def main() -> int:
    dry = "--dry" in sys.argv
    originals = {}
    for label, name, old, _ in MUTANTS:
        text = (SRC / name).read_text(encoding="utf-8")
        originals.setdefault(name, text)
        count = text.replace("\r\n", "\n").count(old)
        if count != 1:
            print(f"BAD PATTERN ({count} matches): {label}")
            return 2
    if dry:
        print(f"OK: {len(MUTANTS)} patterns each match exactly once")
        return 0
    survivors = []
    for label, name, old, new in MUTANTS:
        path = SRC / name
        original = originals[name]
        normal = original.replace("\r\n", "\n")
        try:
            path.write_text(normal.replace(old, new), encoding="utf-8", newline="\n")
            run = subprocess.run(["cargo", "test", "-p", "craft-ext-core", "-j", "8", "--lib"], cwd=ROOT, capture_output=True, text=True)
            out = run.stdout + run.stderr
            if "test result: FAILED" in out:
                print(f"caught    {label}")
            elif "error[" in out or "could not compile" in out:
                print(f"NO BUILD  {label}")
                survivors.append(label)
            else:
                print(f"SURVIVED  {label}")
                survivors.append(label)
        finally:
            path.write_text(original, encoding="utf-8", newline="")
            os.utime(path, (time.time(), time.time()))
    print(f"{len(MUTANTS) - len(survivors)} of {len(MUTANTS)} caught")
    return 1 if survivors else 0


if __name__ == "__main__":
    sys.exit(main())
