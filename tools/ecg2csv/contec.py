#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parses ECG files produced by the Contec ECG90A electrocardiograph.
"""

import os.path
import sys

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
# Default sampling parameters.
DEFAULT_SAMPLE_BITS = 16
DEFAULT_DATA_SERIES = 8
DEFAULT_SAMPLE_RATE = 800
# Shift the X axis by this value, to make it zero-centered.
DEFAULT_XOFFSET = -2048
# How many columns to include into CSV exported files.
DEFAULT_CSV_COLUMNS = 12

class ecg():

    def __init__(self, filename, sample_rate=DEFAULT_SAMPLE_RATE, data_series=DEFAULT_DATA_SERIES, sample_bits=DEFAULT_SAMPLE_BITS):
        if not os.path.exists(filename):
            print(u'ERROR: Input file %s does not exists' % (filename,))
            return None
        if (sample_bits % 8) != 0:
            print(u'ERROR: sample_bits is not multiple of 8')
            return None
        self.filename = filename
        self.data_series = data_series
        self.sample_bits = sample_bits
        # Get some metadata from file size.
        self.file_size = os.path.getsize(filename)
        self.payload_len = self.file_size - HEADER_LEN - FOOTER_LEN
        bytes_per_sample = self.data_series * int(self.sample_bits / 8)
        if (self.payload_len % bytes_per_sample) != 0:
            print(u'ERROR: File size mismatch: (%d - %d - %d) = %d is not multiple of %d' % (self.file_size, HEADER_LEN, FOOTER_LEN, self.payload_len, bytes_per_sample))
            return None
        self.samples = int(self.payload_len / bytes_per_sample)
        self.duration = float(self.samples / sample_rate)
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

    def export_csv(self, filename=None, overwrite=False, xoffset=DEFAULT_XOFFSET, cols=DEFAULT_CSV_COLUMNS):
        if filename is None:
            filename_csv = self.filename + u'.csv'
        else:
            filename_csv = filename
        if os.path.exists(filename_csv) and not overwrite:
            print(u'WARNING: Output file "%s" already exists, will not overwrite.' % (filename_csv,))
            return None

        f_in = open(self.filename, 'rb')
        f_out = open(filename_csv, 'w')

        f_in.seek(HEADER_LEN)
        read_bytes = int(self.sample_bits / 8)
        zero_rows = 0
        while True:
            samples_row = []
            for i in range(0, self.data_series):
                # Read sample
                sample = f_in.read(read_bytes)
                if len(sample) < read_bytes:
                    print(u'DEBUG: Short read: only %d byte(s) => %s' % (len(sample), sample))
                    sample = b''
                    break
                sample_val = int.from_bytes(sample, byteorder='little')
                # Out-of-scale value is 26624 (0x6800).
                if sample_val == NULL_VALUE:
                    sample_val = ''
                else:
                    # Normalize values shifting by xoffset.
                    sample_val += xoffset
                samples_row.append(sample_val)

            if sample == b'':
                # Last sample is empty, the row is incomplete, end of data.
                # There should be 2 zero rows plus 5 zero bytes = FOOTER_LEN of zeroes.
                orphan_samples = len(samples_row)
                if zero_rows != 2 and orphan_samples != 2:
                    print(u'WARNING: Data does not terminate with %d zero bytes' % (FOOTER_LEN,))
                print(u'DEBUG: End of file: zero rows: %d, orphan values: %s' % (zero_rows, orphan_samples))
                break

            # Discard all-zeroes rows at the end of data.
            if samples_row == [xoffset] * self.data_series:
                zero_rows += 1
                continue
            if zero_rows != 0:
                print(u'ERROR: Rows with all zeroes are not expected within data.')
                break

            if self.data_series >= 2:
                # Assume that the first two data series are lead II and lead III,
                # Calculate I, avR, avL and avF using the Einthoven formulas.
                lead_ii  = samples_row[0]
                lead_iii = samples_row[1]
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
            ecg_row = [lead_i, lead_ii, lead_iii, lead_avr, lead_avl, lead_avf] + samples_row[2:]
            f_out.write(','.join(str(x) for x in ecg_row[0:cols]) + '\n')
        f_out.close()
        f_in.close()
