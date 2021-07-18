from make_inlining_dataset import get_first_sentences_as_function_name
import os
from glob import glob
import json

def main():
    # input_dir shall contain 'train', 'test' and 'validation' folders, which contain the extracted .jsonl files
    input_dir = './python/python/final/jsonl/'
    output_dir = './data/docstring-dataset/'

    os.makedirs(output_dir, exist_ok=True)

    dirs = glob(os.path.join(input_dir, '*'))
    if len(dirs) == 0:
        dirs = [input_dir]

    for dir in dirs:
        parts = glob(os.path.join(dir, '*.jsonl'))
        base_dir = os.path.join(output_dir, os.path.basename(dir))
        os.makedirs(base_dir, exist_ok=True)

        for part in parts:
            with open(part) as file:
                content = file.readlines()
            data = [json.loads(jline) for jline in content]

            for i in range(len(data)):
                entry = data[i]
                new_name = get_first_sentences_as_function_name(entry['docstring'], -1)
                new_name = new_name.split('_')
                if len(new_name) > 100:
                    new_name = new_name[:100]
                new_name = '_'.join(new_name)

                code = entry['code']
                code = 'def ' + new_name + code[code.index('('):]

                with open(os.path.join(base_dir, str(i) + '.py'), 'w', encoding="UTF-8") as file:
                    file.write(code)



if __name__ == '__main__':
    main()