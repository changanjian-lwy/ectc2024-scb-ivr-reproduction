# LTspice launcher

Use `ltspice_runner.sh` instead of macOS `open -a LTspice` or launching the
application executable with `-b`. The application bundle does not register
`.cir`/`.net` document types, and its wrapper can pass only the basename into
the Windows working directory. That produces the misleading Windows-program
or unable-to-open-file dialogs.

```bash
./tools/ltspice_runner.sh run /absolute/path/to/model.cir
./tools/ltspice_runner.sh open /absolute/path/to/model.cir
```

`run` performs a batch simulation and waits for completion. `open` displays
the netlist in LTspice without relying on Finder file associations.
