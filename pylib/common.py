def read_tskv(filename):
    rows = []
    for line in open(filename):
        row = {}
        for token in line.strip().split("\t"):
            key, value = token.split('=', 1)
            row[key] = value
        rows.append(row)
    return rows
