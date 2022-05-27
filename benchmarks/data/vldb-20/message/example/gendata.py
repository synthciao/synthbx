from random import shuffle, choice

ppl = ['James', 'Robert', 'John', 'Michael', 'William',
       'David', 'Richard', 'Joseph', 'Ivan', 'Bob']

mid1 = list(range(1111, 3333, 2))
mid2 = list(range(1112, 3334, 2))
mtype = ['html', 'text']
text = ['null', 'not null']
date = ['2012-%02d-%02d' % (i, j) for i in list(range(1, 12))
        for j in list(range(2, 28))]
address = [x + '@mes' for x in ppl]
read = ['y', 'n']
sender = [x + '@mes' for x in ppl]

with open('messagecentre.facts', 'w') as fw:
    for i in range(15):
        print(
            f'{choice(mid1)}\t{choice(mtype)}\t{choice(text)}\t{choice(date)}\t{choice(address)}\t{choice(read)}\t{choice(sender)}', file=fw)

with open('messagecentreemail.facts', 'w') as fw:
    for i in range(20):
        print(
            f'{choice(mid2)}\t{choice(mtype)}\t{choice(text)}\t{choice(date)}\t{choice(address)}\t{choice(read)}\t{choice(sender)}', file=fw)
