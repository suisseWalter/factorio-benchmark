import argparse
import atexit
import csv
import glob
import itertools
import json
import os
import statistics
import subprocess
import tarfile
from datetime import date, datetime
from pathlib import Path
from sys import platform as operatingsystem_codename
from zipfile import ZipFile

import matplotlib.pyplot as plt
import psutil
import requests

outheader = [
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


def exit_handler() -> None:
    print("Terminating grasfully!")
    sync_mods("", True)
    # I should also clean up potential other files
    # such as the lock file (factorio/.lock on linux)
    # also factorio.zip and maps.zip can be left over in rare cases and fail the reinstall.


def get_factorio_version(factorio_bin: str, full: bool = False) -> str:
    """returns the version string of the installed factorio instance"""
    factorio_log_version = os.popen(f"{factorio_bin} --version").read()
    result = factorio_log_version.splitlines()[0].split()[1]
    if full:
        result += " " + factorio_log_version.splitlines()[0].split()[4][:-1]
        result += " " + factorio_log_version.splitlines()[0].split()[5][:-1]
    return result


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
    # print(">>>> sync_mods()\t", set_mod_command)
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


# for mypy
def remove_character_from_string(s: str, char: str = "\r") -> str:
    return s.replace(char, "")


def run_benchmark(
    map_: str,
    folder: str,
    ticks: int,
    runs: int,
    save: bool = True,
    disable_mods: bool = True,
    factorio_bin: str | None = None,
    high_priority: bool | None = None,
) -> None:
    """Run a benchmark on the given map with the specified number of ticks and
    runs."""
    if not factorio_bin:
        factorio_bin = os.path.join("factorio", "bin", "x64", "factorio")
    # setting mods
    if not disable_mods:
        sync_mods(map_)

    print("Running benchmark...")
    # Get Version
    version: str = get_factorio_version(factorio_bin, True)
    # psutil.Popen on Linux it doesn't work well with str()
    command: list[str] = [str(factorio_bin)]
    command.extend(["--benchmark", str(map_)])
    command.extend(["--benchmark-ticks", str(ticks)])
    command.extend(["--benchmark-runs", str(runs)])
    command.extend(["--benchmark-verbose", "all"])
    command.extend(["--benchmark-sanitize"])
    if high_priority is True:
        priority = {
            "linux": -20,
            "win32": 128,
            "cygwin": 128,
        }[operatingsystem_codename]
        print("nice = ", priority)
        process = psutil.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process.nice(priority)
    else:
        process = psutil.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    factorio_log, err = map(
        lambda a: remove_character_from_string(a.decode(), "\r"), process.communicate()
    )

    if "Performed" not in factorio_log:
        print("Benchmark failed")
        print(factorio_log)
        print(err)
    else:
        if save:
            # print(factorio_log)
            print(version)
            avgs = [
                float(line.split()[-2]) / ticks
                for line in factorio_log.split("\n")
                if "Performed" in line
            ]
            avg = statistics.mean(avgs)
            ups = 1000 / avg
            avgs_str: list[str] = [f"{i:.3f}" for i in avgs]
            print("Map benchmarked at:")
            print("avg = {:.3f} ms {}".format(avg, avgs_str))
            print("{:.3f} UPS".format(ups))
            print()
            out: dict[str, str | float | list[str]] = dict()
            out["version"] = version
            out["avg"] = avg
            out["ups"] = ups
            out["avgs"] = avgs_str
            filtered_output = [str(json.dumps(out))]
            filtered_output.extend(
                [line for line in factorio_log.split("\n") if "ed" in line or "t" in line]
            )
            with open(os.path.join(folder, "{}".format(os.path.splitext(map_)[0])), "x") as f:
                f.write("\n".join(filtered_output))


def benchmark_folder(
    ticks: int,
    runs: int,
    disable_mods: bool,
    skipticks: int,
    consistency: str,
    map_regex: str = "*",
    factorio_bin: str | None = None,
    folder: str | None = None,
    filenames: list[str] | None = None,
    high_priority: bool | None = None,
) -> None:
    """Run benchmarks on all maps that match the given regular expression."""
    if not folder:
        folder = f"benchmark_on_{date.today()}_{datetime.now().strftime('%H_%M_%S')}"
    os.makedirs(folder)
    os.makedirs(os.path.join(folder, "saves"))
    os.makedirs(os.path.join(folder, "graphs"))

    print("Warming up the system...")
    run_benchmark(
        os.path.join("saves", "factorio_maps", "big_bases", "flame10k.zip"),
        folder,
        ticks=100,
        runs=1,
        save=False,
        disable_mods=disable_mods,
        factorio_bin=factorio_bin,
        high_priority=high_priority,
    )
    print("Finished warming up, starting the actual benchmark...")

    print()
    print("==================")
    print("benchmark maps")
    print("==================")
    print("")
    if not filenames:
        filenames = glob.glob(os.path.join("saves", map_regex), recursive=True)
    for filename in filenames:
        if os.path.isfile(filename):
            print(filename)
            os.makedirs(os.path.join(folder, os.path.split(filename)[0]), exist_ok=True)
            run_benchmark(
                filename,
                folder,
                ticks=ticks,
                runs=runs,
                save=True,
                disable_mods=disable_mods,
                factorio_bin=factorio_bin,
                high_priority=high_priority,
            )

    print("==================")
    print("creating graphs")
    processed_table: list[list[float]] = []
    maps: list[str] = []
    errfile: list[list[int]] = []
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
            plot_benchmark_results(
                processed_table, outheader, maps, folder, old_subfolder_name, errfile
            )
            processed_table = []
            maps = []
            old_subfolder_name = subfolder_name

        with open(file, "r", newline="") as cfile:

            cfilestr = list(csv.reader(cfile, dialect="excel"))
            inlist: list[list[float]] = []

            for i in cfilestr[0 : len(cfilestr)]:
                try:
                    if int(i[0][1:]) % ticks < skipticks:
                        # figure out how to actually skip these ticks.
                        continue
                    inlist.append([t / 1000000 for t in list(map(int, i[1:-1]))])
                except Exception:  # noqa: PIE786
                    pass
                    # print("can't convert to int")

            processed_line = []
            maps.append(file_name)
            for rowi in range(32):
                processed_line.append(statistics.mean([a[rowi] for a in inlist]))
            processed_table.append(processed_line)

            if consistency is not None:
                # do the consistency plot
                plot_ups_consistency(
                    folder=folder,
                    subfolder=old_subfolder_name,
                    data=[a[consistency_index] for a in inlist],
                    ticks=ticks,
                    skipticks=skipticks,
                    name="consistency_" + file_name + "_" + consistency,
                )

    plot_benchmark_results(processed_table, outheader, maps, folder, old_subfolder_name, errfile)

    print("")
    print("the benchmark is finished")
    print("==================")


def plot_ups_consistency(
    folder: str,
    subfolder: str,
    data: list[float],
    ticks: int,
    skipticks: int,
    name: str = "default",
) -> None:
    subfolder_path = os.path.join(folder, "graphs", subfolder)

    if not os.path.exists(subfolder_path):
        os.makedirs(subfolder_path)
    darray = []
    med = []
    maxi = []
    mini = []

    t = list(range(skipticks, ticks))
    for i in range(int(len(data) / (ticks - skipticks))):
        darray.append(data[(ticks - skipticks) * i : (ticks - skipticks) * (i + 1)])
    for i in range(len(darray[0])):
        # first discard the highest value as that can frequently be an outlier.
        c = sorted([a[i] for a in darray])[:-1]
        med.append(statistics.median(c))
        maxi.append(max(c))
        mini.append(min(c))

    for i in range(int(len(data) / (ticks - skipticks))):
        plt.plot(
            t,
            data[(ticks - skipticks) * i : (ticks - skipticks) * (i + 1)],
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


def plot_benchmark_results(
    data_table: list[list[float]],
    titles: list[str],
    maps: list[str],
    folder: str,
    subfolder: str,
    errfile: list[list[int]],
) -> None:
    """Generate plots of benchmark results."""
    # Create the output subfolder if it does not exist
    subfolder_path = os.path.join(folder, "graphs", subfolder)
    if not os.path.exists(subfolder_path):
        os.makedirs(subfolder_path)

    for col in itertools.chain(range(1, 11), range(22, 32)):
        fig, ax = plt.subplots()
        update = [a[col] for a in data_table]
        hbars = ax.barh(maps, update)
        ax.bar_label(
            hbars,
            labels=[f"{x:.3f}" for x in [a[col] for a in data_table]],
            padding=3,
        )
        ax.margins(0.1, 0.05)
        ax.set_title(titles[col])
        ax.set_xlabel("Mean frametime [ms/frame]")
        ax.set_ylabel("Map name")
        plt.tight_layout()
        # Use os.path.join to build the file path for the output image
        out_path = os.path.join(subfolder_path, f"{titles[col]}.png")
        plt.savefig(out_path)
        plt.clf()
        plt.close()


def create_mods_dir() -> None:
    """creates a folder: 'factorio/mods'"""
    """creates a file: 'factorio/mods/mod-list.json'"""
    """copies the file from 'fmm/mod-settings.dat' to 'factorio/mods/mod-settings.dat'"""
    os.makedirs(os.path.join("factorio", "mods"), exist_ok=True)
    mod_list_json_file = os.path.join("factorio", "mods", "mod-list.json")
    if not os.path.exists(mod_list_json_file):
        with open(mod_list_json_file, "x") as file:
            file.write('{"mods":[{"name":"base","enabled":true}]}')
    mod_settings_dat_file = os.path.join("factorio", "mods", "mod-settings.dat")
    if not os.path.exists(mod_settings_dat_file):
        # copy the file 'mod-settings.dat'
        source: Path = Path(os.path.join("fmm", "mod-settings.dat"))
        destination: Path = Path(mod_settings_dat_file)
        destination.write_bytes(source.read_bytes())


def init_parser() -> argparse.ArgumentParser:
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
        help=str(
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
        help=str(
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
        help=str(
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
        help=str(
            "the number of times each map is repeated. default five. should be "
            "higher if `--consistency` is set.",
        ),
    )
    parser.add_argument(
        "--version_link",
        type=str,
        help=str(
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
    parser.add_argument(
        "-hp",
        "--high_priority",
        action="store_true",
        default=False,
        help="Increases the priority for the 'factorio' process. On Linux requires 'sudo'",
    )
    return parser


######################################
#
# main
if __name__ == "__main__":
    atexit.register(exit_handler)
    args = init_parser().parse_args()
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

    create_mods_dir()
    if args.disable_mods:
        sync_mods(map="", disable_all=True)

    benchmark_folder(
        args.ticks,
        args.repetitions,
        args.disable_mods,
        args.skipticks,
        args.consistency,
        map_regex=args.regex,
        high_priority=args.high_priority,
    )

    # plot_benchmark_results()
