import re
from collections import namedtuple

Node = namedtuple('Node', ['value', 'children'])

def build_tokens(data):

    TAG  = r'(?P<tag>\<\w+\>)'
    ETAG = r'(?P<etag>\<\/\w+\>)'
    STR  = r'(?P<str>.+?(?=\<))'
    regex = '|'.join((TAG, ETAG, STR))

    for i, line in enumerate(data.split('\n')):
        for match in re.finditer(regex, line):
            groups = match.groupdict()
            for k, v in groups.items():
                if v: yield (i + 1,k,v.strip(),)

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


