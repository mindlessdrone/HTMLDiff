import re
import sys
import threading
import queue
from collections import namedtuple

Node = namedtuple('Node', ['value', 'children'])
Elem = namedtuple('Elem', ['line', 'type', 'value'])

class HTMLCompare:
    def __init__(self, file1, file2):
        self.tree_queue = queue.Queue()
        
        worker1 = threading.Thread(target=self._worker, args=(file1,))
        worker2 = threading.Thread(target=self._worker, args=(file2,))

        worker1.start()
        worker2.start()

        worker1.join()
        worker2.join()

    def _worker(self, fn):

        # open file and read in lines of text
        with open(fn) as f:
            lines = f.readlines()

        # build token iterator
        tokens = self.token_iterator(lines)

        # build tree
        tree = self.build_tree(tokens)

        # add tree and file lines to queue
        self.tree_queue.put((tree, lines,))

    def token_iterator(self, lines):

        SP       = r'(?P<sp>\s+)'
        TAG      = r'(?P<tag>\<\w+\>)'
        ETAG     = r'(?P<etag>\<\/\w+\>)'
        VTAG     = r'(?P<vtag>\<\w+\s*\/\>)'
        STR      = r'(?P<str>(.+?(?=\<)|(.+$)))'
        regex = '|'.join((SP, TAG, ETAG, VTAG, STR))

        text_buffer = []
        text_line = 0
        for i, line in enumerate(lines):
            for match in re.finditer(regex, line):
                groups = match.groupdict()
                for k, v in groups.items():
                    if k == 'str' and v is not None:
                        if not text_line: text_line = i + 1
                        text_buffer.append(v.strip())
                    elif v and k != 'sp':
                        if text_buffer:
                            yield Elem(text_line, 'str', ' '.join(text_buffer))
                            text_buffer = []
                            text_line = 0
                        yield Elem(i + 1, k, v.strip())

    def build_tree(self, tokens):
        root = Node(None, [])

        def _build_tree(curr_node):
            for token in tokens:
                curr_node.children.append(Node(token, []))
                if token.type == 'etag': return
                if token.type == 'tag': _build_tree(curr_node.children[-1])

    
        _build_tree(root)
        root.children.append(Node(Elem(0, 'eof', 'End of File'), []))
        return root

def compare_trees(node1, node2):
    for c1, c2 in zip(node1.children, node2.children):
        c1_type, c1_value = c1.value[1:]
        c2_type, c2_value = c2.value[1:]

        if (c1_type == 'str' and c2_type == 'str') and c1_value != c2_value:
            print("text mismatch: %s != %s, continuing" % (c1_value, c2_value))
        elif c1.value[1:] != c2.value[1:]:
            print("%s != %s" % (c1_value, c2_value))
            return
        compare_trees(c1, c2)


def main():
    file_compare = HTMLCompare(sys.argv[1], sys.argv[2])

if __name__ == '__main__': main()
