from pathlib import Path
import operator
import re

def parse_node_vocab(dataset_path):
    with open(dataset_path + 'node_types.csv') as file:
        content = file.readlines()

    content = content[1:]  # remove header
    node_vocab = {}
    for line in content:
        # example line: 485,arglist|argument|test UP\n
        line = line[:-1]

        id, rest = line.split(',')
        rest, direction = rest.split(' ') # The direction is irrelevant for code2seq and is discarded.

        # Due to Pythons grammar, there are often chains of nodes with only one child.
        # Only the end of the chain is relevant
        if '|' in rest:
            node = rest.split('|')[-1]
        else:
            node = rest

        node_vocab[id] = [node]

    return node_vocab

def parse_token_vocab(dataset_path):
    with open(dataset_path + 'tokens.csv', encoding="ISO-8859-1") as file:
        content = file.readlines()

    content = content[1:]  # remove header
    token_vocab = {}
    for line in content:
        # example line: 51817,get|count\n
        line = line[:-1]
        id = re.match('^([0-9]+),', line)
        if id == None:
            #Malformed line
            continue

        id = id.group(1)
        rest = line[len(id) + 1:]

        rest_is_whitespace = re.match('^(\s|\\\\n)*$', rest) != None
        if rest_is_whitespace:
            tokens = ['escapedWhitespace']
            token_vocab[id] = tokens
            continue

        rest_is_string = (rest[0] == "'" or rest[0] == '"') and rest[0] == rest[-1]

        # Docstrings occur in the AST but are usually to long to sensibly subtokenize and process
        if '"""' in rest or "'''" in rest:
            continue

        if '|' in rest and not rest_is_string and (rest.count('"') > 1 or rest.count("'") > 1):
            #Too difficult to process for now
            continue

        if rest_is_string:
            rest = rest.replace(' ', 'escapedSpace')
            rest = rest.replace(',', 'escapedComma')
            rest = rest.replace('|', 'escapedOr')
            tokens = [rest]


        elif rest == '|':
            tokens = ['escapedOr']

        elif rest == ',':
            tokens = ['escapedComma']

        else:
            assert ',' not in rest
            tokens = rest.split('|')

            if '|||' in rest:  # the token | itself is not escaped and would be confused with a separator
                tokens = [token for token in tokens if token != '']
                tokens.append('escapedOr')


        token_vocab[id] = tokens

    return token_vocab

def parse_path_vocab(dataset_path):
    with open(dataset_path + 'paths.csv') as file:
        content = file.readlines()

    content = content[1:]  # remove header
    path_vocab = {}
    for line in content:
        # example line: 341857,103 1283 571 311\n
        line = line[:-1]

        id, rest = line.split(',')
        node_ids = rest.split(' ')
        path_vocab[id] = node_ids

    return path_vocab

def main():
    dataset_path = "./data/python-projects-med/astminer/train/py"
    output_path = "./data/python-projects-med/postprocessed/"
    max_contexts = 200

    Path(output_path).mkdir(parents=True, exist_ok=True)

    path_vocab = parse_path_vocab(dataset_path)
    token_vocab = parse_token_vocab(dataset_path)
    node_vocab = parse_node_vocab(dataset_path)

    target_histogram = {}
    token_histogram = {}
    node_histogram = {}

    with open(dataset_path + 'path_contexts.csv') as file:
        with open(output_path + 'data.csv', 'w', encoding="ISO-8859-1") as new_context_file:
            for line in file.readlines():
                # example line: processitem 15,199,4 15,200,16 15,199,4\n
                line = line[:-1]

                parts = line.split(' ')
                targets = parts[0].split('|')
                contexts = parts[1:]

                #update target_histogram
                for target in targets:
                    try:
                        target_histogram[target] += 1
                    except KeyError:
                        target_histogram[target] = 1

                # update node_histogram
                new_contexts = []
                context_num = 0
                for context in contexts:
                    #example context: 15,199,4

                    context_nodes = []
                    parts = context.split(',')
                    node_ids = path_vocab[parts[1]]
                    for node_id in node_ids:
                        nodes = node_vocab[node_id]
                        context_nodes = context_nodes + nodes
                        for node in nodes:
                            try:
                                node_histogram[node] += 1
                            except KeyError:
                                node_histogram[node] = 1

                    new_context_string = '|'.join(context_nodes)

                    # update token_histogram
                    front = True
                    discard = False
                    for token_id in [parts[0], parts[2]]:
                        try:
                            token = token_vocab[token_id]
                            for subtoken in token:
                                try:
                                    token_histogram[subtoken] += 1
                                except KeyError:
                                    token_histogram[subtoken] = 1

                            if front:
                                new_context_string = '|'.join(token) + ',' + new_context_string
                                front = False
                            else:
                                new_context_string = new_context_string + ',' + '|'.join(token)

                        except KeyError:
                            discard = True
                            break

                    if not discard:
                        new_contexts.append(new_context_string)
                        context_num += 1

                space_padding = ' ' * (max_contexts - context_num)
                new_context_file.write('|'.join(targets) + ' ' + ' '.join(new_contexts) + space_padding + '\n')

    target_histogram = dict(sorted(target_histogram.items(), key=operator.itemgetter(1), reverse=True))
    node_histogram = dict(sorted(node_histogram.items(), key=operator.itemgetter(1), reverse=True))
    token_histogram = dict(sorted(token_histogram.items(), key=operator.itemgetter(1), reverse=True))

    with open(output_path + 'target_histogram.csv', 'w', encoding="ISO-8859-1") as file:
        for key, val in target_histogram.items():
            file.write(key + ',' + str(val) + '\n')

    with open(output_path + 'token_histogram.csv', 'w', encoding="ISO-8859-1") as file:
        for key, val in token_histogram.items():
            file.write(key + ',' + str(val) + '\n')

    with open(output_path + 'node_histogram.csv', 'w', encoding="ISO-8859-1") as file:
        for key, val in node_histogram.items():
            file.write(key + ',' + str(val) + '\n')

if __name__ == '__main__':
    main()