# Python script to read and parse SCP-ECG cardiogram files.

This is just a proof-of-concept script to read SCP-ECG 
cardiogram files and convert them into CSV format. It supports a 
very limited subset of the **ANSI/AAMI EC71:2001** 
specifications.

The script parses the following sections:

* **Section #0** - Pointer Section: read the main structure of 
the file.
* **Section #1** - Patient Data, with only a limited number of 
tags.
* **Section #2** - Huffman tables: only the default SCP-ECG 
Huffman table is supported.
* **Section #3** - ECG lead definition.
* **Section #6** - Rhythm data: only "second difference" 
sequences are supported (no bimodal compression, no reference 
beat compression, etc.)

## The SCP-ECG standard format

It is a shame that the **ANSI/AAMI EC71:2001** specifications 
are available by payment at the astronomical price of $225.00 
(webstore.ansi.org): it is not surprise that support for this 
standard is very poor in software.

## Web References

* Python Module for Huffman Encoding and Decoding:
  * https://pypi.org/project/dahuffman/
  * https://github.com/soxofaan/dahuffman
* Python code to do Huffman coding using bitarray:
  * http://ilan.schnell-web.net/prog/huffman/
  * https://github.com/ilanschnell/bitarray/blob/master/examples/huffman/huffman.py
  * https://github.com/jerabaul29/python_huffman
