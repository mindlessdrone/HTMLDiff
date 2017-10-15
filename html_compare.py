import re
import sys
import threading
import queue
from collections import namedtuple

Node = namedtuple('Node', ['value', 'children'])
Elem = namedtuple('Elem', ['line', 'type', 'value'])

class HTMLCompare:
    def __init__(self, file1, file2):
        self.tree_queue = queue.PriorityQueue()
        
        self.worker1 = threading.Thread(target=self._worker, args=(1, file1,))
        self.worker2 = threading.Thread(target=self._worker, args=(2, file2,))

    def _worker(self, worker_id, fn):
        """_worker

        :param worker_id:
        :param fn:
        """

        # open file and read in lines of text
        with open(fn) as f:
            lines = [line.strip() for line in f.readlines()]

        # build token iterator
        tokens = self.token_iterator(lines)

        # build tree
        tree = self.build_tree(tokens)

        # add tree and file lines to queue
        self.tree_queue.put((worker_id, tree, lines,))

    def token_iterator(self, lines):
        """token_iterator

        :param lines:
        """

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
                        if not text_line: text_line = i
                        text_buffer.append(v.strip())
                    elif v and k != 'sp':
                        if text_buffer:
                            yield Elem(text_line, 'str', ' '.join(text_buffer))
                            text_buffer = []
                            text_line = 0
                        yield Elem(i, k, v.strip())

    def build_tree(self, tokens):
        """build_tree

        :param tokens:
        """
        root = Node(None, [])

        def _build_tree(curr_node):
            for token in tokens:
                curr_node.children.append(Node(token, []))
                if token.type == 'etag': return
                if token.type == 'tag': _build_tree(curr_node.children[-1])

    
        _build_tree(root)
        root.children.append(Node(Elem(-1, 'eof', 'End of File'), []))
        return root

    def compare(self):
        """compare"""
        self.same = True

        self.worker1.start()
        self.worker2.start()

        self.worker1.join()
        self.worker2.join()

        # grab both trees generated from html files
        root1, self.lines1 = self.tree_queue.get()[1:]
        root2, self.lines2 = self.tree_queue.get()[1:]

        self.lines1.append('End-of-File')
        self.lines2.append('End-of-File')

        # compare them!
        self._compare(root1, root2)

        if self.same: print("Files match.")
        else: print("Files do not match.")

    def _mismatch(self, line_num1, line_num2, val1, val2):
        """_mismatch

        :param line_num1:
        :param line_num2:
        :param val1:
        :param val2:
        """
        print('On the following lines...')
        print('file 1: %d. %s' % (line_num1 + 1, self.lines1[line_num1]))
        print('file 2: %d. %s' % (line_num2 + 1, self.lines2[line_num2]))
        print('%s != %s. attempting to continue at end of section.\n' % (val1, val2))

    def _text_mismatch(self, line_num1, line_num2, val1, val2):
        """_text_mismatch

        :param line_num1:
        :param line_num2:
        :param val1:
        :param val2:
        """
        print('On the following lines...')
        print('file 1: %d. %s' % (line_num1 + 1, self.lines1[line_num1]))
        print('file 2: %d. %s' % (line_num2 + 1, self.lines2[line_num2]))
        print('%s != %s. simple text mismatch; continuing...\n' % (val1, val2))

    def _compare(self, n1, n2):
        """_compare

        :param n1:
        :param n2:
        """
        for c1, c2 in zip(n1.children, n2.children):
            line1, c1_type, c1_value = c1.value
            line2, c2_type, c2_value = c2.value

            if (c1_type == 'str' and c2_type == 'str') and c1_value != c2_value:
                self.same = False
                self._text_mismatch(line1, line2, c1_value, c2_value)
            elif c1.value[1:] != c2.value[1:]:
                self.same = False
                self._mismatch(line1, line2, c1_value, c2_value)
                return
            self._compare(c1, c2)

def main():
    """main"""
    file_compare = HTMLCompare(sys.argv[1], sys.argv[2])
    file_compare.compare()

if __name__ == '__main__': main()
