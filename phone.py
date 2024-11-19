#!/usr/bin/env python
import os
import argparse
import subprocess
from time import sleep
from datetime import datetime

os.putenv('DISPLAY', ':0')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-e', '--eventlistener', help='Listen for events from /dev/input/* and sensors', action='store_true')
    parser.add_argument('-l', '--swipeleft', help='Execute swipe left action', action='store_true')
    parser.add_argument('-r', '--swiperight', help='Execute swipe right action', action='store_true')
    parser.add_argument('-u', '--swipeup', help='Execute swipe up action', action='store_true')
    parser.add_argument('-d', '--swipedown', help='Execute swipe down action', action='store_true')
    parser.add_argument('--ui-full', help='Show full conky UI on desktop', action='store_true')
    parser.add_argument('--ui-minimal', help='Show minimal conky UI on desktop', action='store_true')
    parser.add_argument('--rumble', help='Rumble for <RUMBLE> milliseconds', type=int)
    parser.add_argument('--screen-on', help='Turn on the screen', action='store_true')
    parser.add_argument('--notification', help='Display notification')
    parser.add_argument('--enable-modem-wakeirq', help='Enable modem QIPCRTR wake irq', action='store_true')
    parser.add_argument('--disable-modem-wakeirq', help='Disable modem QIPCRTR wake irq', action='store_true')
    parser.add_argument('--try-sleeping', help='Go to s2idle if the screen is off and there is no incoming SSH connection', action='store_true')
    parser.add_argument('--opportunistic-sleep-enable', help='Enable opportunistic sleep', action='store_true')
    parser.add_argument('--opportunistic-sleep-disable', help='Disable opportunistic sleep', action='store_true')
    parser.add_argument('--wake-lock', help='Set phone.py wakelock', action='store_true')
    parser.add_argument('--wake-unlock', help='Release phone.py wakelock', action='store_true')
    parser.add_argument('--gps', help='Retrieve all relevant info from GPS in easy format', action='store_true')
    parser.add_argument('--gps-enable', help='Enable GPS location in ModemManager', action='store_true')
    parser.add_argument('--gpstime', help='Retrieve time from GPS and update system time', action='store_true')
    parser.add_argument('--gpsposition', help='Retrieve and store location from GPS', action='store_true')
    parser.add_argument('--wlan0-managed', help='Restart the wlan0 interface in managed mode', action='store_true')
    parser.add_argument('--wlan0-monitor', help='Restart the wlan0 interface in monitor mode', action='store_true')
    parser.add_argument('--wifi-connect', help='Reconnect to WiFi AP already known by NM')
    parser.add_argument('--wifi-disconnect', help='Disconnect WiFi', action='store_true')
    parser.add_argument('--wifi-off', help='Turn off WiFi', action='store_true')
    parser.add_argument('--espnow', help='Listen for ESPNOW frames on channel 1', action='store_true')
    parser.add_argument('--overcharge-protection', help='Limit charging current to 10mA when battery reached ~80%', action='store_true')
    args = parser.parse_args()

    if args.eventlistener: eventlistener()
    elif args.swipeleft: swipeleft()
    elif args.swiperight: swiperight()
    elif args.swipeup: swipedup()
    elif args.swipedown: swipedown()
    elif args.ui_full: ui_full()
    elif args.ui_minimal: ui_minimal()
    elif args.rumble: rumble(args.rumble)
    elif args.screen_on: screen_on()
    elif args.notification: notification(args.notification)
    elif args.enable_modem_wakeirq: enable_modem_wakeirq()
    elif args.disable_modem_wakeirq: disable_modem_wakeirq()
    elif args.try_sleeping: possibly_s2idle()
    elif args.opportunistic_sleep_enable: opportunistic_sleep_enable()
    elif args.opportunistic_sleep_disable: opportunistic_sleep_disable()
    elif args.wake_lock: opportunistic_sleep_wakelock()
    elif args.wake_unlock: opportunistic_sleep_wakeunlock()
    elif args.gps: gps()
    elif args.gps_enable: gps_enable()
    elif args.gpstime: gpstime()
    elif args.gpsposition: gpsposition()
    elif args.wlan0_managed: wlan0_modeset('managed')
    elif args.wlan0_monitor: wlan0_modeset('monitor')
    elif args.wifi_connect: wificonnect(args.wifi_connect)
    elif args.wifi_disconnect: wifidisconnect()
    elif args.wifi_off: wifi_off()
    elif args.espnow: espnow()
    elif args.overcharge_protection: overcharge_protection()

def notification(msg):
    screen_on()
    doas_10000 = []
    if os.getuid() == 0:
        doas_10000 = ['doas', '-u', '10000']
    subprocess.run(doas_10000 + ['dunstify', msg])

def log(msg):
    with open("/tmp/logging", "a") as f:
        f.write(f'{datetime.now()} {msg}\n')
    print(msg)

def eventlistener():
    import evdev
    import asyncio
    tristate = evdev.InputDevice('/dev/input/by-path/platform-alert-slider-event')
    vol = evdev.InputDevice('/dev/input/by-path/platform-gpio-keys-event')
    pwr = evdev.InputDevice('/dev/input/by-path/platform-c440000.spmi-platform-c440000.spmi:pmic@0:pon@800:pwrkey-event') # acpid will also react on the power button
    
    async def handle_events(device):
        async for event in device.async_read_loop():
            try:
                #log(f'{device.path}: {evdev.categorize(event)}')
                if '(KEY_POWER), up' in str(evdev.categorize(event)):
                    powerbutton_press()
            except KeyError:
                log(f'{device.path}: {event}')

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
    log(f'trying to rumble {millis}ms')

def wakeup_from_powerbutton():
    screen_on()

def wakeup_from_modem():
    screen_on()

def powerbutton_press():
    suspend_restart_powerdown_modal()

def ui_full():
    doas_10000 = []
    if os.getuid() == 0:
        doas_10000 = ['doas', '-u', '10000']
    subprocess.run(doas_10000 + ['sed', '-i', 's/minimal/full/', '/tmp/ui_statemachine'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def ui_minimal():
    doas_10000 = []
    if os.getuid() == 0:
        doas_10000 = ['doas', '-u', '10000']
    subprocess.run(doas_10000 + ['sed', '-i', 's/full/minimal/', '/tmp/ui_statemachine'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def suspend_restart_powerdown_modal():
    import tkinter
    from tkinter import ttk
    import sv_ttk

    root = tkinter.Tk()
    root.overrideredirect(True)  # remove window decorations, including title bar

    def suspend_clicked():
        s2idle_start();
        root.destroy()

    def reboot_clicked():
        reboot()
        root.destroy()

    def poweroff_clicked():
        poweroff()
        root.destroy()

    def cancel_clicked():
        root.destroy()

    ttk.Button(root, text="⏾", command=suspend_clicked, style='Bold.TButton', width=2).pack()
    ttk.Button(root, text="↻", command=reboot_clicked, style='Bold.TButton', width=2).pack()
    ttk.Button(root, text="⏻", command=poweroff_clicked, style='Bold.TButton', width=2).pack()
    ttk.Button(root, text="x", command=cancel_clicked, style='Bold.TButton', width=2).pack()

    sv_ttk.set_theme("dark")
    bStyle = ttk.Style()
    bStyle.configure('Bold.TButton', font =('Noto','72','bold'))

    # place on the right and close to the power button
    root.geometry(f'1x1+1+1') # initially hide, update_idletasks() shows the modal before putting it in the right place
    root.update_idletasks()
    w = root.winfo_width()
    h = root.winfo_height()
    ws = root.winfo_screenwidth()
    root.geometry(f'{w}x{h}+{ws-w}+600')
    root.mainloop()

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
        log('$GPGGA sentence not found, maybe GPS has no fix yet?')
    return sentence

def gpstime():
    sentence = GPGGA().split(',')
    log(sentence[1])

def gpsposition():
    sentence = GPGGA().split(',')
    log(sentence[2:6])

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
    doas_10000 = []
    if os.getuid() == 0:
        doas_10000 = ['doas', '-u', '10000']
    subprocess.run(doas_10000 + ['xset', 's', 'reset'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(doas_10000 + ['xset', 'dpms', 'force', 'on'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def enable_modem_wakeirq():
    modem_wakeirq = '/sys/bus/rpmsg/devices/4080000.remoteproc:glink-edge.IPCRTR.-1.-1/power/wakeup'
    subprocess.run(['doas', '/usr/bin/tee', modem_wakeirq], text=True, input='enabled', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def disable_modem_wakeirq():
    modem_wakeirq = '/sys/bus/rpmsg/devices/4080000.remoteproc:glink-edge.IPCRTR.-1.-1/power/wakeup'
    subprocess.run(['doas', '/usr/bin/tee', modem_wakeirq], text=True, input='disabled', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def s2idle_start():
    log("going to suspend")
    subprocess.run(['doas', '/usr/bin/loginctl', 'suspend'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def opportunistic_sleep_enable():
    subprocess.run(['doas', '/usr/bin/tee', '/sys/power/autosleep'], text=True, input='mem', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def opportunistic_sleep_disable():
    subprocess.run(['doas', '/usr/bin/tee', '/sys/power/autosleep'], text=True, input='off', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def opportunistic_sleep_wakelock(timeout=None):
    subprocess.run(['doas', '/usr/bin/tee', '/sys/power/wake_lock'], text=True, input='phone.py' + (f' {int(timeout * 1e9)}' if timeout else ''), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def opportunistic_sleep_wakeunlock():
    subprocess.run(['doas', '/usr/bin/tee', '/sys/power/wake_unlock'], text=True, input='phone.py', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def opportunistic_sleep_wakelock_toggle():
    with open('/sys/power/wake_lock') as f:
        locks = f.read()
        if 'phone.py' in locks:
            opportunistic_sleep_wakeunlock()
        else:
            opportunistic_sleep_wakelock()

def poweroff():
    log("going to power off")
    subprocess.run(['doas', '/usr/bin/loginctl', 'poweroff'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def reboot():
    log("going to reboot")
    subprocess.run(['doas', '/usr/bin/loginctl', 'reboot'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def is_screen_off():
    xsetq = subprocess.check_output(['xset', 'q']).decode().split('\n')[-2]
    return 'Monitor is Off' in xsetq

def ssh_connection_active():
    # this is actually done by sleep-inhibitor already
    netstat = subprocess.check_output(['netstat', '-tpn'], stderr=subprocess.DEVNULL).decode().split('\n')[2:]
    for connection in netstat:
        c = connection.split()
        if len(c) > 6 and c[3].endswith(':22') and c[5] == 'ESTABLISHED':
            return True
    return False

def opportunistic_sleep():
    while True:
        if is_screen_off() and not ssh_connection_active():
            opportunistic_sleep_wakeunlock()
        sleep(3)

def possibly_s2idle():
    while True:
        if is_screen_off() and not ssh_connection_active():
            s2idle_start()
            sleep(10) # this can take a while
        sleep(3)

def wlan0_modeset(mode='managed'):
    if os.getuid() != 0:
        log('wlan0_modeset should be run as root, so do what you just did with doas')
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
        if ssid[0] != '*' or ssid[2] != accesspoint:
            wifidisconnect()
            wlan0_modeset('managed')
            subprocess.run(['nmcli', 'device', 'wifi', 'connect', accesspoint], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def wifidisconnect():
    subprocess.run(['nmcli', 'device', 'disconnect', 'wlan0'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def wifi_off():
    wifi = subprocess.check_output(['nmcli' ,'device', 'wifi']).decode().split('\n')
    if len(wifi) > 2:
        ssid1 = wifi[1].split()
        if ssid[0] == '*':
            subprocess.run(['nmcli', 'connection', 'delete', 'id', ssid[2]], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def espnow():
    wifidisconnect()
    wlan0_modeset('monitor')

    pf = 'type 0 subtype 0xd0 and wlan[24:4]=0x7f18fe34 and wlan[32]=221 and wlan[33:4]&0xffffff = 0x18fe34 and wlan[37]=0x4'
    with open('/tmp/espnow', 'w') as outfile:
        subprocess.run(['tcpdump', '-XX', '-i' , 'wlan0', pf], stdout=outfile, stderr=subprocess.STDOUT, text=True)

def get_charge_now():
    with open('/sys/class/power_supply/bq27411-0/charge_now', 'r') as f:
        int(f.read())

def limit_charger_current():
    with open('/sys/class/power_supply/pmi8998-charger/current_max', 'w') as f:
        f.write('10000') # 10 mA

def resume_charger_current():
    with open('/sys/class/power_supply/pmi8998-charger/current_max', 'w') as f:
        f.write('1125000') # 1A

BATTERY_MAX_CHARGE = 3000000 # battery is old, not 3.6 Ah but 3.0 Ah
def overcharge_protection():
    wait_for_70 = False # charged to above 80%, wait for it to drop below 70% to charge again
    while True:
        charge_now = get_charge_now()
        if wait_for_70 and charge_now < BATTERY_MAX_CHARGE * 0.7:
            resume_charger_current()
            wait_for_70 = False
        elif charge_now > BATTERY_MAX_CHARGE * 0.8:
            limit_charger_current()
            wait_for_70 = True
        sleep(10)

if __name__ == '__main__':
    main()