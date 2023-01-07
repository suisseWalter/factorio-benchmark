This repository should serve the testing of different factorio optimisations problems. 
The goal is, to be able to test different maps quickly and be able to compare the results over time.  

# install

### Linux
just run `benchmarker.py -u -m` to install the latest version of factorio and download some sample maps. This will also directly run the programm a first time. 

it needs python3. therefore depending on your distro you might have to do `pythen3 benchmarker.py -u -m` or `python benchmarker.py -u -m.
### Windows 
with WSL2:
You are using Linux therefore just use the linux install: `python benchmarker.py -u -m`
without WSL2:
As there is no headless version available for windows, one has to install factorio by hand. to do this download the correct version from the website and unpack it into the main folder. so that `factorio/bin/x64/factorio` is the correct file. It would also be possible to add a link to a existing install into that possition but that isn't recommended due to mods.
After that run `python benchmarker.py -m` to download some sample maps and run it a first time.

### OSX
Same as Windows without WSL. You need to install factorio manually. As with windows `factorio/bin/x64/factorio` needs to be pointing to factorio. If the factorio install uses a different path, for example if you are on a ARM based mac, you might need to create a symlink to there. 
After that run `python benchmarker.py -m` to download some sample maps and run it a first time.
if you have suggestions on how to improve the OSX situation please reach out. 
## Usage 

when running it for the first time, or when updating factorio use the -u mode to get the latest stable version.

if you only want to run part of the testsuite you can use the -r \<regex> option to only match certain files. 

### running benchmarks
To run clean benchmarks make sure that you have a done a fresh boot of your computer and have as few processes running as possible. (turn of any autostart programs you can.)

### Options:
the configurations options are as follows:
options:
```
  -h, --help            show this help message and exit
  -u, --update          Update Factorio to the latest version before running benchmarks.
  -r REGEX, --regex REGEX
                        Regular expression to match map names to benchmark. The regex either needs to be escaped by quotes or every special character needs to be
                        escaped. use ** if you want to match everything. * can only be used if a specific folder is specified.
  -c [CONSISTENCY], --consistency [CONSISTENCY]
                        generates a update time consistency plot for the given metric. It has to be a metric accessible by --benchmark-verbose. the default value is
                        'wholeUpdate'. the first 10 ticks are skipped.(this can be set by setting '--skipticks'.
  -s SKIPTICKS, --skipticks SKIPTICKS
                        the amount of ticks that are ignored at the beginning of very benchmark. helps to get more consistent data, especially for consistency plots.
                        change this to '0' if you want to use all the data
  -t TICKS, --ticks TICKS
                        the default amount of ticks to run for. defaults to 1000
  -e REPETITIONS, --repetitions REPETITIONS
                        the number of times each map is repeated. default five. should be higher if `--consistency` is set.
  --version_link VERSION_LINK
                        if you want to install a specific version of factorio. you have to provide the complete download link to the headless version. don't forget to
                        update afterwards.
  -m [INSTALL_MAPS], --install_maps [INSTALL_MAPS]
                        install maps
```

## Todo

1) add mod support (to do things like miniloader testing.)
2) Add some kind of hardware summary to each test run, so people can now what kind of hardware one has used for a given test result. (best to use lshw)
2) move save files storage to different locations (they shouldn't be stored on github due to their size) 
this should be done by having a -i option to install the saves after download. This maybe should also allow for more custom inputs and or partial downloads.
4) figure out how to get mularks maps downloaded via todo 1. 

5) add ways to customize runtime and amount of runs for, either each map or each test-group, This would be best done by adding a file to each group/test that contains the ticktime and amount of repetitions aswell as a description of what the test is designed to do. 