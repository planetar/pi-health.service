# pi-health.service

This script is intended to run as a daemon on a raspberry pi with raspbian or a derivative like octopi, openhabian etc.
It collects cpu health data including temperature, frequency, throttling, under_voltage, cpu-load, memory use and post them to an MQTT broker.
Namely when a number of raspberries are active like in a smarthome setup or with several 3d printers on octoprint this helps to survey the well being of those raspis and integrate their state on a dedicated page, i.e. with openhab2 and the mqtt binding.

The scripts connection data are configured in the settings.ini which is expected to reside next to the script. A .service file is included which makes it easy to register the script as a daemon and control it via systemctl.

## Installation:

- download/extract the zip or git clone the files here to a directory of your choice.
- chown it all to a user with permissions to use (i:e. pi or openhabian). The user needs to be in the video group.
- rename the file settings.ini.dist to settings.ini and edit it, the address of the mqbroker, the user and password, port
- after you tested it all runs from the commandline, edit the file health.service and update the file path there.
- copy health.service to /etc/systemd/system/health.service

from the command line :
- systemctl enable health.service
- systemctl start health.service
- systemctl status health.service

![health data in habpanel diagram](https://github.com/planetar/pi-health.service/blob/master/rsc/raspi_load_temp_Screenshot_20200602_205336.png?raw=true)
