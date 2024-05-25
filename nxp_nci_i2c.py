#!/usr/bin/env python
from periphery import GPIO,I2C,sleep_ms

# debugging, is controlled by --debug {NONE,MSG,CMD,BOTH}
MSG_DEBUG = False # general debug statement
CMD_DEBUG = False # print raw commands to and from NFCC
TAG_DEBUG = False # print tag protocol parsing
def format_bytes(b): return ' '.join([f'{x:02X}' for x in b])
def print_debug(msg): print(msg) if MSG_DEBUG else None
def print_cmd(direction, b): print(direction + ' ' + format_bytes(b)) if CMD_DEBUG else None
def print_tag(msg): print(msg) if TAG_DEBUG else None

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

    def datapacket_xfer(self, datapacket):
        DataPacketHdr = [0x00, 0x00]
        self.send(DataPacketHdr + [len(datapacket)] + datapacket)
        r = []
        while r[:2] != DataPacketHdr:
            if self.has_data(): r = self.recv()
            else: break
        read_len = r[2]
        return r[3:3 +read_len] if r[:2] == DataPacketHdr else []

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
    global TAG_DEBUG

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
    parser.add_argument('--debug', help='Set debugging level (NONE,MSG,CMD,TAG,ALL)', default='NONE')
    args = parser.parse_args()

    MSG_DEBUG = ('MSG' in args.debug or 'ALL' in args.debug)
    CMD_DEBUG = ('CMD' in args.debug or 'ALL' in args.debug)
    TAG_DEBUG = ('TAG' in args.debug or 'ALL' in args.debug)

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
                tag_type = process_tag(r)
                if tag_type == 'Mifare Ultralight':
                    mifare_ultralight_read(nfcc)
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
    print_debug(f"Tag said hello with {format_bytes(msg)}")
    # Table 80 from https://nfc-forum.org/uploads/specifications/27-NFCForum-TS-NCI-2.3.pdf
    MT = {0x00: 'DAT', 0x20: 'CMD', 0x40: 'RSP', 0x60: 'NTF'}
    GID = {0x0: 'NCI Core', 0x1: 'RF Mgmt', 0x2: 'NFCEE Mgmt', 0x3: 'NFC Mgmt'}
    ConnID = {0x0: 'StaticRF', 0x1: 'StaticHCI'}
    OID_RFmgmt = {0x0: 'DISCOVER_MAP', 0x1: 'SET_LISTEN_MODE_ROUTING', 0x2: 'GET_LISTEN_MODE_ROUTING', 0x3: 'DISCOVER', 0x4: 'DISCOVER_SELECT', 0x5: 'INTF_ACTIVATED', 0x6: 'DEACTIVATE', 0x7: 'FIELD_INFO'}
    RF_Intf = {0x0: 'NFCEE Direct', 0x1: 'Frame', 0x2: 'ISO-DEP', 0x3: 'NFC-DEP', 0x6: 'NDEF', 0x7: 'WLC-P Autonomous'}
    RF_Proto = {0x2: 'T2T', 0x3: 'T3T', 0x4: 'ISO-DEP', 0x5: 'NFC-DEP', 0x6: 'T5T', 0x7: 'NDEF', 0x8: 'WLC'}
    RF_T_M = {0x0: 'NFC A Passive Poll', 0x1: 'NFC B Passive Poll', 0x2: 'NFC F Passive Poll', 0x3: 'NFC Active Poll', 0x6: 'NFC V Passive Poll',
            0x80: 'NFC A Passive Listen', 0x81: 'NFC B Passive Listen', 0x82: 'NFC F Passive Listen', 0x83: 'NFC Active Listen'}
    Bitrates = {0x0: 106, 0x1: 212, 0x2: 424, 0x3: 848, 0x4: 1695, 0x5: 3390, 0x6: 6780, 0x20: 26}

    if msg[0] >> 5:
        print_tag(f'{msg[0]:02X}: MT={msg[0] & 0b11100000:02X}: {MT[msg[0] & 0b11100000]}, GID={msg[0] & 0xf}: {GID[msg[0] & 0xf]}')
    else:
        print_tag(f'{msg[0]:02X}: MT={msg[0] & 0b11100000:02X}: {MT[msg[0] & 0b11100000]}, ConnID={msg[0] & 0xf}: {ConnID[msg[0] & 0xf]}')
    print_tag(f'{msg[1]:02X}: OID={OID_RFmgmt[msg[1]]}')
    print_tag(f'{msg[2]:02X}: payload len: {msg[2]}')
    print_tag('===< payload >===')
    print_tag(f'{msg[3]:02X}: RF Discovery ID: {msg[3]}')
    print_tag(f'{msg[4]:02X}: RF Interface: {RF_Intf[msg[4]]}')
    print_tag(f'{msg[5]:02X}: RF Protocol: {RF_Proto[msg[5]]}')
    protocol = msg[5]
    print_tag(f'{msg[6]:02X}: Activation RF Technology and Mode: {RF_T_M[msg[6]]}')
    mode = msg[6]
    print_tag(f'{msg[7]:02X}: Max Data Packet Payload Size: {msg[7]}')
    print_tag(f'{msg[8]:02X}: Initial Number of Credits: {msg[8]}')
    print_tag(f'{msg[9]:02X}: Length of RF Technology Specific Parameters: {msg[9]}')
    RFTparams_length = msg[9]
    print_tag(f'{format_bytes(msg[10:10 +RFTparams_length])}: RF Technology Specific Parameters')
    sel_resp = process_techspecparams(mode, msg[10:10 +RFTparams_length])
    print_tag(f'{msg[10 +RFTparams_length]:02X}: Data Exchange RF Technology and Mode: {RF_T_M[msg[10 +RFTparams_length]]}')
    print_tag(f'{msg[11 +RFTparams_length]:02X}: Data Exchange Transmit Bit Rate: {Bitrates[msg[11 +RFTparams_length]]} kbps')
    print_tag(f'{msg[12 +RFTparams_length]:02X}: Data Exchange Receive Bit Rate: {Bitrates[msg[12 +RFTparams_length]]} kbps')
    print_tag(f'{msg[13 +RFTparams_length]:02X}: Length of Activation Parameters: {msg[13 +RFTparams_length]}')
    ACTparams_length = msg[13 +RFTparams_length]
    if ACTparams_length:
        ACTparams_idx = 14 +RFTparams_length
        print_tag(f'{format_bytes(msg[ACTparams_idx:ACTparams_idx +ACTparams_length])}: Activation Parameters:')

    tag_type = '<unknown/unimplemented>'
    if protocol == 0x2: # 'T2T'
        tag_type = 'iso14443 3A'
        if sel_resp == 0x00:
            tag_type = 'Mifare Ultralight'
        if sel_resp == 0x01:
            tag_type = 'Mifare Classic Skylander'
        if sel_resp in [0x08, 0x18]:
            tag_type = 'Mifare Classic'
    elif protocol == 0x3: # 'T3T'
        tag_type = 'Felica'
    elif protocol == 0x4: # 'ISO-DEP'
        if mode in [0x0, 0x80, 0x3, 0x83]:
            tag_type = 'ISO DEP - Type A'
        if mode in [0x1, 0x81]:
            tag_type = 'ISO DEP - Type B'
    print(f'* Tag detected: {tag_type}')
    if tag_type == '<unknown/unimplemented>': print('* rerun with --debug=TAG to debug')
    return tag_type

