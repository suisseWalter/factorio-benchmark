This repository should serve the testing of different factorio optimisations problems. 
The goal is, to be able to test different maps quickly and be able to compare the results over time.  

## Usage 

when running it for the first time, or when updating factorio use the -u mode to get the latest stable version.

if you only want to run part of the testsuite you can use the -r \<regex> option to only match certain files. 

### running benchmarks
To run benchmarks make sure that you have a done a fresh boot of your computer and have as few processes running as possible. (turn of any autostart programs you can.)


## Todo

1) add mod support (to do things like miniloader testing.)
2) Add some kind of hardware summary to each test run, so people can now what kind of hardware one has used for a given test result. (best to use lshw)
2) move save files storage to different locations (they shouldn't be stored on github due to their size) 
this should be done by having a -i option to install the saves after download. This maybe should also allow for more custom inputs and or partial downloads.
3) add a directory structure, so that only results from a certain test-group are graphed together. Otherwise, the graphs will get illegible. as there will be too many lines in the graphs. 
4) figure out how to get mularks maps downloaded via todo 2. 

5) add ways to customize runtime and amount of runs for, either each map or each test-group, This would be best done by adding a file to each group/test that contains the ticktime and amount of repetitions aswell as a description of what the test is designed to do. 