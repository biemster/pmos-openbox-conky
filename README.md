# postmarketOS UI based on openbox, with conky
<img src="https://github.com/biemster/pmos-openbox-conky/blob/main/screenshot.png" width=250> <img src="https://github.com/biemster/pmos-openbox-conky/blob/main/screenshot2.png" width=250>

This repo is a collection of random scripts and configs to get a basic UI for postmarketOS.
It shares the simplicity and low levelness of `sxmo`, but way better because `conky`!
Development is done on a OnePlus 6T in the `edge` release, so a couple things will only work there but should
be easily adaptable to other platforms.
Most of the following extra packages are needed to run everything:
```
vim,git,conky,python3,py3-evdev,py3-evdev-pyc,py3-dbus,dbus-x11,modemmanager,iw,feh,lisgd,tcpdump,libc6-compat,lm-sensors,iio-sensor-proxy,xset,xwd,xprintidle,curl,nmap,dunst,dtc,scapy,qcom-diag
```

## Targets
- [x] Basic UI
- [ ] Basic apps (Dialer, SMS, maps, web, etc)
- [x] Notifications
- [ ] Calls / SMS
- [x] Mobile data
- [x] Touch gestures
- [x] Sensors
- [x] GPS
- [x] NFC
- [ ] WhatsApp, iMessage
- [x] Power management
- [ ] Access to internal home network

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
https://wiki.postmarketos.org/wiki/Opportunistic_Sleep

https://www.kernel.org/doc/Documentation/ABI/testing/sysfs-power

The `90-autosleep` file needs to be copied to `/etc/sudoers.d/`, then the `phone.py` commands relating to opportunistic sleep will work.
The phone will not go to sleep if an ssh connection is active, or when the screen is on.
A detailed description on this will be added here, as some more logic will be added like regularly waking up to check for messages.

```bash
$ ls /sys/class/power_supply/*
$ cat /sys/class/power_supply/bq27411-0/capacity
$ cat /sys/class/power_supply/bq27411-0/charge_full_design
$ cat /sys/class/power_supply/bq27411-0/charge_full
$ cat /sys/class/power_supply/bq27411-0/charge_now
$ cat /sys/class/power_supply/pmi8998-charger/status 
$ cat /sys/class/power_supply/pmi8998-charger/current_now
```

## Access to internal home network
- wireguard: https://gist.github.com/insdavm/b1034635ab23b8839bf957aa406b5e39
- sish: https://docs.ssi.sh/

## NFC
Still a work in progress, but we can talk to the NFC chip:
1. Enable `i2c-3` and pins 12 and 63 in the device tree using `NFC.patch` from this repo:
```bash
cd /boot/dtbs/qcom
dtc sdm845-oneplus-fajita.dtb -o sdm845-oneplus-fajita.dts
patch < NFC.patch
dtc sdm845-oneplus-fajita.dts -o sdm845-oneplus-fajita.dtb
mkinitfs
reboot
```
2. Use (and develop) `nxp_nci_i2c.py` to directly talk to the NFC chip over i2c.

## Wishlist
- Camera: https://gitlab.com/sdm845-mainline/linux/-/issues/21
- USB host (or whatever it's called nowadays, I want to be able to power and connect to an ESP32 or RP2040)
