# postmarketOS UI based on openbox, with conky
<img src="https://github.com/biemster/pmos-openbox-conky/blob/main/screenshot.png" width=250> <img src="https://github.com/biemster/pmos-openbox-conky/blob/main/screenshot2.png" width=250>

This repo is a collection of random scripts and configs to get a basic UI for postmarketOS.
It shares the simplicity and low levelness of `sxmo`, but way better because `conky`!
Development is done on a OnePlus 6T in the `edge` release, so a couple things will only work there but should
be easily adaptable to other platforms.
Most of the following extra packages are needed to run everything:
```
vim,conky,python3,py3-evdev,py3-evdev-pyc,modemmanager,iw,feh,lisgd,tcpdump,libc6-compat,lm-sensors,iio-sensor-proxy,xset,curl,nmap,dbus-x11,dunst
```

## Targets
- [x] Basic UI
- [ ] Basic apps (Dialer, SMS, maps, web, etc)
- [x] Notifications
- [ ] Calls
- [x] Mobile data
- [ ] Touch gestures
- [ ] Sensors
- [ ] GPS
- [ ] WhatsApp, iMessage
- [ ] Power management

## Basic UI, notifications and gestures
The python script `phone.py` runs the show, and takes care of everything from `/dev/input` besides the gestures.
So the power button, volume control, tri-state thingy (on OP6), rumble and sensors (light,accelerometer,compass,proximity).

The conkyrc scripts provide a basic home screen, with input gestures provided by `lisgd`.
It is made dynamic by a small state machine that lives in
```
/tmp/ui_statemachine
```

Basic apps will be built as web apps, to provide easy testing on a remote machine. The webbrowser intended for this
will probably be `Servo` (https://servo.org), which will be launched using a swipe-right (or -left?) on the home screen.

Notifications are done using `dunst`, with the supplied `dunstrc` which should go to `$HOME/.config/dunst/dunstrc`
The `autostart` script is for openbox, and should be copied to `$HOME/.config/openbox/autostart`

## Calls
This should work out of the box with `q6voiced`, but is not tested yet.

## Mobile data
```bash
# service modemmanager start
$ mmcli -m any
$ mmcli -m 0 --simple-connect="apn=internet,ip-type=ipv4v6" # use apn settings specific for your provider
# ip l set qmapmux0.0 up
# ip a add <ip address from bearer>/32 dev qmapmux0.0
# ip r add default dev qmapmux0.0
$ mmcli -m 0 --simple-disconnect
```

## Sensors (light,proximity,acceleration,compass)
```bash
$ sensors
$ ssccli --sensor accelerometer # or other sensors
```
The `ssccli` tool has a timeout of 10 seconds, after which the application stops. This is annoying, one can change that for version `0.1.4` to half a day like this:
```bash
$ printf '00005490: 0018 9552 ebfe ff97 0100 8052 0000 80d2  @..R.......R....' | xxd -r - /usr/bin/ssccli
```
or use the proper dbus thing to listen to the sensors:
```bash
# service iio-sensor-proxy start
# monitor-sensor -a
```

## GPS
```bash
$ mmcli -m 0 --location-enable-gps-nmea
$ mmcli -m 0 --location-enable-agps-msb
$ mmcli -m 0 --location-status
$ mmcli -m 0 --location-inject-assistance-data=/path/to/downloaded/file
$ mmcli -m 0 --location-get
```

## SMS, WhatsApp, iMessage
WhatsApp will be connected through `whatsmeow`, iMessage when `pypush` works again.
They will be set up to write new messages to a separate SQLite database, from which `phone.py` pulls the latest entries.
Support for sending messages will be provided by a web app.

## Power management
https://wiki.postmarketos.org/wiki/Runtime_Power_Management

https://wiki.postmarketos.org/wiki/Opportunistic_Sleep

```bash
$ ls /sys/class/power_supply/*
$ cat /sys/class/power_supply/bq27411-0/capacity
$ cat /sys/class/power_supply/bq27411-0/charge_full_design
$ cat /sys/class/power_supply/bq27411-0/charge_full
$ cat /sys/class/power_supply/bq27411-0/charge_now
$ cat /sys/class/power_supply/pmi8998-charger/status 
$ cat /sys/class/power_supply/pmi8998-charger/current_now
```
