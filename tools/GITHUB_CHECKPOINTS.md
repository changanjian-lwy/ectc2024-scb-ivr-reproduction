# GitHub experiment checkpoints

## Policy

The repository is backed up after each completed, interpretable experiment or
framework module - not after every file save. A checkpoint is created only if:

1. all Python regression tests pass;
2. the staged diff has no whitespace errors;
3. PDF sources and LTspice raw/log/db outputs remain excluded;
4. the commit has a short result-oriented message.

Run:

```sh
tools/github_checkpoint.sh "Describe the completed experiment"
```

The local post-commit hook pushes `main` automatically. The checkpoint script
also contains a push fallback for fresh clones where the hook is not installed.

## Recovery

Every successful checkpoint is an immutable Git commit. Failed simulations may
still be committed when their boundary and conclusion are documented; a
failure is a valid research result. Partially written or currently running
simulations are not checkpointed.
