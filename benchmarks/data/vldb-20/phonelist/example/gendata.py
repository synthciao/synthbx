from random import shuffle, choice

lname = ['Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez',
         'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson', 'Thomas', 'Taylor']
fname = ['James', 'Robert', 'John', 'Michael', 'William',
         'David', 'Richard', 'Joseph', 'Ivan', 'Jeans']

id1 = ['1%02d' % x for x in range(1, 99)]
id2 = ['2%02d' % x for x in range(1, 99)]
id3 = ['3%02d' % x for x in range(1, 99)]

num = ['44', '1', '84', '81', '86', '33', '49', '61', '7']

fw1 = open('customer.facts', 'w')
fw2 = open('supplier.facts', 'w')
fw3 = open('vendor.facts', 'w')


for i in range(10):
    t = choice(num)
    d = list(range(10))
    x = '+%s-%d%d%d%d-%d%d%d%d' % (t, choice(d), choice(d), choice(
        d), choice(d), choice(d), choice(d), choice(d), choice(d))
    print(
        f'{choice(id1)}\t{t}\t{choice(lname)}\t{choice(fname)}\t{x}', file=fw1)

for i in range(15):
    t = choice(num)
    d = list(range(10))
    x = '+%s-%d%d%d%d-%d%d%d%d' % (t, choice(d), choice(d), choice(
        d), choice(d), choice(d), choice(d), choice(d), choice(d))
    print(
        f'{choice(id2)}\t{t}\t{choice(lname)}\t{choice(fname)}\t{x}', file=fw2)

for i in range(8):
    t = choice(num)
    d = list(range(10))
    x = '+%s-%d%d%d%d-%d%d%d%d' % (t, choice(d), choice(d), choice(
        d), choice(d), choice(d), choice(d), choice(d), choice(d))
    print(
        f'{choice(id3)}\t{t}\t{choice(lname)}\t{choice(fname)}\t{x}', file=fw3)

fw1.close()
fw2.close()
fw3.close()
