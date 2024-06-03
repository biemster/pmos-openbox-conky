#!/usr/bin/env python
import os
import argparse
import evdev
import asyncio
import subprocess
from time import sleep

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-e', '--eventlistener', help='Listen for events from /dev/input/* and sensors', action='store_true')
    parser.add_argument('-l', '--swipeleft', help='Execute swipe left action', action='store_true')
    parser.add_argument('-r', '--swiperight', help='Execute swipe right action', action='store_true')
    parser.add_argument('-u', '--swipeup', help='Execute swipe up action', action='store_true')
    parser.add_argument('-d', '--swipedown', help='Execute swipe down action', action='store_true')
    parser.add_argument('--rumble', help='Rumble for <RUMBLE> milliseconds', type=int)
    parser.add_argument('--gps', help='Retrieve all relevant info from GPS in easy format', action='store_true')
    parser.add_argument('--gpstime', help='Retrieve time from GPS and update system time', action='store_true')
    parser.add_argument('--gpsposition', help='Retrieve and store location from GPS', action='store_true')
    parser.add_argument('--wlan0managed', help='Restart the wlan0 interface in managed mode', action='store_true')
    parser.add_argument('--wlan0monitor', help='Restart the wlan0 interface in monitor mode', action='store_true')
    parser.add_argument('--wificonnect', help='Reconnect to WiFi AP already known by NM')
    parser.add_argument('--wifidisconnect', help='Disconnect WiFi', action='store_true')
    parser.add_argument('--espnow', help='Listen for ESPNOW frames on channel 1', action='store_true')
    args = parser.parse_args()

    if args.eventlistener: eventlistener()
    elif args.swipeleft: swipeleft()
    elif args.swiperight: swiperight()
    elif args.swipeup: swipedup()
    elif args.swipedown: swipedown()
    elif args.rumble: rumble(args.rumble)
    elif args.gps: gps()
    elif args.gpstime: gpstime()
    elif args.gpsposition: gpsposition()
    elif args.wlan0managed: wlan0_modeset('managed')
    elif args.wlan0monitor: wlan0_modeset('monitor')
    elif args.wificonnect: wificonnect(args.wificonnect)
    elif args.wifidisconnect: wifidisconnect()
    elif args.espnow: espnow()

def notification(msg):
    subprocess.run(['sudo', '-u', '#10000', 'dunstify', msg])

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
    notification('swiped left')

def swiperight():
    notification('swiped right')

def swipedup():
    notification('swiped up')

def swipedown():
    notification('swiped down')

def rumble(millis):
    print(f'trying to rumble {millis}ms')

def GPGGA():
    loc = subprocess.check_output(['mmcli', '-m', '0', '--location-get', '--output-keyvalue']).decode().split('\n')
    sentence = ''
    for kv in loc:
        if 'GPGGA' in kv:
            sentence = kv[kv.find('$GPGGA'):]
            break
    else:
        print('$GPGGA sentence not found, maybe GPS has no fix yet?')
    return sentence

def gpstime():
    sentence = GPGGA().split(',')
    print(sentence[1])

def gpsposition():
    sentence = GPGGA().split(',')
    print(sentence[2:6])

def gps():
    loc = subprocess.check_output(['mmcli', '-m', '0', '--location-get', '--output-keyvalue']).decode().split('\n')
    gpsdata = {}
    for kv in loc:
        if 'gps.utc' in kv:
            gpsdata['utc'] = int(float(kv[kv.find(': ') +2:]))
        elif 'gps.longitude' in kv:
            gpsdata['lon'] = float(kv[kv.find(': ') +2:])
        elif 'gps.latitude' in kv:
            gpsdata['lat'] = float(kv[kv.find(': ') +2:])
        elif 'gps.altitude' in kv:
            gpsdata['alt'] = int(float(kv[kv.find(': ') +2:]))
        elif 'GPGGA' in kv:
            sentence = kv[kv.find('$GPGGA'):]
            gpsdata['acc'] = float(sentence[8])
    print(f'gps: {gpsdata['utc']} {gpsdata['lat']:.3f} {gpsdata['lon']:.3f} {gpsdata['acc']} {gpsdata['alt']}')

def wlan0_modeset(mode='managed'):
    if os.getuid() != 0:
        print('wlan0_modeset should be run as root, so do what you just did with sudo')
    else:
        modes = {'managed': ('start', b'\x00', 'frame_mode=1'), 'monitor': ('stop', b'\x04', 'frame_mode=0')}

        for s in ['wpa_supplicant', 'networkmanager']:
            subprocess.run(['service', s, modes[mode][0]], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        subprocess.run(['rmmod', 'ath10k_snoc', 'ath10k_core', 'ath'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        with open('/lib/firmware/ath10k/WCN3990/hw1.0/firmware-5.bin', 'r+b') as f:
            f.seek(33)
            f.write(modes[mode][1])

        subprocess.run(['modprobe', 'ath10k_core', modes[mode][2]], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(['modprobe', 'ath10k_snoc'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        if mode == 'monitor':
            sleep(1) # give it some time to init
            subprocess.run(['ip', 'link', 'set', 'wlan0', 'down'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(['iw', 'dev', 'wlan0', 'set', 'type', 'monitor'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(['ip', 'link', 'set', 'wlan0', 'up'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(['iw', 'dev', 'wlan0', 'set', 'channel', '1'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    notification(f'wlan0 now {mode}')

def wificonnect(accesspoint):
    wifi = subprocess.check_output(['nmcli' ,'device', 'wifi']).decode().split('\n')
    # this is not correct, wifi[1] will be the first anyway if it is the closest
    # FIXME check if there is an actual connection already
    if accesspoint not in wifi[1]:
        wifidisconnect()
        wlan0_modeset('managed')
        subprocess.run(['nmcli', 'device', 'wifi', 'connect', accesspoint], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def wifidisconnect():
    subprocess.run(['nmcli', 'device', 'disconnect', 'wlan0'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def espnow():
    wifidisconnect()
    wlan0_modeset('monitor')

    pf = 'type 0 subtype 0xd0 and wlan[24:4]=0x7f18fe34 and wlan[32]=221 and wlan[33:4]&0xffffff = 0x18fe34 and wlan[37]=0x4'
    with open('/tmp/espnow', 'w') as outfile:
        subprocess.run(['tcpdump', '-i' , 'wlan0', f'"{pf}"'], stdout=outfile, stderr=subprocess.STDOUT, text=True)

if __name__ == '__main__':
    main()