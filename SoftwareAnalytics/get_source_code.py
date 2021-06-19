import token, tokenize
import re

#Returns the code of a node in the callgraph. Comments and annotations are removed
def get_source_code(module_to_filename, node):
    blacklist = []
    blacklist.append('*')
    blacklist.append('---')
    blacklist.append('???')
    blacklist.append('^^^')

    if any([symbol in node for symbol in blacklist]):
        assert False

    is_module = node.startswith('<Node module:')
    is_class = node.startswith('<Node class:')
    is_function = node.startswith('<Node function:')
    is_method = node.startswith('<Node method:')

    # e.g.:
    # <Node function:httpie.client.collect_messages>
    # httpie.client.collect_messages>
    # httpie.client.collect_messages
    node = node[node.find(':') + 1:]
    node = node[:-1]

    parts = node.split('.')
    current_module = node
    module_end_index = len(parts) - 1
    while current_module not in module_to_filename:
        current_module = '.'.join(parts[:module_end_index])
        module_end_index -= 1

    filename = module_to_filename[current_module]

    with open(filename) as file:
        file_content = file.readlines()

    file_content = remove_comments(file_content)
    file_content = file_content.split('\n')
    file_content = remove_annotations(file_content)
    file_content = [line for line in file_content if re.match('^\s+$', line) is None]

    if is_module:
        code = get_module(file_content)

    elif is_function:
        function = parts[-1]
        code = get_function(file_content, function)

    elif is_method:
        class_name = parts[-2]
        function = parts[-1]
        code = get_method(file_content, class_name, function)

    elif is_class:
        class_name = parts[-1]
        code = get_class(file_content, class_name)

    else:
        assert False

    return code


def get_module(file_content):
    keep = False
    script = []
    for line in file_content:
        if not (line.startswith(' ') or line.startswith('\t') or line == ''):
            keep = not line.startswith('class ') and not line.startswith('def ')
        if keep:
            script.append(line)
    return script

def get_class(file_content, class_name):
    keep = False
    in_correct_class = False
    function = []
    class_indentation = ''
    first_indentation = False
    for n in range(len(file_content)):
        line = file_content[n]

        if first_indentation:
            class_indentation = re.match('^(\s*)', line).group(0)
            first_indentation = len(class_indentation) == 0 \
                                or file_content[n-1].endswith('\\')
            if first_indentation:
                continue

        if in_correct_class:
            in_correct_class = line.startswith(class_indentation) or line == ''
        else:
            in_correct_class = line.startswith('class ' + class_name + ':')
            first_indentation = in_correct_class

        keep = in_correct_class and \
               not line.startswith(class_indentation + 'def ') and \
               (not line.startswith(class_indentation + 'class ') or \
               line.startswith(class_indentation + 'class ' + class_name)) and \
               re.match('^' + class_indentation + '([^\s])', line) is not None


        if keep:
            function.append(line)
    return function


def get_function(file_content, function_name):
    assert sum([1 if line.startswith('def ' + function_name) else 0 for line in file_content]) <= 1

    keep = False
    function = []
    indentation = ''
    for line in file_content:
        if keep:
            keep = line == '' or line.isspace() or (line.startswith(indentation) and line[len(indentation)].isspace())
        else:
            search = re.search(r'(\s*)def ' + function_name + r'\(', line)
            keep = search != None
            if keep:
                indentation = search.group(1)

        if not (line.startswith(' ') or line.startswith('\t') or line == ''):
            keep = line.startswith('def ' + function_name + '(')

        if keep:
            function.append(line)
    return function

def get_method(file_content, class_name, method_name):
    #TODO: allow methods not to be unique within a file

    keep = False
    in_correct_class = False
    function = []
    class_indentation = ''
    first_indentation = False
    for n in range(len(file_content)):
        line = file_content[n]

        if first_indentation:
            class_indentation = re.match('^(\s*)', line).group(0)
            first_indentation = len(class_indentation) == 0 \
                                or file_content[n-1].endswith('\\')
            if first_indentation:
                continue

        if in_correct_class:
            in_correct_class = (not line.startswith('class ') and not line.startswith('def ')) \
            and (line.startswith(' ') or line.startswith('\t') or line.startswith('#') or line == '')
        else:
            in_correct_class = line.startswith('class ' + class_name)
            first_indentation = in_correct_class


        if keep:
            keep = in_correct_class and not line.startswith(class_indentation + 'def ')
        else:
            keep = line.startswith(class_indentation + 'def ' + method_name + '(')

        keep = keep and in_correct_class

        if keep:
            function.append(line)
    return function

#Adapted from: https://gist.github.com/BroHui/aca2b8e6e6bdf3cb4af4b246c9837fa3
def remove_comments(code):
    iterator = code.__iter__()
    result = ''
    prev_toktype = token.INDENT
    first_line = None
    last_lineno = -1
    last_col = 0

    tokgen = tokenize.generate_tokens(iterator.__next__)
    for toktype, ttext, (slineno, scol), (elineno, ecol), ltext in tokgen:
        if 0:  # Change to if 1 to see the tokens fly by.
            print("%10s %-14s %-20r %r" % (
                tokenize.tok_name.get(toktype, toktype),
                "%d.%d-%d.%d" % (slineno, scol, elineno, ecol),
                ttext, ltext
            ))
        if slineno > last_lineno:
            last_col = 0
        if scol > last_col:
            result = result + " " * (scol - last_col)
        if toktype == token.STRING and prev_toktype == token.INDENT:
            # Docstring
            continue
        elif toktype == tokenize.COMMENT:
            # Comment
            continue
        else:
            result = result + ttext
        prev_toktype = toktype
        last_col = ecol
        last_lineno = elineno

    return result


def remove_annotations(text):
    return [line for line in text if re.search(r'^\s*@', line) is None]