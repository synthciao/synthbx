from random import shuffle, choice

nazwa_klubu = []
adres = []
for x in range(10, 100):
    nazwa_klubu.append('k' + str(x))
    adres.append('a' + str(x))

nazwa_zespolu = []
ilosc_czlonkow = []
for x in range(200, 300):
    nazwa_zespolu.append('z' + str(x))
    ilosc_czlonkow.append('ic' + str(x))

data_wystepu = ['dat' + str(x) for x in range(1000, 2000)]


with open('klub.facts', 'w') as fw:
    for i, k in enumerate(nazwa_klubu):
        print(
            f'{k}\t{adres[i]}', file=fw)

with open('zespol.facts', 'w') as fw:
    for i, z in enumerate(nazwa_zespolu):
        print(
            f'{z}\t{ilosc_czlonkow[i]}', file=fw)

with open('koncert.facts', 'w') as fw:
    for i in range(20):
        nk = choice(nazwa_klubu)
        nazwa_klubu.remove(nk)
        nz = choice(nazwa_zespolu)
        nazwa_zespolu.remove(nz)

        print(
            f'{nk}\t{nz}\t{choice(data_wystepu)}', file=fw
        )
