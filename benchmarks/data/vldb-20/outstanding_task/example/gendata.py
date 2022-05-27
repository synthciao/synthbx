from random import shuffle, choice

idl = list(range(1, 10))
pid = list(range(0, 4))

cid = list(range(500, 1000))
vid = list(range(50, 75))
mid = list(range(100000, 999999))
eid = list(range(100, 200))
result = ['D', 'A', 'W']
context = ['c0', 'c1', 'c2', 'c3']
guide = ['0', '1']
s_at = '2022-02-22 22:22:22'
e_at = '2022-02-22 23:59:59'
cu_at = '0000-00-00 00:00:00'


with open('task.facts', 'w') as fw:
    for i in idl:
        print(
            f'{i}\t{choice(pid)}\t{choice(cid)}\t{choice(vid)}\t{choice(mid)}\t{choice(eid)}\t{choice(result)}\t{choice(context)}\t{choice(guide)}\t{s_at}\t{e_at}\t{cu_at}\t{cu_at}', file=fw)
