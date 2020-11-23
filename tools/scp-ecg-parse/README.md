# Python script to read and parse SCP-ECG cardiogram files

This is just a proof-of-concept script to read SCP-ECG 
cardiogram files and convert them into CSV format. It supports a 
very limited subset of the **ANSI/AAMI EC71:2001** 
specifications.

The script parses the following sections:

* **Section #0** - **Pointer Section**: read the main structure 
of the file.
* **Section #1** - **Patient Data**, with support to only a 
limited number of tags.
* **Section #2** - **Huffman tables**: only the default SCP-ECG 
Huffman table is supported. Custom tables and switching table 
during encoding is not supported.
* **Section #3** - **ECG lead definition**.
* **Section #6** - **Rhythm data**: only "second difference" 
sequences are supported. Bimodal compression, reference beat 
compression, etc. are not supported.

## The SCP-ECG standard format

It is a shame that the **ANSI/AAMI EC71:2001** specifications 
are available by payment at the astronomical price of $225.00 
(webstore.ansi.org): it is not surprise that support for this 
standard is very poor in software.

## How to execute the script

The script is actually tested only against the **Example.scp** 
file that you can find into the 
[../../examples/](../../examples/README.md) directory.

Copy both files **scp-ecg-parse** and **huffman.py** into your 
working directory, along with the **Example.scp** file, then 
execute:

```
./scp-ecg-parse Example.scp
```

Several info about the sections are printed to the standard 
output, followed by the CSV dump of the original values.

## Web References

* Python Module for Huffman Encoding and Decoding:
  * https://pypi.org/project/dahuffman/
  * https://github.com/soxofaan/dahuffman
* Python code to do Huffman coding using bitarray:
  * http://ilan.schnell-web.net/prog/huffman/
  * https://github.com/ilanschnell/bitarray/blob/master/examples/huffman/huffman.py
  * https://github.com/jerabaul29/python_huffman
