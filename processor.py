import csv
import itertools
import statistics
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import style
def column(table, index):
    col = []
    for row in table:
        try:
            col.append(row[index])
        except:
            continue
    return col


files = open("files.csv", "r+", newline="")
filesstr = list(csv.reader(files, dialect="excel"))
filepramble = filesstr[0][0]

outheader = ["name", "timestamp", "wholeUpdate", "latencyUpdate", "gameUpdate", "circuitNetworkUpdate", "transportLinesUpdate", "fluidsUpdate", "heatManagerUpdate", "entityUpdate", "particleUpdate", "mapGenerator", "mapGeneratorBasicTilesSupportCompute", "mapGeneratorBasicTilesSupportApply", "mapGeneratorCorrectedTilesPrepare", "mapGeneratorCorrectedTilesCompute",
             "mapGeneratorCorrectedTilesApply", "mapGeneratorVariations", "mapGeneratorEntitiesPrepare", "mapGeneratorEntitiesCompute", "mapGeneratorEntitiesApply", "crcComputation", "electricNetworkUpdate", "logisticManagerUpdate", "constructionManagerUpdate", "pathFinder", "trains", "trainPathFinder", "commander", "chartRefresh", "luaGarbageIncremental", "chartUpdate", "scriptUpdate"]
outfile = [outheader]
errfile = [outheader[:]]
for file in filesstr[1:]:

    cfile = open(filepramble+file[0], "r", newline="")
    cfilestr = list(csv.reader(cfile, dialect="excel"))
    inlist = []
    errinlist = []
    for i in cfilestr[6: len(cfilestr)-1]:
        try:
            inlist.append([t/1000000 for t in list(map(int, i[1:-1]))])
            if not i[0]=="t0":
                errinlist.append(list(map(int, i[1:-1])))
        except:
            print("can't convert to int")
            # print(i)

    # inlist = [list(map(int, i[1:-1])) for i in cfilestr[6: len(cfilestr)]][:-1]
    # print(inlist)
    outrow = []
    outrow.append(file[0].split(".")[0])
    outrowerr = []
    outrowerr.append(file[0]+"_stdev")
    print(inlist[-1])
    for rowi in range(32):
        outrow.append(statistics.mean(column(inlist, rowi)))
        outrowerr.append(statistics.stdev(column(errinlist, rowi)))
    outfile.append(outrow)
    errfile.append(outrowerr)
    print(outrowerr)


for col in itertools.chain(range(1,12),range(23,33)):
    fig, ax = plt.subplots()
    # print(style.available)
    # style.use("dark_background")
    maps=column(outfile,0)[1:]
    update=column(outfile,col)[1:]
    hbars = ax.barh(maps,update)
    ax.bar_label(hbars, labels= [f'{x:.3f}' for x in column(outfile,col)[1:]],
                padding=3)
    ax.margins(0.1,0.05)
    ax.set_title(outfile[0][col])
    ax.set_xlabel("Mean frametime [ms/update]")
    ax.xaxis.grid(True)
    ax.yaxis.grid(False)
    ax.set_yticks(np.arange(len(maps)) )
    r = ax.set_yticklabels(maps, ha = 'left')
    plt.draw()
    yax = ax.get_yaxis()
    pad = max(T.label.get_window_extent(renderer=fig.canvas.get_renderer()).width for T in yax.majorTicks)*0.75
    yax.set_tick_params(pad=pad)
    #ax.set_ylabel("Map")
    plt.draw()
    plt.tight_layout()
    fig.savefig(filepramble.split("/")[0]+ "/graphs/" + outfile[0][col] + ".png", dpi=200)
    plt.close("all")
    #print(outfile)
cleanfile = open("cleanfile.csv", "w", newline="")
cleanoutput = csv.writer(cleanfile, dialect="excel")
cleanoutput.writerows(outfile)
