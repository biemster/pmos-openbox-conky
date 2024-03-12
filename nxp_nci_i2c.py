#!/usr/bin/env python
from periphery import GPIO,I2C,sleep_ms

# debugging, is controlled by --debug {NONE,MSG,CMD,BOTH}
MSG_DEBUG = False # general debug statement
CMD_DEBUG = False # print raw commands to and from NFCC
def format_bytes(b): return ' '.join([f'{x:02X}' for x in b])
def print_debug(msg): print(msg) if MSG_DEBUG else None
def print_cmd(direction, b): print(direction + ' ' + format_bytes(b)) if CMD_DEBUG else None

HW_VER = {0x04: 'PN547 C1', 0x05: 'PN547C2, NPC100, PN7120, NQ410', 0x15: 'NPC120, PN65T', 0x40: 'PN553 A0', 0x41: 'PN553 B0, PN557, NPC400, NQ310, NQ410',
            0x50: 'PN553 A0 + P73', 0x51: 'PN553 B0 + P73 , NQ440, NQ330, PN80T, PN80S, PN81F, PN81T', 0x00: 'PN551', 0x98: 'NPC310', 0xA8: 'PN67T', 0x08: 'PN67T',
            0x28: 'PN548 C2', 0x48: 'NQ210', 0x88: 'PN7150', 0x18: 'pn66T', 0x58: 'NQ220'}

class NFCC:
    def __init__(self, i2cbus, address, gpiochip, pin_ven, pin_irq):
        self.venLine = GPIO(gpiochip, pin_ven, 'high', label='nfc_VEN')
        self.irqLine = GPIO(gpiochip, pin_irq, 'in', edge='rising', label='nfc_IRQ')
        sleep_ms(100)
        self.i2c = I2C(i2cbus)
        self.i2c_addr = address
        self.reset()

    def on(self):
        self.venLine.write(True)

    def off(self):
        self.venLine.write(False)

    def send(self, cmd):
        self.i2c.transfer(self.i2c_addr, [I2C.Message(cmd)])
        print_cmd('>>', cmd)

    def recv(self, size=-1):
        res = []
        if size > 0:
            msg = [I2C.Message([0x00]*size, read=True)]
            self.i2c.transfer(0x28, msg)
            res = msg[0].data
        elif size < 0:
            r = self.recv(3)
            res = r + self.recv(r[-1])
            print_cmd('<<', res)
        return res

    def reset(self):
        r = self.send([0x20, 0x00, 0x01, 0x01])
        if self.has_data(): # Catch potential notification
            self.recv()

    def has_data(self, timeout=0.3):
        if self.irqLine.poll(timeout=timeout):
            self.irqLine.read_event()
            return True
        return False

    def __del__(self):
        self.off()
        self.venLine.close()
        self.irqLine.close()


def main():
    global MSG_DEBUG
    global CMD_DEBUG

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--i2c', help='I2C bus', default='/dev/i2c-3')
    parser.add_argument('--address', help='NFCC address on I2C bus', type=int, default=0x28)
    parser.add_argument('--gpio', help='GPIO chip for IRQ and VEN pins', default='/dev/gpiochip2')
    parser.add_argument('--ven', help='VEN pin', type=int, default=12)
    parser.add_argument('--irq', help='IRQ pin', type=int, default=63)
    parser.add_argument('--chipid', help='Check NFC chip ID', action='store_true')
    parser.add_argument('--listen', help='Listen for tags/devices', action='store_true')
    parser.add_argument('--emulate', help='Emulate tag/card', action='store_true')
    parser.add_argument('--debug', help='Set debugging level (NONE,MSG,CMD,BOTH)', default='NONE')
    args = parser.parse_args()

    MSG_DEBUG = (args.debug in ['BOTH', 'MSG'])
    CMD_DEBUG = (args.debug in ['BOTH', 'CMD'])

    nfcc = NFCC(args.i2c, args.address, args.gpio, args.ven, args.irq)

    try:
        if args.chipid: chipid(nfcc)
        elif args.listen: listen(nfcc)
        elif args.emulate: emulate(nfcc)
    except KeyboardInterrupt:
        print('Switching off NFCC')

def chipid(nfcc):
    NCICoreInit1_0 = [0x20, 0x01, 0x00]
    NCICoreInit2_0 = [0x20, 0x01, 0x02, 0x00, 0x00]
    cid = None
    nfcc.send(NCICoreInit2_0)
    if nfcc.has_data():
        r = nfcc.recv()
        if r[:2] == [0x40, 0x01] and r[2] >= 4:
            idver_offset = len(r) -4
            cid = r[idver_offset]
            fwv = r[idver_offset +1:idver_offset +4]
            print(f'Chip ID 0x{cid:02X} ({HW_VER[cid]}), FW ver {fwv[0]:02x}.{fwv[1]:02x}.{fwv[2]:02x}')
    return cid

def listen(nfcc, restart=False):
    NCIStartDiscovery = [0x21, 0x03, 0x09, 0x04, 0x00, 0x01, 0x01, 0x01, 0x02, 0x01, 0x06, 0x01];
    NCIRestartDiscovery = [0x21, 0x06, 0x01, 0x03];
    if not restart:
        chipid(nfcc) # initialize
        nfcc.send(NCIStartDiscovery)
    else:
        nfcc.send(NCIRestartDiscovery)

    while not nfcc.has_data(): pass
    r = nfcc.recv()
    if r[:4] in [[0x41, 0x03, 0x01, 0x00], [0x41, 0x06, 0x01, 0x00]]:
        print_debug('Discovery loop started')
        while True:
            while not nfcc.has_data(): pass
            r = nfcc.recv()
            if r[:2] in [[0x61, 0x03], [0x61, 0x05]]:
                print_debug(f'Found a tag')
                process_tag(r)
                print_debug(f'Finished processing tag, restarting loop')
                break
            if r[:2] == [0x61, 0x06]:
                print_debug(f"What does this mean? ({format_bytes(r)})")
    else:
        print_debug(f"E: Could not start discovery loop: {format_bytes(r)}")
        return
    listen(nfcc, restart=True)

def emulate(nfcc):
    print('Emulation not implemented yet')

def process_tag(msg):
    print(f"Tag said hello with {format_bytes(msg)}")

if __name__ == '__main__':
    main()