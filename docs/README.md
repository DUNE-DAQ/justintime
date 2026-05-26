# Just in time

Just in time provided a data visualisation project for DUNE exactly when it was needed. Although it worked, it was a small scaled project with no expansion capabilities, and an expandable version of the project was by now long overdue. "It's about time" aims to provide an implementation of the Just in time functionality with code that's easily expandable and much more robust file structure.

## Quick start

### Dev area setup
To use `justintime`, you should first setup up a DUNE DAQ work area. You can follow the instructions in the [DUNE DAQ wiki](https://dune-daq-sw.readthedocs.io/en/latest/packages/daq-buildtools/) to do so. Then, to set up `justintime`:
```
cd $DBT_AREA_ROOT  # Assumes you've set up your work area's environment

# justintime depends on dqmtools
git clone https://github.com/DUNE-DAQ/dqmtools.git
cd dqmtools
pip install -e .
cd ..

git clone https://github.com/DUNE-DAQ/justintime.git
cd justintime
pip install -e .
cd ..
```

### Running Just-in-Time
To run `justintime`, you need a directory containing HDF5-format DUNE DAQ data files and a TPC channel map name. The channel map is passed with the `--tpc-channel-map` flag:
```
python -m justintime.app --tpc-channel-map <CHANNEL_MAP_NAME> <DATA_FOLDER_PATH>
```
For example, for ProtoDUNE-HD:
```
python -m justintime.app --tpc-channel-map PD2HDTPC /path/to/data
```
Known working channel map names (passed without the trailing `ChannelMap` suffix, which is appended automatically): `PD2HDTPC`, `PD2VDTPC`. Run `python -m justintime.app --help` for the full list of options.

Additional options:
| Option | Default | Description |
|---|---|---|
| `--tpc-channel-map` | *(required)* | TPC channel map name |
| `--pds-channel-map` | `SimplePDS` | PDS channel map name |
| `-p` / `--port` | `8001` | Port to serve on |
| `--template` | `flatly` | UI theme: `flatly` (light) or `darkly` (dark) |
| `-v` / `--verbose` | off | Enable debug logging |

By default, this will run `justintime` on port 8001. Navigate to `localhost:8001` in a web browser to view the monitoring page. If running `justintime` on a remote host and you want to open the browser on your local machine, you must first set up an ssh tunnel via
```bash
ssh -KL 8001:<hostname>:8001 <username>@<hostname> -N
```
where `hostname` and `username` are the names of the host machine on which `justintime` is running and the user running it. If you're not sure, run `hostname` and `whoami` in a terminal on the remote host.
