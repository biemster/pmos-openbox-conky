#!/usr/bin/env python
import argparse
import subprocess
from time import sleep

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-e', '--eventlistener', help='Listen for events from /dev/input/* and sensors', action='store_true')
    parser.add_argument('-s', '--opportunistic-sleep', help='Allow sleeping by removing "phone.py" wakelock when idle for a while and not connected', action='store_true')
    parser.add_argument('-l', '--swipeleft', help='Execute swipe left action', action='store_true')
    parser.add_argument('-r', '--swiperight', help='Execute swipe right action', action='store_true')
    parser.add_argument('-u', '--swipeup', help='Execute swipe up action', action='store_true')
    parser.add_argument('-d', '--swipedown', help='Execute swipe down action', action='store_true')
    parser.add_argument('--ui-full', help='Show full conky UI on desktop', action='store_true')
    parser.add_argument('--ui-minimal', help='Show minimal conky UI on desktop', action='store_true')
    parser.add_argument('--rumble', help='Rumble for <RUMBLE> milliseconds', type=int)
    parser.add_argument('--screen-on', help='Turn on the screen', action='store_true')
    parser.add_argument('--try-sleeping', help='Set wake lock if the screen is on, or if there is an SSH connection', action='store_true')
    parser.add_argument('--opportunistic-sleep-enable', help='Enable opportunistic sleep', action='store_true')
    parser.add_argument('--opportunistic-sleep-disable', help='Disable opportunistic sleep', action='store_true')
    parser.add_argument('--wake-lock', help='Set phone.py wakelock', action='store_true')
    parser.add_argument('--wake-unlock', help='Release phone.py wakelock', action='store_true')
    parser.add_argument('--gps', help='Retrieve all relevant info from GPS in easy format', action='store_true')
    parser.add_argument('--gps-enable', help='Enable GPS location in ModemManager', action='store_true')
    parser.add_argument('--gpstime', help='Retrieve time from GPS and update system time', action='store_true')
    parser.add_argument('--gpsposition', help='Retrieve and store location from GPS', action='store_true')
    parser.add_argument('--wlan0managed', help='Restart the wlan0 interface in managed mode', action='store_true')
    parser.add_argument('--wlan0monitor', help='Restart the wlan0 interface in monitor mode', action='store_true')
    parser.add_argument('--wificonnect', help='Reconnect to WiFi AP already known by NM')
    parser.add_argument('--wifidisconnect', help='Disconnect WiFi', action='store_true')
    parser.add_argument('--espnow', help='Listen for ESPNOW frames on channel 1', action='store_true')
    args = parser.parse_args()

    if args.eventlistener: eventlistener()
    elif args.opportunistic_sleep: opportunistic_sleep()
    elif args.swipeleft: swipeleft()
    elif args.swiperight: swiperight()
    elif args.swipeup: swipedup()
    elif args.swipedown: swipedown()
    elif args.ui_full: ui_full()
    elif args.ui_minimal: ui_minimal()
    elif args.rumble: rumble(args.rumble)
    elif args.screen_on: screen_on()
    elif args.try_sleeping: opportunistic_sleep()
    elif args.opportunistic_sleep_enable: opportunistic_sleep_enable()
    elif args.opportunistic_sleep_disable: opportunistic_sleep_disable()
    elif args.wake_lock: opportunistic_sleep_wakelock()
    elif args.wake_unlock: opportunistic_sleep_wakeunlock()
    elif args.gps: gps()
    elif args.gps_enable: gps_enable()
    elif args.gpstime: gpstime()
    elif args.gpsposition: gpsposition()
    elif args.wlan0managed: wlan0_modeset('managed')
    elif args.wlan0monitor: wlan0_modeset('monitor')
    elif args.wificonnect: wificonnect(args.wificonnect)
    elif args.wifidisconnect: wifidisconnect()
    elif args.espnow: espnow()

def notification(msg):
    screen_on()
    subprocess.run(['sudo', '-u', '#10000', 'dunstify', msg])

def eventlistener():
    import evdev
    import asyncio
    tristate = evdev.InputDevice('/dev/input/by-path/platform-alert-slider-event')
    vol = evdev.InputDevice('/dev/input/by-path/platform-gpio-keys-event')
    pwr = evdev.InputDevice('/dev/input/by-path/platform-c440000.spmi-platform-c440000.spmi:pmic@0:pon@800:pwrkey-event') # acpid will also react on the power button
    
    async def handle_events(device):
        async for event in device.async_read_loop():
            try:
                #print(device.path, evdev.categorize(event), sep=': ')
                if '(KEY_POWER), down' in str(evdev.categorize(event)):
                    opportunistic_sleep_wakelock_toggle()
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

def ui_full():
    subprocess.run(['sudo', '-u', '#10000', 'sed', '-i', 's/minimal/full/', '/tmp/ui_statemachine'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def ui_minimal():
    subprocess.run(['sudo', '-u', '#10000', 'sed', '-i', 's/full/minimal/', '/tmp/ui_statemachine'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def gps_enable():
    for gps_action in ['--location-enable-gps-raw', '--location-enable-gps-nmea', '--location-set-gps-refresh-rate=1']:
        subprocess.run(['mmcli', '-m', '0', gps_action], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

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
    gpsdata = {'view': 0, 'fix': 0, 'acc': 10}
    for kv in loc:
        val = kv[kv.find(': ') +2:]
        if 'gps.utc' in kv:
            gpsdata['utc'] = int(float(val)) if val != '--' else 0
        elif 'gps.longitude' in kv:
            gpsdata['lon'] = float(val) if val != '--' else 0.0
        elif 'gps.latitude' in kv:
            gpsdata['lat'] = float(val) if val != '--' else 0.0
        elif 'gps.altitude' in kv:
            gpsdata['alt'] = int(float(val)) if val != '--' else 0
        elif 'GPGSV' in kv:
            sentence = kv[kv.find('$GPGSV'):].split(',')
            gpsdata['view'] = int(sentence[3] or gpsdata['view'])
        elif 'GPGGA' in kv:
            sentence = kv[kv.find('$GPGGA'):].split(',')
            gpsdata['fix'] = int(sentence[7] or gpsdata['fix'])
            gpsdata['acc'] = float(sentence[8] or gpsdata['acc'])
    print(f'gps: {gpsdata['view']} {gpsdata['fix']} {gpsdata['utc']} {gpsdata['lat']:.3f} {gpsdata['lon']:.3f} {gpsdata['acc']} {gpsdata['alt']}')

def screen_on():
    # screensaver reset resets the idle timer, dpms force on let's dpms know the screen is on again
    subprocess.run(['sudo', '-u', '#10000', 'xset', 's', 'reset'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(['sudo', '-u', '#10000', 'xset', 'dpms', 'force', 'on'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def opportunistic_sleep_enable():
    subprocess.run(['sudo', '/usr/bin/tee', '/sys/power/autosleep'], text=True, input='mem', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def opportunistic_sleep_disable():
    subprocess.run(['sudo', '/usr/bin/tee', '/sys/power/autosleep'], text=True, input='off', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def opportunistic_sleep_wakelock(timeout=None):
    subprocess.run(['sudo', '/usr/bin/tee', '/sys/power/wake_lock'], text=True, input='phone.py' + (f' {int(timeout * 1e9)}' if timeout else ''), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def opportunistic_sleep_wakeunlock():
    subprocess.run(['sudo', '/usr/bin/tee', '/sys/power/wake_unlock'], text=True, input='phone.py', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def opportunistic_sleep_wakelock_toggle():
    with open('/sys/power/wake_lock') as f:
        locks = f.read()
        if 'phone.py' in locks:
            opportunistic_sleep_wakeunlock()
        else:
            opportunistic_sleep_wakelock()

def opportunistic_sleep():
    while True:
        xsetq = subprocess.check_output(['xset', 'q']).decode().split('\n')[-2]
        screen_off = 'Monitor is Off' in xsetq

        netstat = subprocess.check_output(['netstat', '-tpn'], stderr=subprocess.DEVNULL).decode().split('\n')[2:]
        ssh_connection_active = False
        for connection in netstat:
            c = connection.split()
            if len(c) > 6 and c[3].endswith(':22') and c[5] == 'ESTABLISHED':
                ssh_connection_active = True
                break

        print(screen_off, ssh_connection_active)
        if screen_off and not ssh_connection_active:
            opportunistic_sleep_wakeunlock()
        sleep(3)

def wlan0_modeset(mode='managed'):
    import os
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
    if len(wifi) > 2:
        ssid1 = wifi[1].split()
        if ssid[0] != '*' or ssid[2] != 'accesspoint':
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
        subprocess.run(['tcpdump', '-XX', '-i' , 'wlan0', pf], stdout=outfile, stderr=subprocess.STDOUT, text=True)

if __name__ == '__main__':
    main()