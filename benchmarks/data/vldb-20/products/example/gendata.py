from random import shuffle, choice

with open('subscriptions_agg.facts', 'w') as fw:
    for i in range(1011, 1021):
        print(f'{i}\t{choice(list(range(1,50)))}', file=fw)

with open('products_raw.facts', 'w') as fw:
    title = ['Case', 'RAM', 'HDD', 'SSD', 'Mouse', 'Keyboard',
             'Headset', 'Cooler', 'GPU', 'CPU', 'Motherboard', 'UPS', 'SPU']
    manuid = ['Corsair', 'EVGA', 'ASUS', 'Gigabyte', 'HP', 'Razer']
    created = ['2020-%02d-%02d' % (i, j)
               for i in range(1, 13)
               for j in range(1, 29)]
    description = ['null', 'none']
    mpn = ['null', 'none']
    visiable = ['T', 'F']

    for i in range(1001, 1041):
        c = choice(created)
        print(f'{i}\t{choice(title)}\t{choice(description)}\t{choice(manuid)}\t{c}\t{c}\t{choice(mpn)}\t{choice(visiable)}', file=fw)
