#!/bin/bash

show_help () {
	echo 'options: '
	echo '	-u 		: update factorio '
	echo '	-r <regex> 	: provide regex to match saves to test. '
	echo '			  The regex either needs to be escaped by " or every special character needs to be escaped'
	echo '			  It only accepts regex that can be used by the "ls" command. '

}

update () {
	wget https://factorio.com/get-download/stable/headless/linux64
  	tar -xJf linux64
	rm linux64
}

bench () {
	export MAP=$1
	echo $MAP
	touch "$folder"/"$MAP""".out
	#touch "$folder"/"$MAP""hp".out
	#curl $URL --output /tmp/test2.zip
	#echo " no hugepages"| tee cs"$folder"/"$MAP""nohp".out
	MAP=$1 bash ./singlefile.sh | egrep "ed|t" | tee -a "$folder"/"$MAP""".out
	#echo " with hugepages"| tee "$folder"/"$MAP""hp".out
	#sudo MAP=$1 MIMALLOC_PAGE_RESET=0 MIMALLOC_LARGE_OS_PAGES=1 HUGETLB_MORECORE=thp MALLOC_ARENA_MAX=1 LD_PRELOAD=/usr/local/lib/mimalloc-2.0/libmimalloc.so  bash ./singlefile.sh | egrep "ed|t" | tee -a "$folder"/"$MAP""hp".out
}

# A POSIX variable
OPTIND=1         # Reset in case getopts has been used previously in the shell.

# Initialize our own variables:
do_update="0"
regex="*"

while getopts "h?ur:" opt; do
  case "$opt" in
    h|\?)
      show_help
      exit 0
      ;;
    u)  do_update="1"
      ;;
    r)  regex="$OPTARG"
		echo "$OPTARG"
      ;;
  esac
done

echo "$do_update"
if [ "$do_update" == "1" ];  
then
	echo "doing update first"
	echo "$do_update"
	update 
fi

folder="benchmark_on_"$(date '+%F;%H:%M:%S')

echo $folder
mkdir "$folder"
mkdir "$folder"/saves/
mkdir "$folder"/graphs/
echo "$regex"
for filename in saves/$regex; do
	echo " ${filename}"
	bench ${filename}

done

echo "$folder"/saves/ > files.csv
ls "$folder"/saves/ >> files.csv
#ls "$folder"/saves/ > "$folder"/files.csv
/bin/python3 processor.py
