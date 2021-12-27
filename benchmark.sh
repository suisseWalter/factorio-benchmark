#!/bin/bash


bench () {
	export MAP=$1
	echo $MAP
	touch "$folder"/"$MAP""nohp".out
	touch "$folder"/"$MAP""hp".out
	#curl $URL --output /tmp/test2.zip
	echo " no hugepages"| tee cs"$folder"/"$MAP""nohp".out
	sudo MAP=$1 bash ./singlefile.sh | egrep "ed|t" | tee -a "$folder"/"$MAP""nohp".out
	echo " with hugepages"| tee "$folder"/"$MAP""hp".out
	sudo MAP=$1 MIMALLOC_PAGE_RESET=0 MIMALLOC_LARGE_OS_PAGES=1 HUGETLB_MORECORE=thp MALLOC_ARENA_MAX=1 LD_PRELOAD=/usr/local/lib/mimalloc-2.0/libmimalloc.so  bash ./singlefile.sh | egrep "ed|t" | tee -a "$folder"/"$MAP""hp".out
}
folder="benchmark_on_"$(date)
echo $folder
mkdir "$folder"
mkdir "$folder"/benchsaves/
for filename in benchsaves/*; do
	echo " ${filename}"
	bench ${filename}

done
echo "$folder"/benchsaves/ > files.csv
ls "$folder"/benchsaves/ >> files.csv
ls "$folder"/benchsaves/ > "$folder"/files.csv
/bin/python3 processor.py
