#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Helper module to read and write SCP-ECG electrocardiogram files.
It implements a limited subset of ANSI-AAMI EC71:2001 specifications.
"""

import binascii
import struct

__author__ = "Niccolo Rigacci"
__copyright__ = "Copyright 2019-2020 Niccolo Rigacci <niccolo@rigacci.org>"
__license__ = "GPLv3-or-later"
__email__ = "niccolo@rigacci.org"
__version__ = "0.1.0"

SCPECG_HEADER_LEN = 6
SECTION_HEADER_LEN = 16
POINTER_FIELD_LEN = 10
MIN_POINTER_FIELDS = 12
SECTION_1_TAG_TERMINATOR = 255
DEFAULT_HUFFMAN_TABLE = 19999

# SECTION #1 - Patient Data - Tags
TAG_PATIENT_LAST_NAME = 0
TAG_PATIENT_FIRST_NAME = 1
TAG_PATIENT_ID = 2
TAG_PATIENT_SECOND_LAST_NAME = 3
TAG_PATIENT_AGE = 4
TAG_PATIENT_DATE_OF_BIRTH = 5
TAG_PATIENT_SEX = 8
TAG_DRUGS = 10
TAG_DIAG_INDICATION = 13
TAG_ACQ_DEV_ID = 14
TAG_ANALYZ_DEV_ID = 15
TAG_ACQ_INST_DESC = 16
TAG_ANALYZ_INST_DESC = 17
TAG_ACQ_DEPT_DESC = 18
TAG_ANALYZ_DEPT_DESC = 19
TAG_REF_PHYSICIAN = 20
TAG_LATEST_PHYSICIAN = 21
TAG_TECHNICIAN_DESC = 22
TAG_ROOM_DESC = 23
TAG_DATE_ACQ = 25
TAG_TIME_ACQ = 26
TAG_FREE_TEXT = 30
TAG_ECG_SEQ_NUM = 31
TAG_HIST_DIAG_CODES = 32
TAG_DATE_TIME_ZONE = 34
TAG_TEXT_MED_HIST = 35
TAG_EOF = 255
TAG = {
    TAG_PATIENT_LAST_NAME: 'Patient Last Name',
    TAG_PATIENT_FIRST_NAME: 'Patient First Name',
    TAG_PATIENT_ID: 'Patient ID',
    TAG_PATIENT_SECOND_LAST_NAME: 'Second Last Name',
    TAG_PATIENT_AGE: 'Patient Age',
    TAG_PATIENT_DATE_OF_BIRTH: 'Patient Date of Birth',
    TAG_PATIENT_SEX: 'Patient Sex',
    TAG_DRUGS: 'Drugs',
    TAG_DIAG_INDICATION: 'Diagnosis or Referral Indication',
    TAG_ACQ_DEV_ID: 'Acquiring Device Id',
    TAG_ANALYZ_DEV_ID: 'Analyzing Device Id',
    TAG_ACQ_INST_DESC: 'Acquiring Institution Description',
    TAG_ANALYZ_INST_DESC: 'Analyzing Institution Description',
    TAG_ACQ_DEPT_DESC: 'Acquiring Department Description',
    TAG_ANALYZ_DEPT_DESC: 'Analyzing Department Description',
    TAG_REF_PHYSICIAN: 'Referring Physician',
    TAG_LATEST_PHYSICIAN: 'Latest Confirming Physician',
    TAG_TECHNICIAN_DESC: 'Technician Description',
    TAG_ROOM_DESC: 'Room Description',
    TAG_DATE_ACQ: 'Date of Acquisition',
    TAG_TIME_ACQ: 'Time of Acquisition',
    TAG_FREE_TEXT: 'Free Text',
    TAG_ECG_SEQ_NUM: 'ECG Sequence Number',
    TAG_HIST_DIAG_CODES: 'History diagnostic codes',
    TAG_DATE_TIME_ZONE: 'Date Time Zone',
    TAG_TEXT_MED_HIST: 'Free-text Medical History',
    TAG_EOF: 'End of section'
}

# Section #1 - Patient Data - Sex
SEX_UNKNOWN = 0
SEX_MALE = 1
SEX_FEMALE = 2
SEX_UNSPECIFIED = 9
SEX = {
    SEX_UNKNOWN: u'Not Known', 
    SEX_MALE: u'Male', 
    SEX_FEMALE: u'Female', 
    SEX_UNSPECIFIED: u'Unspecified'
}

# Section #1 - Patient Data - Age
AGE_UNSPECIFIED = 0
AGE_YEARS = 1
AGE_MONTHS = 2
AGE_WEEKS = 3
AGE_DAYS = 4
AGE_HOURS = 5
AGE = {
    AGE_UNSPECIFIED: 'Unspecified', 
    AGE_YEARS: 'Years', 
    AGE_MONTHS: 'Months', 
    AGE_WEEKS: 'Weeks', 
    AGE_DAYS: 'Days', 
    AGE_HOURS: 'Hours'
}

# Section #1 - Patient Data - Tags type
TAGS_MANDATORY = [2, 14, 25, 26]
TAGS_TYPE_DATE = [5, 25]
TAGS_TYPE_TIME = [26]
TAGS_TYPE_AGE = [4]
TAGS_TYPE_ASCIIZ = [0, 1, 2, 3, 13, 16, 17, 18, 19, 20, 21, 22, 23, 30, 31, 35]
TAGS_TYPE_MACHINE_ID = [14, 15]

# Section #3 - Lead Definition
# Numbering scheme from ANSI-AAMI EC71:2001
# Standard lead names for 12-lead electrocardiogram:
LEAD_I = 1
LEAD_II = 2
LEAD_III = 61
LEAD_AVR = 62
LEAD_AVL = 63
LEAD_AVF = 64
LEAD_V1 = 3
LEAD_V2 = 4
LEAD_V3 = 5
LEAD_V4 = 6
LEAD_V5 = 7
LEAD_V6 = 8
# Alternative names?
LEAD_I_CAL = 31
LEAD_II_CAL = 32
LEAD_LA_CAL = 51
LEAD_RA_CAL = 52
LEAD_LL_CAL = 53
LEAD = {
    1: 'I',
    2: 'II',
    3: 'V1',
    4: 'V2',
    5: 'V3',
    6: 'V4',
    7: 'V5',
    8: 'V6',
    9: 'V7',
    10: 'V2R',
    11: 'V3R',
    12: 'V4R',
    13: 'V5R',
    14: 'V6R',
    15: 'V7R',
    16: 'X',
    17: 'Y',
    18: 'Z',
    19: 'CC5',
    20: 'CM5',
    21: 'LA',
    22: 'RA',
    23: 'LL',
    24: 'I',
    25: 'E',
    26: 'C',
    27: 'A',
    28: 'M',
    29: 'F',
    30: 'H',
    31: 'I-cal',
    32: 'II-cal',
    33: 'V1-cal',
    34: 'V2-cal',
    35: 'V3-cal',
    36: 'V4-cal',
    37: 'V5-cal',
    38: 'V6-cal',
    39: 'V7-cal',
    40: 'V2R-cal',
    41: 'V3R-cal',
    42: 'V4R-cal',
    43: 'V5R-cal',
    44: 'V6R-cal',
    45: 'V7R-cal',
    46: 'X-cal',
    47: 'Y-cal',
    48: 'Z-cal',
    49: 'CC5-cal',
    50: 'CM5-cal',
    51: 'Left Arm-cal',
    52: 'Right Arm-cal',
    53: 'Left Leg-cal',
    54: 'I-cal',
    55: 'E-cal',
    56: 'C-cal',
    57: 'A-cal',
    58: 'M-cal',
    59: 'F-cal',
    60: 'H-cal',
    61: 'III',
    62: 'aVR',
    63: 'aVL',
    64: 'aVF'
}

ALL_SIMULTANEOUS_READ = 0b100  # Leads all simultaneously read.

# Section #6 - Rhythm Data
ENCODING_REAL = 0
ENCODING_FIRST_DIFF = 1
ENCODING_SECOND_DIFF = 2
ENCODING = {
    ENCODING_REAL: 'Real (zero difference)',
    ENCODING_FIRST_DIFF: 'First difference',
    ENCODING_SECOND_DIFF: 'Second difference'
}

BIMODAL_COMPRESSION_FALSE = 0
BIMODAL_COMPRESSION_TRUE = 1
BIMODAL_COMPRESSION = {
    BIMODAL_COMPRESSION_FALSE: 'Not used', 
    BIMODAL_COMPRESSION_TRUE: 'Bimodal'
}

MEASURE_NOT_COMPUTED = 29999
MEASURE_LEAD_REJECTED = 29998
MEASURE_WAVE_NOT_PRESENT = 19999

def csv_format(val, none_as_empty=True, num_format=u'%.6f', multiplier=1):
    """ Return the value formatted as string suitable for CSV output """
    if val == None:
        if none_as_empty:
            return u''
        else:
            return num_format % (0,)
    else:
        return num_format % (val * multiplier,)

def make_date(d):
    """ Return a 4-bytes SCP-ECG encoded date from a datetime object """
    return struct.pack('<H', d.year) + struct.pack('<B', d.month) + struct.pack('<B', d.day)

def make_time(d):
    """ Return a 3 bytes SCP-ECG encoded time from a datetime object """
    return struct.pack('<B', d.hour) + struct.pack('<B', d.minute) + struct.pack('<B', d.second)

def make_age(age, unit):
    """ Return a 3 bytes SCP-ECG encoded age object """
    return struct.pack('<H', age) + struct.pack('<B', unit)

def make_asciiz(s):
    """ Return a zero-terminated string """
    return s.encode('utf-8') + b'\0'

def make_tag(tag, data):
    """ Return a patient tag for Section #1 """
    return struct.pack('<B', tag) + struct.pack('<H', len(data)) + data

