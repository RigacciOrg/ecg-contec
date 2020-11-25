#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parses ECG files produced by the Contec ECG90A electrocardiograph.
Can export in CSV or SCP-ECG format.
"""

import binascii
import datetime
import os.path
import struct
import sys
import ecg_scp as scp

__author__ = "Niccolo Rigacci"
__copyright__ = "Copyright 2019-2020 Niccolo Rigacci <niccolo@rigacci.org>"
__license__ = "GPLv3-or-later"
__email__ = "niccolo@rigacci.org"
__version__ = "0.1.0"

# File contains a fixed-lenght header and footer.
HEADER_LEN = 43
FOOTER_LEN = 37
# Numeric codes representing patient sex.
SEX_LABELS = {0: 'F', 1: 'M', 255: 'Unknown'}
# Numeric value representing invalid data.
NULL_VALUE = 0x6800
# Sampling parameters for the Contec ECG90A device.
ECG90A_SAMPLE_BITS = 16
ECG90A_DATA_SERIES = 8
ECG90A_SAMPLE_RATE = 800
ECG90A_AMPL_NANOVOLT = 5000
# Shift the X axis by this value, to make it zero-centered.
ECG90A_XOFFSET = -2048
# Mapping from ECG90A to SCP-ECG definitions.
ECG90A_LEADS = {
    0:  scp.LEAD_I,
    1:  scp.LEAD_II,
    2:  scp.LEAD_III,
    3:  scp.LEAD_AVR,
    4:  scp.LEAD_AVL,
    5:  scp.LEAD_AVF,
    6:  scp.LEAD_V1,
    7:  scp.LEAD_V2,
    8:  scp.LEAD_V3,
    9:  scp.LEAD_V4,
    10: scp.LEAD_V5,
    11: scp.LEAD_V6
}

# How many columns to include into CSV exported files.
DEFAULT_CSV_COLUMNS = 12

class ecg():

    def __init__(self, filename, sample_rate=ECG90A_SAMPLE_RATE, data_series=ECG90A_DATA_SERIES, sample_bits=ECG90A_SAMPLE_BITS):
        if not os.path.exists(filename):
            print(u'ERROR: Input file %s does not exists' % (filename,))
            return None
        if (sample_bits % 8) != 0:
            print(u'ERROR: sample_bits is not multiple of 8')
            return None
        self.filename = filename
        self.sample_rate = sample_rate
        self.data_series = data_series
        self.sample_bits = sample_bits
        # Get some metadata from file size.
        self.file_size = os.path.getsize(filename)
        self.file_timestamp = datetime.datetime.fromtimestamp(os.path.getmtime(filename))
        self.payload_len = self.file_size - HEADER_LEN - FOOTER_LEN
        bytes_per_sample = self.data_series * int(self.sample_bits / 8)
        if (self.payload_len % bytes_per_sample) != 0:
            print(u'ERROR: File size mismatch: (%d - %d - %d) = %d is not multiple of %d' % (self.file_size, HEADER_LEN, FOOTER_LEN, self.payload_len, bytes_per_sample))
            return None
        self.samples = int(self.payload_len / bytes_per_sample)
        self.duration = float(self.samples / self.sample_rate)
        # Read the header.
        with open(filename, 'rb') as f:
            self.case = self.asciiz(f.read(8))
            self.unknown1 = f.read(2)
            self.timestamp = self.asciiz(f.read(20))
            self.unknown2 = f.read(2)
            self.patient_name = self.asciiz(f.read(8))
            self.patient_sex = int.from_bytes(f.read(1), byteorder='little')  # 0: F, 1: M, 255: Blank
            self.patient_age = int.from_bytes(f.read(1), byteorder='little')  # Max is 200.
            self.patient_weight = int.from_bytes(f.read(1), byteorder='little')
            if self.patient_sex in SEX_LABELS:
                self.patient_sex_label = SEX_LABELS[self.patient_sex]
            else:
                self.patient_sex_label = 'Unknown code %s' % (self.patient_sex,)

    def asciiz(self, byte_str):
        return byte_str.decode('utf-8').split('\0', 1)[0]


    def readline(self, xoffset=ECG90A_XOFFSET, cols=DEFAULT_CSV_COLUMNS):
        """ Iterate data one row (list of values) at a time """

        f_in = open(self.filename, 'rb')
        f_in.seek(HEADER_LEN)
        bytes_per_sample = int(self.sample_bits / 8)
        empty_rows = 0
        while True:
            row = []
            # Read a sampled value for each data serie.
            for i in range(0, self.data_series):
                data = f_in.read(bytes_per_sample)
                if len(data) < bytes_per_sample:
                    print(u'DEBUG: Short read: only %d byte(s) => %s' % (len(data), data))
                    data = None
                    break
                # Convert bytes into signed integer.
                value = int.from_bytes(data, byteorder='little')
                # Out-of-scale value is 26624 (0x6800).
                if value == NULL_VALUE:
                    value = None
                else:
                    # Normalize the values shifting by xoffset.
                    value += xoffset
                row.append(value)
            # At the end of data there should be two zero rows plus 5 zero bytes = FOOTER_LEN of zeroes.
            if data is None:
                unused_values = len(row)
                if empty_rows != 2 and unused_values != 2:
                    print(u'WARNING: Data does not terminate with %d zero bytes' % (FOOTER_LEN,))
                print(u'DEBUG: End of file: zero rows: %d, unused values: %s' % (empty_rows, unused_values))
                # Terminate iterator.
                break
            # Discard all-zeroes rows, that should appear only at the end of data.
            if row == [xoffset] * self.data_series:
                empty_rows += 1
                continue
            # Found a zeroes row, but not at the end of data: terminate the iterator.
            if empty_rows != 0:
                print(u'ERROR: Rows with all zeroes are not expected within data.')
                break
            # Assume that the first two data series are lead II and lead III,
            # so calculate I, avR, avL and avF using the Einthoven formulas.
            if self.data_series >= 2:
                lead_ii  = row[0]
                lead_iii = row[1]
                if lead_ii is not None and lead_iii is not None:
                    lead_i   = lead_ii - lead_iii
                    lead_avr = int(lead_iii / 2) - lead_ii
                    lead_avl = int(lead_ii  / 2) - lead_iii
                    lead_avf = int((lead_ii + lead_iii) / 2)
                else:
                    lead_i   = None
                    lead_avr = None
                    lead_avl = None
                    lead_avf = None
            ecg_row = [lead_i, lead_ii, lead_iii, lead_avr, lead_avl, lead_avf] + row[2:]
            yield ecg_row[0:cols]
        f_in.close()


    def export_csv(self, filename=None, overwrite=False, as_millivolt=False, xoffset=ECG90A_XOFFSET, cols=DEFAULT_CSV_COLUMNS):
        """ Export ECG data into a CSV format file """

        if filename is None:
            filename_csv = self.filename + u'.csv'
        else:
            filename_csv = filename
        if os.path.exists(filename_csv) and not overwrite:
            print(u'WARNING: Output file "%s" already exists, will not overwrite.' % (filename_csv,))
            return None
        amplitude_mult = float(ECG90A_AMPL_NANOVOLT) / 1000000.0
        with open(filename_csv, 'w') as f:
            for row in self.readline(xoffset=xoffset, cols=cols):
                if as_millivolt:
                    f.write(','.join(scp.csv_format(x, multiplier=amplitude_mult) for x in row) + '\n')
                else:
                    f.write(','.join(scp.csv_format(x, num_format=u'%d') for x in row) + '\n')


    def export_scp(self, filename=None, overwrite=False, xoffset=ECG90A_XOFFSET):
        """ Export data into a SCP-ECF file """

        if filename is None:
            filename_scp = self.filename + u'.scp'
        else:
            filename_scp = filename
        if os.path.exists(filename_scp) and not overwrite:
            print(u'WARNING: Output file "%s" already exists, will not overwrite.' % (filename_scp,))
            return None

        # Section pointers are required at least from #0 to #11.
        s = {}
        for sect_id in range(0, 12):
            s[sect_id] = b''

        # Prepare Section #1 - Patient Data
        # Patient sex.
        if self.patient_sex == 1:
            sex_code = scp.SEX_MALE
        elif self.patient_sex == 0:
            sex_code = scp.SEX_FEMALE
        else:
            sex_code = scp.SEX_UNKNOWN
        # Patient age.
        age_unit = scp.AGE_UNSPECIFIED if self.patient_age == 0 else scp.AGE_YEARS
        # Date and time of acquisition
        try:
            t = datetime.datetime.strptime(self.timestamp, '%Y-%m-%d %H:%M:%S')
        except:
            t = self.file_timestamp
            print(u'WARNING: Cannot parse case time, using file timestamp "%s"' % (t.strftime('%Y-%m-%d %H:%M:%S'),))
        s[1]  = scp.make_tag(scp.TAG_PATIENT_ID, scp.make_asciiz(self.patient_name))
        s[1] += scp.make_tag(scp.TAG_ECG_SEQ_NUM, scp.make_asciiz(self.case))
        s[1] += scp.make_tag(scp.TAG_PATIENT_LAST_NAME, scp.make_asciiz(self.patient_name))
        s[1] += scp.make_tag(scp.TAG_PATIENT_SEX, struct.pack('<B', sex_code))
        s[1] += scp.make_tag(scp.TAG_PATIENT_AGE, scp.make_age(self.patient_age, age_unit))
        s[1] += scp.make_tag(scp.TAG_DATE_ACQ, scp.make_date(t))
        s[1] += scp.make_tag(scp.TAG_TIME_ACQ, scp.make_time(t))
        s[1] += scp.make_tag(scp.TAG_ACQ_DEV_ID, scp.make_machine_id('ECG90A'))
        s[1] += scp.make_tag(scp.TAG_EOF, b'')

        # Prepare Section #3 - ECG Lead Definition
        leads_number = 12
        flag_byte = 0b00000000
        flag_byte |= scp.ALL_SIMULTANEOUS_READ
        flag_byte |= (leads_number << 3)  # Simultaneous lead.
        s[3] = struct.pack('<B', leads_number)
        s[3] += struct.pack('<B', flag_byte)
        for i in range(0, leads_number):
            starting_sample = 1
            ending_sample = self.samples
            lead_id = ECG90A_LEADS[i]
            s[3] += struct.pack('<I', starting_sample)
            s[3] += struct.pack('<I', ending_sample)
            s[3] += struct.pack('<B', lead_id)

        # Prepare Section #6 - Rhythm data
        amplitude_multiplier = ECG90A_AMPL_NANOVOLT
        sample_time_interval = int(1000000 / self.sample_rate)  # In microseconds
        s[6] = struct.pack('<H', amplitude_multiplier)
        s[6] += struct.pack('<H', sample_time_interval)
        s[6] += struct.pack('<B', scp.ENCODING_REAL)
        s[6] += struct.pack('<B', scp.BIMODAL_COMPRESSION_FALSE)
        # Bytes to store for each serie, limited to 16bit size counter (sic!)
        bytes_to_store = int(self.samples * ECG90A_SAMPLE_BITS / 8)
        max_samples = int(0xffff / (ECG90A_SAMPLE_BITS / 8))
        if self.samples > max_samples:
            print(u'WARNING: Cannot store %d samples in SCP-ECG rhythm data, max is %d' % (self.samples, max_samples))
            bytes_to_store = int(max_samples * (ECG90A_SAMPLE_BITS / 8))
        for i in range(0, leads_number):
            s[6] += struct.pack('<H', bytes_to_store)
        all_rows = []
        for row in self.readline(xoffset=xoffset):
            all_rows.append(row)
        for i in range(0, leads_number):
            count = 0
            serie = b''
            for row in all_rows:
                val = row[i]
                # TODO: How to represent Null values in SCP-ECG?
                if val == None:
                    val = 0
                serie += struct.pack('<h', val)
                count += 1
                if count >= max_samples:
                    break
            s[6] += serie

        # Prepare Section #0 - Section Pointers
        sect_id = 0
        length = scp.SECTION_HEADER_LEN + scp.POINTER_FIELD_LEN * 12
        index = scp.SCPECG_HEADER_LEN + 1
        s[0] = scp.make_pointer_field(sect_id, length, index)
        index += length
        for sect_id in range(1, 12):
            length = len(s[sect_id])
            if length > 0:
                length += scp.SECTION_HEADER_LEN
            s[0] += scp.make_pointer_field(sect_id, length, index)
            index += length 

        # Prepare SCP-ECG Record
        # CRC(2bytes) + Size(4bytes) + Section #0 + Section #1 + ...
        size = scp.SCPECG_HEADER_LEN
        for sect_id in (0, 1, 2, 3, 6):
            if len(s[sect_id]) > 0:
                size += scp.SECTION_HEADER_LEN + len(s[sect_id])
        scp_ecg = struct.pack('<I', size)
        for sect_id in (0, 1, 2, 3, 6):
            if len(s[sect_id]) > 0:
                scp_ecg += scp.pack_section(sect_id, s[sect_id])
        crc = struct.pack('<H', binascii.crc_hqx(scp_ecg, 0xffff))

        f_out = open(filename_scp, 'wb')
        f_out.write(crc + scp_ecg)
        f_out.close()
