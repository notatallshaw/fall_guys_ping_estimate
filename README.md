# Fall Guys Ping Estimate

Reads the IP address of the Fall Guys Server from the player logs.

Instead of reading the "ping" value from the logs the script directly pings the Fall Guys Server and presents the stats in an overlay

## Screenshot

## Install

To install you must have Python 3.9+ and run the following command:

```
python -m pip install git+https://github.com/notatallshaw/fall_guys_ping_estimate
```

### Warning installing in a conda environment

If you are installing in a conda environmnet (Anaconda / Miniconda / Miniforge / Mambaforge) you must first install pywin32 for it to be compatible with the conda environment. I reccomend first running this in your conda environment before runing the above pip install:

```
conda install pywin32 psutil
```
