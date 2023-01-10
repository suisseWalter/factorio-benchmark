import argparse
import atexit
import csv
import glob
import itertools
import os
import statistics
import tarfile
from datetime import date, datetime
from sys import platform as operatingsystem_codename
from typing import List
from zipfile import ZipFile

import matplotlib.pyplot as plt
import requests


def column(table: str, index: int) -> List[str]:
    """Return the column of the table with the given index."""
    col = []
    for row in table:
        try:
            col.append(row[index])
        except Exception:  # noqa: PIE786
            continue
    return col


def exit_handler() -> None:
    print("Terminating grasfully!")
    sync_mods("", True)
    # I should also clean up potential other files
    # such as the lock file (factorio/.lock on linux)
    # also factorio.zip and maps.zip can be left over in rare cases and fail the reinstall.


def sync_mods(map: str, disable_all: bool = False) -> None:
    fmm_name = {"linux": "fmm_linux", "win32": "fmm_win32.exe", "cygwin": "fmm_win32.exe"}[
        operatingsystem_codename
    ]
    if not disable_all:
        set_mod_command = (
            os.path.join("fmm", fmm_name)
            + f'  --config {os.path.join("fmm", "fmm.toml")}  sf "{map}"'
        )
    else:
        set_mod_command = os.path.join("fmm", fmm_name) + " --game-dir factorio disable"
    print(os.popen(set_mod_command).read())


def install_maps(link: str) -> None:
    """download maps from the walterpi server"""
    file = requests.get(link)
    with open("maps.zip", "xb") as mapsfile:
        mapsfile.write(file.content)
    with ZipFile("maps.zip", "r") as zip:
        zip.extractall("saves")
    os.remove("maps.zip")


def install_factorio(
    link: str = "https://factorio.com/get-download/stable/headless/linux64",
) -> None:
    """Download and extract the latest version of Factorio."""
    file = requests.get(link)
    with open("factorio.zip", "xb") as zipfile:
        zipfile.write(file.content)
    with tarfile.open("factorio.zip", "r:xz") as tar:
        tar.extractall("")
    os.remove("factorio.zip")


def run_benchmark(map_: str, folder: str, save: bool = True, ticks: int = 0, runs: int = 0) -> None:
    """Run a benchmark on the given map with the specified number of ticks and
    runs."""
    if ticks == 0:
        ticks = args.ticks
    if runs == 0:
        runs = args.repetitions
    factorio_bin = os.path.join("factorio", "bin", "x64", "factorio")
    # setting mods
    if not args.disable_mods:
        sync_mods(map_)

    print("Running benchmark...")
    os.dup(1)
    command = (
        f"{factorio_bin} "
        f'--benchmark "{map_}" '
        f"--benchmark-ticks {ticks} "
        f"--benchmark-runs {runs} "
        "--benchmark-verbose all "
        "--benchmark-sanitize"
    )
    # print(command)

    factorio_log = os.popen(command).read()

    if "Performed" not in factorio_log:
        print("Benchmark failed")
        print(factorio_log)
        return
    # print(factorio_log)
    ups = int(
        1000
        * args.ticks
        / float([line.split()[-2] for line in factorio_log.split("\n") if "Performed" in line][0])
    )
    print(f"Map benchmarked at {ups} UPS")
    if not save:
        return
    filtered_output = [line for line in factorio_log.split("\n") if "ed" in line or "t" in line]
    with open(os.path.join(folder, "{}".format(os.path.splitext(map_)[0])), "x") as f:
        f.write("\n".join(filtered_output))


