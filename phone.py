#!/usr/bin/env python
import argparse
import evdev
import asyncio
import subprocess

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-e', '--eventlistener', help='Listen for events from /dev/input/* and sensors', action='store_true')
    parser.add_argument('-l', '--swipeleft', help='Execute swipe left action', action='store_true')
    parser.add_argument('-r', '--swiperight', help='Execute swipe right action', action='store_true')
    parser.add_argument('-u', '--swipeup', help='Execute swipe up action', action='store_true')
    parser.add_argument('-d', '--swipedown', help='Execute swipe down action', action='store_true')
    parser.add_argument('--rumble', help='Rumble for <RUMBLE> milliseconds', type=int)
    parser.add_argument('--gpstime', help='Retrieve time from GPS and update system time', action='store_true')
    parser.add_argument('--gpsposition', help='Retrieve and store location from GPS', action='store_true')
    parser.add_argument('--wificonnect', help='Reconnect to WiFi AP already known by NM')
    parser.add_argument('--wifidisconnect', help='Disconnect WiFi')
    parser.add_argument('--espnow', help='Listen for ESPNOW frames on channel 1', action='store_true')
    args = parser.parse_args()

    if args.eventlistener: eventlistener()
    elif args.swipeleft: swipeleft()
    elif args.swiperight: swiperight()
    elif args.swipeup: swipedup()
    elif args.swipedown: swipedown()
    elif args.rumble: rumble(args.rumble)
    elif args.gpstime: gpstime()
    elif args.gpsposition: gpsposition()
    elif args.wificonnect: wificonnect(args.wificonnect)
    elif args.wifidisconnect: wifidisconnect()
    elif args.espnow: espnow()

def eventlistener():
    tristate = evdev.InputDevice('/dev/input/by-path/platform-alert-slider-event')
    vol = evdev.InputDevice('/dev/input/by-path/platform-gpio-keys-event')
    pwr = evdev.InputDevice('/dev/input/by-path/platform-c440000.spmi-platform-c440000.spmi:pmic@0:pon@800:pwrkey-event') # acpid will also react on the power button
    
    async def handle_events(device):
        async for event in device.async_read_loop():
            try:
                print(device.path, evdev.categorize(event), sep=': ')
            except KeyError:
                print(device.path, event, sep=': ')

    for device in tristate, vol, pwr:
        asyncio.ensure_future(handle_events(device))

    loop = asyncio.get_event_loop()
    loop.run_forever()

def swipeleft():
    subprocess.run(['dunstify', 'swiped -->'])

def swiperight():
    subprocess.run(['dunstify', 'swiped <--'])

def swipedup():
    subprocess.run(['dunstify', 'swiped /\\'])

def swipedown():
    subprocess.run(['dunstify', 'swiped \\/'])

def rumble(millis):
    print(f'trying to rumble {millis}ms')

def gpstime():
    subprocess.run([])

def gpsposition():
    subprocess.run([])
def wificonnect(accesspoint)
    wifi = subprocess.check_output(['nmcli' ,'device', 'wifi']).decode().split('\n')
    if accesspoint not in wfi[1]:
        for s in ['wpa_supplicant', 'networkmanager']:
            subprocess.run(['service', s, 'start'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


        wifidisconnect()
        subprocess.run(['nmcli', 'device', 'wifi', 'connect', accesspoint], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def wifidisconnect():
    subprocess.run(['nmcli', 'device', 'disconnect', 'wlan0'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def espnow():
    wifidisconnect()
    for s in ['wpa_supplicant', 'networkmanager']:
        subprocess.run(['service', s, 'stop'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    pf = 'type 0 subtype 0xd0 and wlan[24:4]=0x7f18fe34 and wlan[32]=221 and wlan[33:4]&0xffffff = 0x18fe34 and wlan[37]=0x4'
    with open('/tmp/espnow', 'w') as outfile:
        subprocess.run(['tcpdump', '-i' , 'wlan0', f'"{pf}"'], stdout=outfile, stderr=subprocess.STDOUT, text=True)

if __name__ == '__main__':
    main()