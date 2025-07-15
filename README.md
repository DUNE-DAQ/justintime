# Just in time

Just in time provided a data visualisation project for DUNE exactly when it was needed. Although it worked, it was a small scaled project with no expansion capabilities, and an expandable version of the project was by now long overdue. "It's about time" aims to provide an implementation of the Just in time functionality with code that's easily expandable and much more robust file structure.

## Quick start

### Dev area setup
To use `justintime`, you should first setup up a DUNE DAQ environment. You can follow the instructions in the [DUNE DAQ wiki](https://dune-daq-sw.readthedocs.io/en/latest/packages/daq-buildtools/) to do so. 
```
dbt-create -n <nightly_tag> my_dev_area
cd my_dev_area/
source env.sh
```
Then, to set up `justintime`,
```
git clone https://github.com/DUNE-DAQ/justintime.git
cd justintime
pip install -r requirements.txt
```

### Running Just-in-Time
To run `justintime`, you need a directory containing HDF5-format DUNE DAQ data files and you need to select a channel map. As of March 2024, the available channel map options are 'VDColdbox', 'ProtoDUNESP1', 'PD2HD', 'VST', 'FiftyL', and 'ICEBERG'. 
```
cd /path/to/justintime/
source env.sh
python -m justintime.app <DATA FOLDER PATH> <CHANNEL_MAP_NAME>
```
By default, this will run `justintime` on port number 8001. You can then navigate to `localhost:8001` in web browser to view the monitoring page. If running `justintime` on a remote host and you want to open the brower on your local machine, you must first set up an ssh tunnel via
```bash
ssh -KL 8001:<hostname>:8001 <username>@<hostname> -N
```
where `hostname` and `username` are the names of the host machine on which `justintime` is running and the user running it. If you're not sure, run `hostname` and `whoami` in a terminal on the remote host. 
