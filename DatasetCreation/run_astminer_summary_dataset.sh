#Executes the astminer for each project individually
input_dir="../data/summary-dataset/validation/*"
output_dir="../data/summary-dataset/processed/validation/"
cd astminer
threads=10

#export PATH="/C/Program Files/Java/jdk-8/bin:"$PATH

run_astminer() {
  folder="$(basename $1)"
  ./cli.sh code2vec --lang py --project "${1}" --output "${output_dir}${folder}" --split-tokens --granularity method --hide-method-name --maxContexts 200
  cp "${1}/readme.md" "${output_dir}${folder}/readme.md"
}


(
for dir in $input_dir; do
   ((i=i%threads)); ((i++==0)) && wait
   run_astminer "$dir" &
done
)

wait
read myvar