import csv
import statistics


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

for file in filesstr[1:]:

    cfile = open(filepramble+file[0], "r", newline="")
    cfilestr = list(csv.reader(cfile, dialect="excel"))
    inlist = []
    for i in cfilestr[6: len(cfilestr)-1]:
        try:
            inlist.append(list(map(int, i[1:-1])))
        except:
            print("can't convert to int")
            print(i)

    # inlist = [list(map(int, i[1:-1])) for i in cfilestr[6: len(cfilestr)]][:-1]
    # print(inlist[0])
    outrow = []
    outrow.append(file[0])
    print(inlist[-1])
    for rowi in range(32):
        outrow.append(statistics.mean(column(inlist, rowi)))
    outfile.append(outrow)


outrow = []
outrow.append("rel. avg. increase")
for coli in range(1, 33):
    col = column(outfile, coli)
    incr = []
    for rowi in range(1, len(col), 2):
        if(col[rowi+1] != 0):
            incr.append(col[rowi]/col[rowi+1]-1)
        else:
            if(len(incr) != 0):
                incr.append(0)
    try:
        outrow.append(statistics.mean(incr))
    except:
        print("bad luck")
        outrow.append(0)
outfile.append(outrow)

outrow = []
outrow.append("abs. avg. increase")
for coli in range(1, 33):
    col = column(outfile, coli)
    incr = []
    for rowi in range(1, len(col)-1, 2):
        if(col[rowi+1] != 0):
            incr.append(col[rowi]-col[rowi+1])
        else:
            if(len(incr) != 0):
                incr.append(0)
    try:
        outrow.append(statistics.mean(incr))
    except:
        print("bad luck")
        outrow.append(0)
outfile.append(outrow)

print(outfile)
cleanfile = open("cleanfile.csv", "w", newline="")
cleanoutput = csv.writer(cleanfile, dialect="excel")
cleanoutput.writerows(outfile)
