from random import shuffle, choice

proid = list(range(101, 116))
wbought = ['20%02d-%02d-%02d' % (i, j, k)
           for i in list(range(17, 21))
           for j in list(range(1, 13))
           for k in list(range(1, 29))]


with open('purchase.facts2', 'w') as fw:
    for i in range(1001, 1051):
        print(
            f'{i}\t{choice(proid)}\t{choice(wbought)}', file=fw)