def benchmark_folder(map_regex: str = "*") -> None:
    """Run benchmarks on all maps that match the given regular expression."""
    folder = f"benchmark_on_{date.today()}_{datetime.now().strftime('%H_%M_%S')}"
    os.makedirs(folder)
    os.makedirs(os.path.join(folder, "saves"))
    os.makedirs(os.path.join(folder, "graphs"))

    print("Warming up the system...")
    run_benchmark(
        os.path.join("saves", "factorio_maps", "big_bases", "flame10k.zip"),
        folder,
        False,
        ticks=100,
        runs=1,
    )
    print("Finished warming up, starting the actual benchmark...")

    for filename in glob.glob(os.path.join("saves", map_regex), recursive=True):
        if not os.path.isfile(filename):
            continue
        print(filename)
        os.makedirs(os.path.join(folder, os.path.split(filename)[0]), exist_ok=True)
        run_benchmark(filename, folder)

    outheader = [
        "name",
        "timestamp",
        "wholeUpdate",
        "latencyUpdate",
        "gameUpdate",
        "circuitNetworkUpdate",
        "transportLinesUpdate",
        "fluidsUpdate",
        "heatManagerUpdate",
        "entityUpdate",
        "particleUpdate",
        "mapGenerator",
        "mapGeneratorBasicTilesSupportCompute",
        "mapGeneratorBasicTilesSupportApply",
        "mapGeneratorCorrectedTilesPrepare",
        "mapGeneratorCorrectedTilesCompute",
        "mapGeneratorCorrectedTilesApply",
        "mapGeneratorVariations",
        "mapGeneratorEntitiesPrepare",
        "mapGeneratorEntitiesCompute",
        "mapGeneratorEntitiesApply",
        "crcComputation",
        "electricNetworkUpdate",
        "logisticManagerUpdate",
        "constructionManagerUpdate",
        "pathFinder",
        "trains",
        "trainPathFinder",
        "commander",
        "chartRefresh",
        "luaGarbageIncremental",
        "chartUpdate",
        "scriptUpdate",
    ]
    outfile = [outheader]
    errfile = [outheader[:]]
    old_subfolder_name = ""
    # print(
    #     sorted(
    #         glob.glob(
    #             os.path.join(
    #                 folder,
    #                 "saves",
    #                 map_regex,
    #             ),
    #             recursive=True,
    #         )
    #     )
    # )
    for file in sorted(
        glob.glob(
            os.path.join(folder, "saves", map_regex),
            recursive=True,
        )
    ):
        # check if file is actually a file or a folder

        if not os.path.isfile(file):
            continue

        # check if we are in a new folder and if so generate the old graphs.
        file_name = os.path.split(file)[1]
        subfolder_name = os.path.split(os.path.split(file)[0])[1]
        if old_subfolder_name == "":
            old_subfolder_name = subfolder_name
        # print(subfolder_name)
        if subfolder_name != old_subfolder_name:
            plot_benchmark_results(outfile, folder, old_subfolder_name, errfile)
            outfile = [outheader]
            old_subfolder_name = subfolder_name

        with open(file, "r", newline="") as cfile:

            cfilestr = list(csv.reader(cfile, dialect="excel"))
            inlist = []
            errinlist = []

            for i in cfilestr[0 : len(cfilestr)]:
                try:
                    if int(i[0][1:]) % args.ticks < args.skipticks:
                        # figure out how to actually skip these ticks.
                        continue
                    inlist.append([t / 1000000 for t in list(map(int, i[1:-1]))])
                    if i[0] != "t0":
                        errinlist.append(list(map(int, i[1:-1])))
                except Exception:  # noqa: PIE786
                    pass
                    # print("can't convert to int")

            outrow = [file_name]

            outrowerr = [file_name + "_stdev"]
            for rowi in range(32):
                outrow.append(statistics.mean(column(inlist, rowi)))
                outrowerr.append(statistics.stdev(column(errinlist, rowi)))
            outfile.append(outrow)
            errfile.append(outrowerr)

            if args.consistency is not None:
                # do the consistency plot
                plot_ups_consistency(
                    folder,
                    old_subfolder_name,
                    column(inlist, consistency_index - 1),
                    "consistency_" + file_name + "_" + args.consistency,
                )

    plot_benchmark_results(outfile, folder, old_subfolder_name, errfile)

    errout_path = os.path.join(folder, "stdev.csv")
    with open(errout_path, "w+", newline="") as erroutfile:
        erroutfile.write(str(errfile))


def plot_ups_consistency(folder: str, subfolder: str, data: str, name: str = "default") -> None:
    subfolder_path = os.path.join(folder, "graphs", subfolder)

    if not os.path.exists(subfolder_path):
        os.makedirs(subfolder_path)
    darray = []
    med = []
    maxi = []
    mini = []

    t = list(range(args.skipticks, args.ticks))
    for i in range(int(len(data) / (args.ticks - args.skipticks))):
        darray.append(
            data[(args.ticks - args.skipticks) * i : (args.ticks - args.skipticks) * (i + 1)]
        )
    for i in range(len(darray[0])):
        # first discard the highest value as that can frequently be an outlier.
        c = sorted(column(darray, i))[:-1]
        med.append(statistics.median(c))
        maxi.append(max(c))
        mini.append(min(c))

    for i in range(int(len(data) / (args.ticks - args.skipticks))):
        plt.plot(
            t,
            data[(args.ticks - args.skipticks) * i : (args.ticks - args.skipticks) * (i + 1)],
            "k",
            alpha=0.2,
            linewidth=0.6,
        )
    plt.plot(t, med, "r", label="median", linewidth=0.6)
    plt.title(label=name)
    plt.xlabel(xlabel="tick")
    plt.ylabel(ylabel="tick time [ms]")
    plt.legend()
    plt.tight_layout()
    # Use os.path.join to build the file path for the output image
    out_path = os.path.join(subfolder_path, f"{name}_all.png")
    # plt.show()
    plt.savefig(out_path, dpi=800)
    plt.clf()
    plt.close()

    plt.plot(t, maxi, label="maximum", linewidth=0.3)
    plt.plot(t, mini, label="minimum", linewidth=0.3)
    plt.plot(t, med, "r", label="median", linewidth=0.6)
    plt.title(label=name)
    plt.xlabel(xlabel="tick")
    plt.ylabel(ylabel="tick time [ms]")
    plt.legend()
    plt.tight_layout()
    # Use os.path.join to build the file path for the output image
    out_path = os.path.join(subfolder_path, f"{name}_min_max_med.png")
    # plt.show()
    plt.savefig(out_path, dpi=800)
    plt.clf()
    plt.close()


