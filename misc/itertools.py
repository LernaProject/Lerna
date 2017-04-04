import itertools


def indexed_groupby(iterable, key=None, start=0):
    for k, g in itertools.groupby(iterable, key):
        g = list(g)
        step = len(g)
        yield start, start + step, k, g
        start += step