def make_pointer_field(sect, length, index):
    """ Return a Section Pointer field (10 bytes) """
    index = 0 if length == 0 else index
    return struct.pack('<H', sect) + struct.pack('<I', length) + struct.pack('<I', index)

def make_machine_id(s):
    """ Return an (almos empty) SCP-ECG machine parameter """
    s += u'\0' * 6
    text = s.encode('utf-8')[0:5] + b'\0'
    return (8 * b'\0') + text + (23 * b'\0')

def pack_section(sect, data_part):
    """ Return a Section structure prepending CRC and header to data part """
    sect_id = struct.pack('<H', sect)
    length = struct.pack('<I', SECTION_HEADER_LEN + len(data_part))
    version = struct.pack('<B', 0x14)
    protocol = struct.pack('<B', 0x14)
    reserved = b'SCPECG' if sect == 0 else b'\0' * 6
    buff = sect_id + length + version + protocol + reserved + data_part
    crc = struct.pack('<H', binascii.crc_hqx(buff, 0xffff))
    return crc + buff

def parse_asciiz(data):
    return data.decode('utf-8').split('\0', 1)[0]


def parse_age(data):
    age = int.from_bytes(data[0:2], byteorder='little')
    unit = int.from_bytes(data[2:3], byteorder='little')
    if unit not in AGE:
        unit = 0
    if age == 0 and unit == 0:
        return 'Not specified'
    else:
        return '%d %s' % (age, AGE[unit])