def plot_benchmark_results(outfile: str, folder: str, subfolder: str, errfile: str) -> None:
    """Generate plots of benchmark results."""
    # Create the output subfolder if it does not exist
    subfolder_path = os.path.join(folder, "graphs", subfolder)
    if not os.path.exists(subfolder_path):
        os.makedirs(subfolder_path)

    for col in itertools.chain(range(1, 12), range(23, 33)):
        fig, ax = plt.subplots()
        maps = column(outfile, 0)[1:]
        update = column(outfile, col)[1:]
        hbars = ax.barh(maps, update)
        ax.bar_label(
            hbars,
            labels=[f"{x:.3f}" for x in column(outfile, col)[1:]],
            padding=3,
        )
        ax.margins(0.1, 0.05)
        ax.set_title(outfile[0][col])
        ax.set_xlabel("Mean frametime [ms/frame]")
        ax.set_ylabel("Map name")
        plt.tight_layout()
        # Use os.path.join to build the file path for the output image
        out_path = os.path.join(subfolder_path, f"{outfile[0][col]}.png")
        plt.savefig(out_path)
        plt.clf()
        plt.close()


atexit.register(exit_handler)
parser = argparse.ArgumentParser(
    description=(
        "Benchmark Factorio maps. " 'The default configuration is `-r "**" -s 20 -t 1000 -e 5'
    )
)
parser.add_argument(
    "-u",
    "--update",
    action="store_true",
    help="Update Factorio to the latest version before running benchmarks.",
)
parser.add_argument(
    "-r",
    "--regex",
    default="**",
    help=(
        "Regular expression to match map names to benchmark. "
        "The regex either needs to be escaped by quotes or every special "
        "character needs to be escaped. use ** if you want to match "
        "everything. * can only be used if a specific folder is specified.",
    ),
)
parser.add_argument(
    "-c",
    "--consistency",
    nargs="?",
    const="wholeUpdate",
    help=(
        "generates a update time consistency plot for the given metric. It "
        "has to be a metric accessible by --benchmark-verbose. the default "
        "value is 'wholeUpdate'. the first 10 ticks are skipped.(this can "
        "be set by setting '--skipticks'.",
    ),
)
parser.add_argument(
    "-s",
    "--skipticks",
    type=int,
    default="20",
    help=(
        "the amount of ticks that are ignored at the beginning of very "
        "benchmark. helps to get more consistent data, especially for "
        "consistency plots. change this to '0' if you want to use all the "
        "data",
    ),
)
parser.add_argument(
    "-t",
    "--ticks",
    type=int,
    default="1000",
    help="the default amount of ticks to run for. defaults to 1000",
)
parser.add_argument(
    "-e",
    "--repetitions",
    type=int,
    default="5",
    help=(
        "the number of times each map is repeated. default five. should be "
        "higher if `--consistency` is set.",
    ),
)
parser.add_argument(
    "--version_link",
    type=str,
    help=(
        "if you want to install a specific version of factorio. you have to "
        "provide the complete download link to the headless version. don't "
        "forget to update afterwards.",
    ),
)

parser.add_argument(
    "-m",
    "--install_maps",
    type=str,
    nargs="?",
    const="https://walterpi.hopto.org/s/g6BLGR6wa27cNRf/download",
    help="install maps",
)
parser.add_argument(
    "-dm",
    "--disable_mods",
    action="store_true",
    help="disables the usage of mod syncronisations. runs all benchmarks without enabling any mods",
)

args = parser.parse_args()
outheader = [
    "name",
    "timestamp",
    "wholeUpdate",
    "latencyUpdate",
    "gameUpdate",
    "circuitNetworkUpdate",
    "transportLinesUpdate",
    "fluidsUpdate",
    "heatManagerUpdate",
    "entityUpdate",
    "particleUpdate",
    "mapGenerator",
    "mapGeneratorBasicTilesSupportCompute",
    "mapGeneratorBasicTilesSupportApply",
    "mapGeneratorCorrectedTilesPrepare",
    "mapGeneratorCorrectedTilesCompute",
    "mapGeneratorCorrectedTilesApply",
    "mapGeneratorVariations",
    "mapGeneratorEntitiesPrepare",
    "mapGeneratorEntitiesCompute",
    "mapGeneratorEntitiesApply",
    "crcComputation",
    "electricNetworkUpdate",
    "logisticManagerUpdate",
    "constructionManagerUpdate",
    "pathFinder",
    "trains",
    "trainPathFinder",
    "commander",
    "chartRefresh",
    "luaGarbageIncremental",
    "chartUpdate",
    "scriptUpdate",
]
consistency_index: int = 0

if args.consistency is not None:
    try:
        consistency_index = outheader.index(args.consistency)
    except ValueError as e:
        print("the chosen consistency variable doesn't exist:", e)
        exit(0)

if args.update:
    if args.version_link:
        install_factorio(args.version_link)
    else:
        install_factorio()

if args.install_maps:
    install_maps(args.install_maps)


benchmark_folder(map_regex=args.regex)
sync_mods("", True)

# plot_benchmark_results()
