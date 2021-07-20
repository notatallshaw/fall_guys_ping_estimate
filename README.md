# Fall Guys Ping Estimate

Reads the IP address of the Fall Guys Server from the player logs. Then directly pings the Fall Guys Server every 5 seconds and presents the stats in an overlay

This is different from other Fall Guys stats collectors which read the ping from the logs. The problem with that approach is the ping is not updated very often in the logs, and the value appears to be more than just an RTT ping, for example it could include processing time on the server, or it could be rounded up to specific numbers. In my experince the ping number in the player logs can not be trusted.

## Screenshot

![Fall Guys Ping Estimate](fall_guys_ping_estimator.png "Fall Guys Ping Estimate")

## Download and Run Executable

If you want a one click executable file, no need to worry about the source code or anything, download and run here (you may need to give it a minute after downloading while Windows File Deferender scans it): https://github.com/notatallshaw/fall_guys_ping_estimate/releases/download/v0.1.3/run_fgpe.exe

## Shutdown

Press the X at the leftmost section of the overlay

## Install from Source Code

To install you must have Python 3.9+ and run the following command:

```
python -m pip install git+https://github.com/notatallshaw/fall_guys_ping_estimate.git
```

## Run from Source code

On the command line run:

```
python -m fgpe
```

## Build Executable

Checkout the source code from git, have Python 3.9+ installed.

Install Pyinstaller:

```
python -m pip install pyinstaller
```

Build the installer (will create an exe at dist\run_fgpe.exe):

```
pyinstaller run_fgpe.py --noconsole --onefile
```
