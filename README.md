# Fall Guys Ping Estimate

Reads the IP address of the Fall Guys Server from the player logs. Then directly pings the Fall Guys Server every 5 seconds and presents the stats in an overlay

This is different from other Fall Guys stats collectors which read the ping from the logs. The problem with that approach is the ping is not updated very often in the logs, and the value appears to be more than just an RTT ping, for example it could include processing time on the server, or it could be rounded up to specific numbers. In my experince the ping number in the player logs can not be trusted.

## Screenshot

![Fall Guys Ping Estimate](fall_guys_ping_estimator.png "Fall Guys Ping Estimate")

## Install

To install you must have Python 3.9+ and run the following command:

```
python -m pip install git+https://github.com/notatallshaw/fall_guys_ping_estimate.git
```

## Run

On the command line run:

```
python -m fgpe
```

## Shutdown

Press the X at the leftmost section of the overlay