def process_techspecparams(mode, params):
    print_debug(f'Technology Specific Parameters: {mode:02X}: {format_bytes(params)}')
    sel_resp = None
    if mode == 0x0: # NFC A Passive Poll
        print_tag(f'  {format_bytes(params[:2])}: SENSE_RES Response')
        print_tag(f'  {params[2]:02X}: NFCID1 length: {params[2]}')
        nfcid1_length = params[2]
        print_tag(f'  {format_bytes(params[3:3 +nfcid1_length])}: NFCID1')
        print_tag(f'  {params[3 +nfcid1_length]:02X}: SEL_RES Response length (should be 1): {params[3 +nfcid1_length]}')
        print_tag(f'  {params[4 +nfcid1_length]:02X}: SEL_RES Response')
        sel_resp = params[4 +nfcid1_length]
    elif mode == 0x80: # NFC A Passive Listen
        print_tag('  No parameters defined for this mode')
    elif mode == 0x1: # NFC B Passive Poll
        print_tag(f'  {params[0]:02X}: SENSB_RES Response length: {params[0]}')
        SRResp_length = params[0]
        print_tag(f'  {format_bytes(params[1:1 +SRResp_length])}: SENSB_RES Response')
    elif mode == 0x81: # NFC B Passive Listen
        print_tag(f'  {params[0]:02X}: SENSB_REQ Command')
    elif mode == 0x2: # NFC F Passive Poll
        print_tag(f'  {params[0]:02X}: Bit Rate: {Bitrates[params[0]]} kbps')
        print_tag(f'  {params[1]:02X}: SENSF_RES Response length: {params[1]}')
        SRResp_length = params[1]
        print_tag(f'  {format_bytes(params[2:2 +SRResp_length])}: SENSF_RES Response')
    elif mode == 0x82: # NFC F Passive Listen
        print_tag(f'  {params[0]:02X}: NFCID2 length: {params[0]}')
        if params[0]: print_tag(f'  {format_bytes(params[1:9])}: NFCID2')
    elif mode == 0x6: # NFC V Passive Poll
        print_tag(f'  {params[0]:02X}: RES_FLAG')
        print_tag(f'  {params[1]:02X}: DSFID')
        print_tag(f'  {format_bytes(params[2:10])}: UID')
    elif mode == 0x3: # NFC Active Poll
        print_tag(f'  {params[0]:02X}: ATR_RES Response length: {params[0]}')
        ATRRes_length = params[0]
        print_tag(f'  {format_bytes(params[1:1 +ATRRes_length])}: ATR_RES Response')
    elif mode == 0x83: # NFC Active Listen
        print_tag(f'  {params[0]:02X}: ATR_REQ Command length: {params[0]}')
        ATRReq_length = params[0]
        print_tag(f'  {format_bytes(params[1:1 +ATRReq_length])}: ATR_REQ Command')
    return sel_resp

def mifare_ultralight_read(nfcc):
    ReadCmd = [0x30, 0x00];
    SectorSelect1Cmd = [0xC2, 0xFF];
    SectorSelect2Cmd = [0x01, 0x00, 0x00, 0x00];

    print(f'*-- Read response: {format_bytes(nfcc.datapacket_xfer(ReadCmd))}')
    print(f'*-- SectorSelect1 response: {format_bytes(nfcc.datapacket_xfer(SectorSelect1Cmd))}')
    print(f'*-- Read response: {format_bytes(nfcc.datapacket_xfer(ReadCmd))}')
    print(f'*-- SectorSelect2 response: {format_bytes(nfcc.datapacket_xfer(SectorSelect2Cmd))}')
    print(f'*-- Read response: {format_bytes(nfcc.datapacket_xfer(ReadCmd))}')

if __name__ == '__main__':
    main()