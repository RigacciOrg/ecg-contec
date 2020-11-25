# Electrocardiogram Example Files

### 0000037.ECG

ECG acquired using a **Contec ECG90A** device. Only the limb 
leads were attached. Precordial (chest) electrodes were not 
connected, so V1, ..., V6 have no data. Patient name, sex, age 
and weigth are filled with data. The recording is about 10 
seconds long. It was acquired whit no active filters and a 
strong 50Hz noise is present.


### Example.scp

This is an example file provided with the source code of 
**C# ECG Toolkit**, a software toolkit to convert, view and print 
electrocardiograms (downloaded from
[sourceforge.net](https://sourceforge.net/projects/ecgtoolkit-cs/)).
The file contains a 12-leads electrocardiogram encoded into the 
**SCP-ECG** format:

  * Sections #0, #1, #2, #3, #4, #5, #6 and #7 are present.
  * The file contains 5000 samples per lead.
  * Acquiring interval is 2000 us (500 Hz).
  * Data stream is encoded using the default SCP-ECG Huffman table.
  * Data are signed integers, representing the "second difference" of the original data.
  * The referece unit of the restored sequence is 2500 nV; it must be multiplied by 2.5 to obtain mV.
  * No bimodal compression, no reference beat compression.

### demo.scp

This is an example file provided with the **ECG Viewer** program
(free version for MS-Windows) downloaded from
[www.ecg-soft.com](http://www.ecg-soft.com/ecgviewer/ecgviewer.htm).
The file contains an 8-leads recording (2 limb and 6 precordial) 
encoded into the **SCP-ECG** format:

  * Sections #0, #1, #3 and #6 are present.
  * The file contains 10000 samples per lead.
  * Acquiring interval is 1000 us (1 KHz).
  * Data stream is stored raw (no Huffman encoding).
  * Data are signed integers of real data (no sequence of differences).
  * The referece unit of the restored sequence is 183 nV.
  * No bimodal compression, no reference beat compression.
