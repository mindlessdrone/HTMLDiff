import re

def build_tokens(data):
    regex = r"(?P<sp>\s+)|(?P<tag>\<\w+\>)|(?P<etag>\<\/\w+\>)|(?P<str>[\w\s]+)"

    for i, line in enumerate(data.split('\n')):
        for match in re.finditer(regex, line):
            groups = match.groupdict()
            for k, v in groups.items():
                if v and k != 'sp': yield (i + 1,k,v,)
