input_dir="../data/"
output_dir="../data/output"
cd astminer
./cli.sh code2vec --lang py --project $input_dir --output $output_dir --split-tokens --granularity method --hide-method-name --maxContexts 1000