from random import shuffle, choice

cityid2 = ['2%02d' % i for i in list(range(10))]
cityid3 = ['3%02d' % i for i in list(range(15))]
logdate2 = ['2006-02-%02d' % i for i in list(range(1, 21, 2))]
logdate3 = ['2006-03-%02d' % i for i in list(range(1, 16, 1))]
peaktemp = [15, 16, 17, 18, 19, 20, 21, 22, 23]
unitsales = [50, 100, 150, 200, 245, 250, 300, 500]


with open('measurement_y2006m02.facts', 'w') as fw:
    for i, c in enumerate(cityid2):
        print(
            f'{c}\t{logdate2[i]}\t{choice(peaktemp)}\t{choice(unitsales)}', file=fw)

with open('measurement_y2006m03.facts', 'w') as fw:
    for i, c in enumerate(cityid3):
        print(
            f'{c}\t{logdate3[i]}\t{choice(peaktemp)}\t{choice(unitsales)}', file=fw)
