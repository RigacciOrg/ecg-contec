#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import struct

class decoder():

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

        fmt = '{0:0%db}' % (size,)
        #print('DEBUG: Iterator terminated')
        if size > 0:
            print('WARNING: Unmatched Huffman prefix = %s' % (fmt.format(huffman_prefix),))
