from random import shuffle, choice

poiid1 = list(range(1, 1000))
poiid2 = list(range(1, 1000, 2))

cola = list(range(100, 250))
colb = list(range(250, 500))
colc = list(range(500, 600))

cold = ['d' + str(x) for x in list(range(100, 400))]
cole = ['e' + str(x) for x in list(range(100, 400))]
colf = ['f' + str(x) for x in list(range(100, 400))]


# with open('poi.facts', 'w') as fw:
#     for i in poiid1:
#         print(
#             f'{i}\t{choice(cola)}\t{choice(colb)}\t{choice(colc)}', file=fw)

# with open('points.facts', 'w') as fw:
#     for i in poiid2:
#         print(
#             f'{i}\t{choice(cold)}\t{choice(cole)}\t{choice(colf)}', file=fw)

with open('update.test', 'w') as fw:
    for i in range(1001, 1200, 2):
        print(
            f'{i}\t{choice(cola)}\t{choice(colb)}\t{choice(cold)}\t{choice(cole)}', file=fw
        )