def parse_date(data):
    """ Convert a date from 4-bytes SCP-ECG format to ISO YYYY-MM-DD format """
    year = int.from_bytes(data[0:2], byteorder='little')
    month = int.from_bytes(data[2:3], byteorder='little')
    day = int.from_bytes(data[3:4], byteorder='little')
    if (month < 1 or month > 12) or (day < 1 or day > 31):
        print(u'WARNING: Invalid date: %d-%d-%d (%s)' % (year, month, day, data))
        year, month, day = 0, 0, 0
    return '%04d-%02d-%02d' % (year, month, day)

def parse_time(data):
    """ Convert a time from 3-bytes SCP-ECG format to HH:MM:SS format """
    hours = int.from_bytes(data[0:1], byteorder='little')
    minutes = int.from_bytes(data[1:2], byteorder='little')
    seconds = int.from_bytes(data[2:3], byteorder='little')
    if (hours > 23 or minutes > 59 or seconds > 59):
        print(u'WARNING: Invalid time: %d:%d:%d (%s)' % (hours, minutes, seconds, data))
        hours, minutes, seconds = 0, 0, 0
    return '%02d:%02d:%02d' % (hours, minutes, seconds)

def parse_machine_id(data):
    """ Convert an SCP-ECG machine parameter data into a string """
    institute_n  = int.from_bytes(data[1:3], byteorder='little')
    department_n = int.from_bytes(data[3:5], byteorder='little')
    device_id    = int.from_bytes(data[5:7], byteorder='little')
    device_type  = int.from_bytes(data[7:8], byteorder='little')
    model = parse_asciiz(data[8:14])
    return 'Inst. %d, Dept. %d, Dev. %d, Type %d, Model "%s"' % (institute_n, department_n, device_id, device_type, model)


