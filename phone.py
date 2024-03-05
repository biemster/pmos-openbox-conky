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
    args = parser.parse_args()

    if args.eventlistener: eventlistener()
    elif args.swipeleft: swipeleft()
    elif args.swiperight: swiperight()
    elif args.swipeup: swipedup()
    elif args.swipedown: swipedown()
    elif args.rumble: rumble(args.rumble)

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

if __name__ == '__main__':
    main()