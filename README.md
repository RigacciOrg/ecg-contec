# ecg2pdf

Python program to plot electrocardiogram graphs from files 
produced by the **Contec ECG90A** device.

The program relay on the Pyhon modules **ecg_contec.py** and 
**ecg_scp.py**, which should be present in the same directory or 
installed as system-wide modules. I requires also the libraries 
Numpy, Scipy and Reportlab. Developed with Python 3.7.

This is a minimal usage example:

```
./ecg2pdf 0000053.ECG
```

You can ask for a PNG filei instead, that will rendered at 300 dpi:

```
./ecg2pdf --png 0000053.ECG
```

The command above will produce the following output: 

![ECG90A file plotted with ecg2pdf](0000053.png "ECG90A file plotted with ecg2pdf")


## Command line options

The program can filter the data with a lowpass filter (to remove 
noise e.g. generated from AC powered devices in the nearby), you 
can choose to plot only some leads starting from a specified 
time and to use a different format:

```
./ecg2pdf --lowpass 40 --leads 1,2,3,4,5,6 --time0 4.2 --format 6x1 0000053.ECG
```

You can ask for complete command line help:

```
./ecg2pdf -h
usage: ecg2pdf [-h] [--png] [--speed mm/s] [--ampli mm/mV] [--time0 TIME0]
               [--lowpass Hz] [--format ROWSxCOLS] [--leads LIST] [-y]
               filename [filename_out]

Parse an ECG90A file and create a PDF or PNG graph.

positional arguments:
  filename            Contec ECG90A file to read
  filename_out        output PDF or PNG file to write (default append .pdf or
                      .png to filename)

optional arguments:
  -h, --help          show this help message and exit
  --png               output a PNG raster file instead of PDF (default no)
  --speed mm/s        speed in mm/s (default 25.0)
  --ampli mm/mV       leads amplitude in mm/mV (default auto)
  --time0 TIME0       plotting start time, in seconds (default 0.0)
  --lowpass Hz        add a lowpass filter at specified Hz (default None)
  --format ROWSxCOLS  use specified print format (default 6x1)
  --leads LIST        comma separated list of leads to print (default 1,..,12)
  -y, --overwrite     overwrite existing output files (default no)
```

## More on filters

The program uses the scipy.signal.filtfilt() to apply a 
Butterworth filter builded with scipy.signal.butter(). The 
filtfilt() is better than lfilter() because it does not shift 
the phase of the graph and it does not generate artifacts at the 
edges. Beware the filtfilt() performs two passes (forward and 
backward), so the order used is generally the half the one used 
with lfilter(). The program generates one plot pitch every 0.2 
mm, if that pitch correspond to more than 4 sample points, an 
uniform_filter() is applied over the pitch segment.

## Web References

* Contec ECG90A Electrocardiograph - ECG File Format
  * https://www.rigacci.org/wiki/doku.php/tecnica/misc/contec_ecg_file_format
