[[ -z $PYTHOPATH || $PYTHONPATH != $(pwd) ]] && export PYTHONPATH=$(pwd)

YELLOW='\033[1;33m'
NC='\033[0m'

message="./stat.sh <benhchmark-folder> <positive-number-of-runs>"

if [ $# -eq 2 ]; then
	nr=$2
	[[ $nr -lt 1 ]] && { echo ${message}; exit; }
elif [ $# -eq 1 ]; then
	nr=32
else
	echo ${message}
	exit
fi

b=$1 # benchmark path: benchmarks/data/bsource/bname

bf=$(echo $b|awk -F'/' '{print $NF}')
bd=$(echo $b|awk -F'/' '{print $(NF-1)}')
rpath="$(echo $b|awk -F'/' 'NF-=3' OFS='/')/results"

[[ -d "${rpath}/${bd}/${bf}" ]] && rm -r "${rpath}/${bd}/${bf}"
[[ ! -d "${rpath}/${bd}/${bf}" ]] && mkdir -p "${rpath}/${bd}/${bf}"

f="${rpath}/${bd}/${bf}/${bf}.log"

[[ -f $f ]] && (echo > $f) || touch $f

temp="${rpath}/${bd}/${bf}/$bf.temp"

sc=$(echo $b/schema/$bf.sc)
inl=$(cat $sc | grep -e "^*" | cut -d '*' -f 2 | cut -d '(' -f 1)
outl=$(cat $sc | grep -v "^*" | cut -d '(' -f 1)
view=$(ls $b/example/*_update.facts|rev|cut -d '/' -f1|rev|sed 's/_update.facts//g')
view=${view[0]}

fact_files=( "${view}_update.facts" )
expected_files=()

for i in ${inl[@]}; do
	fact_files+=( "${i}.facts" )
	expected_files+=( "${i}_update.expected" )
done

t_in=0
t_out=0

for i in ${fact_files[@]}; do
	t_in=$(expr ${t_in} + $(grep -cve "^\s*$" $b/example/$i))
done

for i in ${expected_files[@]}; do
	t_out=$(expr ${t_out} + $(grep -cve "^\s*$" $b/example/$i))
done

atvn=(R S P C J I D U)

stga=0
stpa=0
stta=0


for i in `seq -w 1 ${nr}`; do
	clear
	echo ${YELLOW}================= $i${NC}
	echo === $i >> $f

	python synthbx -s $b -m clean
	python synthbx -s $b -m synth > $temp

	bi="${rpath}/${bd}/${bf}/run-${i}"
	mkdir ${bi}

	[[ -d "$b/result" ]] && cp "$b/result"/*.dl "${bi}" || continue
	
	dsg=$(grep -ce "^\w.*$" ${bi}/dget.dl)
	sv=($(grep "==type" $temp|cut -d_ -f 1|rev|cut -b 1))

	printf "#Atomic View: " >> $f
	atvq=(0 0 0 0 0 0 0 0)

	for a in ${sv[@]: -${dsg}}; do
		for ia in `seq 0 ${#atvn[@]}`; do
			[[ ${atvn[$ia]} == $a ]] && { ((atvq[ia]+=1)) ; break; }
		done
	done

	for ia in `seq 0 ${#atvn[@]}`; do
		if [[ ${atvq[$ia]} -gt 1 ]]; then
			printf "${atvq[$ia]}${atvn[$ia]} " >> $f
		elif [[ ${atvq[$ia]} -eq 1 ]]; then
			printf "${atvn[$ia]} " >> $f
		fi
	done

	echo >> $f

	echo "#Tuples" >> $f
	echo "In/Out: ${t_in}/${t_out}" >> $f

	is=0
	ds=0
	for i in ${inl[@]}; do
		is=$(expr $is + $(grep -cve "^\s*$" $b/synth/_put/${i}_sdt_insert.expected))
		ds=$(expr $ds + $(grep -cve "^\s*$" $b/synth/_put/${i}_sdt_delete.expected))
	done
	echo "IS/DS: ${is}/${ds}" >> $f

	iv=$(grep -cve "^\s*$" $b/synth/_put/${view}_vdt_insert.expected)
	dv=$(grep -cve "^\s*$" $b/synth/_put/${view}_vdt_delete.expected)
	echo "IV/DV: ${iv}/${dv}" >> $f

	echo "#Rules" >> $f
	sg=$(grep -ce "^\w.*$" ${bi}/get.dl)
	cg=$(grep -ce "^\w.*$" ${bi}/cget.dl)
	echo "Sg/Cg: ${sg}/${cg}" >> $f

	echo "DSg: ${dsg}" >> $f

	sp=$(grep -ce "^\w.*$" ${bi}/put.dl)
	cp=$(grep -ce "^\w.*$" ${bi}/cput.dl)
	echo "Sp/Cp: ${sp}/${cp}" >> $f

	echo "#FoundGet" >> $f
	nfg=$(grep "Number of found gets" $temp|cut -d: -f2)
	echo "NFg : ${nfg}" >> $f

	echo "#SynthTime" >> $f
	stg=($(grep "SynthTime (get.dl)" $temp|cut -d'[' -f2|cut -d, -f1))
	stg=$(printf "%.8f" ${stg[${#stg[@]}-1]})

	stp=($(grep "SynthTime (get.dl)" $temp|cut -d, -f2|sed 's/ //g'|sed 's/]//g'))
	stp=$(printf "%.8f" ${stp[${#stp[@]}-1]})
	stp2=($(grep "SynthTime (put.dl)" $temp|cut -d, -f2|sed 's/ //g'|sed 's/]//g'))
	stp2=$(printf "%.8f" ${stp2[${#stp2[@]}-1]})
	stp=$(printf "%.8f" $(echo $stp + $stp2 | bc))
	stt=($(grep "Total runtime (get.dl)" $temp|cut -d: -f2|sed 's/ //g'))
	stt=$(printf "%.8f" ${stt[${#stt[@]}-1]})

	echo "get: $stg" >> $f
	echo "put: $stp" >> $f
	echo "total: $stt" >> $f

	stga=$(echo $stga + $stg | bc)
	stpa=$(echo $stpa + $stp | bc)
	stta=$(echo $stta + $stt | bc)

	echo >> $f
	echo >> $f

	rm $temp
done

python synthbx -s $b -m clean

echo "=== #MeanSynthTime" >> $f

stga=$(echo $stga / $nr | bc -l)
stpa=$(echo $stpa / $nr | bc -l)
stta=$(echo $stta / $nr | bc -l)

printf "m_st_get: %-8.2f | m_st_put: %-8.2f | m_st_total: %-8.2f\n" ${stga} ${stpa} ${stta} >> $f

echo >> $f
echo >> $f
printf "=== #Pair : " >> $f
echo $(grep 'Sp/Cp:' $f|sort -u|wc -l|sed 's/ //g') >> $f

echo >> $f
echo >> $f
printf "=== #WorseNFg : " >> $f
echo $(grep 'NFg : ' $f|cut -d: -f 2|sed 's/ //g'|sort -rnu|head -1) >> $f
