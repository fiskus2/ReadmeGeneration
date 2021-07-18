#Executes the astminer for each project individually, so they can be dist
input_dir="../data/summary-dataset/train/*"
output_dir="../data/summary-dataset/processed/train/"
cd astminer
export PATH="/C/Program Files/Java/jdk-8/bin:"$PATH

for dir in $input_dir; do
  folder="$(basename $dir)"
  ./cli.sh code2vec --lang py --project "${dir}" --output "${output_dir}${folder}" --split-tokens --granularity method --hide-method-name --maxContexts 200
  cp "${dir}/readme.md" "${output_dir}${folder}/readme.md"
done

read myvar