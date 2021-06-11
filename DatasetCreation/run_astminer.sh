input_dir="./data/python-projects-med/train"
output_dir="./data/python-projects-med/astminer/train"
./astminer/cli.sh code2vec --lang py --project $input_dir --output $output_dir --split-tokens --granularity method --hide-method-name --maxContexts 200