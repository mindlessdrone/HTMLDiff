import re
from collections import namedtuple

Node = namedtuple('Node', ['value', 'children'])

def build_tokens(data):

    SP       = r'(?P<sp>\s+)'
    TAG      = r'(?P<tag>\<\w+\>)'
    ETAG     = r'(?P<etag>\<\/\w+\>)'
    STR      = r'(?P<str>(.+?(?=\<)|(.+$)))'
    regex = '|'.join((SP, TAG, ETAG, STR))

    text_buffer = []
    text_line = 0
    for i, line in enumerate(data.split('\n')):
        for match in re.finditer(regex, line):
            groups = match.groupdict()
            print(groups)
            for k, v in groups.items():
                if k == 'str' and v is not None:
                    if not text_line: text_line = i + 1
                    text_buffer.append(v)
                    print(text_buffer)
                elif v and k != 'sp':
                    if text_buffer:
                        yield (text_line, 'str', ''.join(text_buffer))
                        text_buffer = []
                        text_line = 0
                    yield (i + 1,k,v.strip(),)

def build_tree(tokens):
    root = Node(None, [])     

    def _build_tree(curr_node):
        for token in tokens:
            curr_node.children.append(Node(token, []))
            if token[0] == 'etag': return
            if token[0] == 'tag': _build_tree(curr_node.children[-1])

    
    _build_tree(root)
    root.children.append(Node((0, 'eof', 'End of File'), []))
    return root

def compare_trees(t1, t2):
    pass
