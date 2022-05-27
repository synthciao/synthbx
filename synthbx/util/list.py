def flatten(l):
    """
    flatten([[1,2,3],0,[4,5]]) -> generator(1,2,3,0,4,5)
    """
    for i in l:
        if type(i) is list:
            yield from flatten(i)
        else:
            yield i


def mapin(l, lx):
    """
    mapin([2,1,5], [1,5,2,4,3]) = [2,0,1]
    """
    return [lx.index(i) for i in l if i in lx]


def mapto(l, m):
    """
    mapto(['a','b','c','d','e'], [2,0,1]) = ['c','a','b']
    """
    out = []
    for i in range(len(m)):
        try:
            out.append(l[m[i]])
        except:
            return []
    return out
