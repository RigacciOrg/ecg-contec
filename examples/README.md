# Electrocardiogram Example Files

### 0000037.ECG

ECG acquired using a **Contec ECG90A** device. Only the limb 
leads were attached. Precordial (chest) electrodes were not 
connected, so V1, ..., V6 have no data. Patient name, sex, age 
and weigth are filled with data. The recording is about 10 
seconds long. It was acquired whit no active filters and a 
strong 50Hz noise is present.


### Example.scp

This is an example file provided with the source code of C# ECG 
Toolkit, a software toolkit to convert, view and print 
electrocardiograms 
(https://sourceforge.net/projects/ecgtoolkit-cs/). The file 
contains a 12-leads electrocardiogram encoded into the 
**SCP-ECG** format.

  * The file contains 5000 samples per lead.
  * Acquiring interval is 2000 us (500 Hz).
  * Data stream is encoded using the default SCP-ECG Huffman table.
  * Data are signed integers, representing the "second difference" of the original data.
  * The referece unit of the restored sequence is 2500 nV; it must be multiplied by 2.5 to obtain mV.
  * No bimodal compression, no reference beat compression.
