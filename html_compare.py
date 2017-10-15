import re
import sys
import threading
import queue
from collections import namedtuple

# namedtuple class factories
Node = namedtuple('Node', ['value', 'children'])
Elem = namedtuple('Elem', ['line', 'type', 'value'])

class HTMLCompare:
    """HTMLCompare: class that compares two HTML files together"""

    def __init__(self, file1, file2):
        """__init__: class constructor

        :param file1: first html file
        :param file2: second html file
        """

        # create priority queue to store trees and html file lines
        self.tree_queue = queue.PriorityQueue()
        
        # create workers to read in files and build parse trees
        self.worker1 = threading.Thread(target=self._worker, args=(1, file1,))
        self.worker2 = threading.Thread(target=self._worker, args=(2, file2,))

    def _worker(self, worker_id, fn):
        """_worker: thread function, reads in files and builds parse trees

        :param worker_id: id of worker, helps to keep results in order
        :param fn: file name of the HTML file to be read in
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
        """token_iterator: generator that returns a stream of lexemes

        :param lines: lines of text to be read in
        """

        # regex for all lexemes
        SP       = r'(?P<sp>\s+)'
        TAG      = r'(?P<tag>\<\w+\>)'
        ETAG     = r'(?P<etag>\<\/\w+\>)'
        VTAG     = r'(?P<vtag>\<\w+\s*\/\>)'
        STR      = r'(?P<str>(.+?(?=\<)|(.+$)))'
        regex = '|'.join((SP, TAG, ETAG, VTAG, STR))

        # some state to handle multiline text
        text_buffer = []
        text_line = 0

        # iterate over lines
        for i, line in enumerate(lines):

            # for every match found
            for match in re.finditer(regex, line):
                groups = match.groupdict()

                for k, v in groups.items():

                    # we've encountered text and have to handle it accordingly
                    if k == 'str' and v is not None:
                        if not text_line: text_line = i
                        text_buffer.append(v.strip())

                    # we've encountered another lexeme
                    elif v and k != 'sp':
                        
                        # if we have text we've collected we want to yield that first
                        if text_buffer:
                            yield Elem(text_line, 'str', ' '.join(text_buffer))

                            # reset state
                            text_buffer = []
                            text_line = 0

                        # yield lexeme
                        yield Elem(i, k, v.strip())

    def build_tree(self, tokens):
        """build_tree: builds parse tree

        :param tokens: token generator object
        """

        # add root node
        root = Node(None, [])

        def _build_tree(curr_node):
            """_build_tree: recursive function to build parse tree

            :param curr_node: current node to add children to.
            """
            for token in tokens:
                curr_node.children.append(Node(token, []))
                if token.type == 'etag': return
                if token.type == 'tag': _build_tree(curr_node.children[-1])


        # build the tree!
        _build_tree(root)

        # add EOF node
        root.children.append(Node(Elem(-1, 'eof', 'End of File'), []))

        return root

    def compare(self):
        """compare: compares the two HTML files"""

        # flag to see 
        self.same = True

        # start both workers
        self.worker1.start()
        self.worker2.start()

        # wait for workers to finish
        self.worker1.join()
        self.worker2.join()

        # grab both trees generated from html files
        root1, self.lines1 = self.tree_queue.get()[1:]
        root2, self.lines2 = self.tree_queue.get()[1:]

        # append EOF tag to end of lines (for display purposes)
        self.lines1.append('End-of-File')
        self.lines2.append('End-of-File')

        # compare them!
        self._compare(root1, root2)

        # print if they match or not
        if self.same: print("Files match.")
        else: print("Files do not match.")

    def _mismatch(self, line_num1, line_num2, val1, val2):
        """_mismatch: reports non-text mismatches

        :param line_num1: line number for file 1 of mismatch
        :param line_num2: line number for file 2 of mismatch
        :param val1: value for file 1
        :param val2: value for file 2
        """
        print('On the following lines...')
        print('file 1: %d. %s' % (line_num1 + 1, self.lines1[line_num1]))
        print('file 2: %d. %s' % (line_num2 + 1, self.lines2[line_num2]))
        print('%s != %s. attempting to continue at end of section.\n' % (val1, val2))

    def _text_mismatch(self, line_num1, line_num2, val1, val2):
        """_text_mismatch: reports text mismatches

        :param line_num1: line number for file 1 of mismatch
        :param line_num2: line number for file 2 of mismatch
        :param val1: value for file 1
        :param val2: value for file 2
        """
        print('On the following lines...')
        print('file 1: %d. %s' % (line_num1 + 1, self.lines1[line_num1]))
        print('file 2: %d. %s' % (line_num2 + 1, self.lines2[line_num2]))
        print('%s != %s. simple text mismatch; continuing...\n' % (val1, val2))

    def _compare(self, n1, n2):
        """_compare: recursive function to compare the children of two nodes

        :param n1: first current node
        :param n2: second current node
        """

        # for each child in both node1 and node2
        for c1, c2 in zip(n1.children, n2.children):
            # unpack Elem tuples
            line1, c1_type, c1_value = c1.value
            line2, c2_type, c2_value = c2.value

            # if there was a simple text mismatch
            if (c1_type == 'str' and c2_type == 'str') and c1_value != c2_value:
                # files no longer match, print mismatch
                self.same = False
                self._text_mismatch(line1, line2, c1_value, c2_value)

            # if there is another type of mismatch
            elif c1.value[1:] != c2.value[1:]:
                # files no longer match, print mismatch
                self.same = False
                self._mismatch(line1, line2, c1_value, c2_value)

                # stop comparing the children
                return

            # go down the tree!
            self._compare(c1, c2)

def main():
    """main: entry point for program"""

    # create the object and compare the files
    file_compare = HTMLCompare(sys.argv[1], sys.argv[2])
    file_compare.compare()

if __name__ == '__main__': main()