def read_section_header(fp, offset):
    """ Read an SCP-ECG section header (16 bytes) and check the CRC """
    h = {}
    fp.seek(offset)
    h['crc'] = int.from_bytes(fp.read(2), byteorder='little')
    h['id'] = int.from_bytes(fp.read(2), byteorder='little')
    h['length'] = int.from_bytes(fp.read(4), byteorder='little')
    h['version'] = int.from_bytes(fp.read(1), byteorder='little')
    h['protocol'] = int.from_bytes(fp.read(1), byteorder='little')
    h['reserved'] = fp.read(6)
    fp.seek(offset + 2)
    h['calc_crc'] = binascii.crc_hqx(fp.read(h['length'] - 2), 0xffff)
    if h['crc'] != h['calc_crc']:
        print(u'ERROR: Section CRC check failed')
        sys.exit(1)
    return h


def print_section_header(i, h, label=''):
    """ Print data from the the section header """
    print()
    print(u'==== Section #%d: %s ====' % (i, label))
    print(u'Section CRC:      0x%04X' % (h['crc'],))
    print(u'Section Id:       0x%04X' % (h['id'],))
    print(u'Section length:   %d'     % (h['length'],))
    print(u'Section version:  0x%02X' % (h['version'],))
    print(u'Protocol version: 0x%02X' % (h['protocol'],))
    print(u'Calculated CRC:   0x%04X' % (h['calc_crc'],))


def read_parameter(fp):
    """ Read a parameter from patient data (Section #1) """
    tag = int.from_bytes(fp.read(1), byteorder='little')
    length = int.from_bytes(fp.read(2), byteorder='little')
    value = fp.read(length)
    if tag in TAGS_TYPE_DATE:
        value = parse_date(value)
    elif tag in TAGS_TYPE_TIME:
        value = parse_time(value)
    elif tag in TAGS_TYPE_ASCIIZ:
        value = parse_asciiz(value)
    elif tag == TAG_PATIENT_SEX:
        value = int.from_bytes(value, byteorder='little')
        if value in SEX:
            value = SEX[value]
        else:
            value = u'Invalid %d' % (value)
    elif tag in TAGS_TYPE_AGE:
        value = parse_age(value)
    elif tag in TAGS_TYPE_MACHINE_ID:
        value = parse_machine_id(value)
    if tag in TAG:
        tag_label = TAG[tag]
    else:
        tag_label = u'Unknown %d' % (tag,)
    return (tag, tag_label, length, value)


