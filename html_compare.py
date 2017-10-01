import re

def build_tokens(data):

    TAG  = r'(?P<tag>\<\w+\>)'
    ETAG = r'(?P<etag>\<\/\w+\>)'
    STR  = r'(?P<str>.+?(?=\<))'
    regex = '|'.join((TAG, ETAG, STR))

    for i, line in enumerate(data.split('\n')):
        for match in re.finditer(regex, line):
            groups = match.groupdict()
            for k, v in groups.items():
                if v and k != 'sp': yield (i + 1,k,v,)