class second_diff():
    """ Reconstruct a sequence from Second Differences """
    def __init__(self):
        self.previous_val = None
        self.previous_diff1 = None
    def val(self, diff2):
        if self.previous_val == None:
            self.previous_val = diff2
            return diff2
        if self.previous_diff1 == None:
            self.previous_diff1 = diff2 - self.previous_val
            self.previous_val = diff2
            return diff2
        diff1 = self.previous_diff1 + diff2
        val = self.previous_val + diff1
        self.previous_val = val
        self.previous_diff1 = diff1
        return val


class raw_decoder():
    """ Iterator yielding signed two-byte integers from data """
    def decode(self, data):
        words = len(data)
        if (words % 2) != 0:
            print('WARNING: Data contains an odd number of bytes, shall be even')
            words -= 1
        for i in range(0, words, 2):
            yield struct.unpack('<h', data[i:i+2])[0]


class huffman_decoder():
    """ Iterator yielding signed two-byte integers from Huffman encoded data """

    # The SCP-ECG default Huffman table.
    _8bit = 511
    _16bit = 1023
    default_table = {
        ( 1, 0b0):            0,
        ( 3, 0b100):          1,
        ( 3, 0b101):         -1,
        ( 4, 0b1100):         2,
        ( 4, 0b1101):        -2,
        ( 5, 0b11100):        3,
        ( 5, 0b11101):       -3,
        ( 6, 0b111100):       4,
        ( 6, 0b111101):      -4,
        ( 7, 0b1111100):      5,
        ( 7, 0b1111101):     -5,
        ( 8, 0b11111100):     6,
        ( 8, 0b11111101):    -6,
        ( 9, 0b111111100):    7,
        ( 9, 0b111111101):   -7,
        (10, 0b1111111100):   8,
        (10, 0b1111111101):  -8,
        (10, 0b1111111110):  _8bit,
        (10, 0b1111111111):  _16bit
    }

    def decode(self, data):
        """ Iterator over data (bytes) """
        huffman_prefix = 0
        size = 0
        get_orig_bits = 0
        orig_bits_buffer = ''
        for byte in data:
            for m in [128, 64, 32, 16, 8, 4, 2, 1]:
                if get_orig_bits > 0:
                    # We are reading original bits for 8 or 16 bit value.
                    orig_bits_buffer += ('1' if (bool(byte & m)) else '0')
                    get_orig_bits -= 1
                    if get_orig_bits == 0:
                        #print('DEBUG: Read orig %dbit: %s' % (len(orig_bits_buffer), orig_bits_buffer))
                        # Pack as unsigned, then unpack as signed.
                        if len(orig_bits_buffer) == 8:
                            orig_val = struct.unpack('b', struct.pack('B', int(orig_bits_buffer, 2)))[0]
                        elif len(orig_bits_buffer) == 16:
                            orig_val = struct.unpack('h', struct.pack('H', int(orig_bits_buffer, 2)))[0]
                        else:
                            print('ERROR: Invalid bit buffer length: %d' % (len(orig_bits_buffer),))
                            return
                        yield orig_val
                        orig_bits_buffer = ''
                        huffman_prefix = 0
                        size = 0
                else:
                    # We are searching an Huffman prefix.
                    huffman_prefix = (huffman_prefix << 1) + bool(byte & m)
                    size += 1
                    if (size, huffman_prefix) in self.default_table:
                        symbol = self.default_table[size, huffman_prefix]
                        if symbol == self._8bit:
                            #print('DEBUG: Found 8 bit value')
                            get_orig_bits = 8
                        elif symbol == self._16bit:
                            #print('DEBUG: Found 16 bit value')
                            get_orig_bits = 16
                        else:
                            yield symbol
                            orig_bits_buffer = ''
                            huffman_prefix = 0
                            size = 0
        #print('DEBUG: Iterator terminated')
        fmt = '{0:0%db}' % (size,)
        if size > 0:
            print('WARNING: Unmatched Huffman prefix = %s' % (fmt.format(huffman_prefix),))
