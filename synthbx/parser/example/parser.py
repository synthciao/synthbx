from synthbx.ast.example import Example, ExampleStatus
from synthbx.ast.table import Table, TableBase, TableStatus
from synthbx.util.io import load_data, get_ext_files
from synthbx.env.const import EExt, ESuffix


def parse_example(path, schema):
    inputs = schema.input()
    outputs = schema.output()

    fact_files = get_ext_files(path, EExt.FACT)
    expt_files = get_ext_files(path, EExt.EXPT)

    e_source, e_source_update, e_view_update = check_existance(
        inputs, outputs, fact_files, expt_files
    )

    t_source, t_source_update, t_view_update = make_tables(
        e_source, e_source_update, e_view_update, path
    )

    tables = t_source + t_source_update + t_view_update

    return Example(tables=tables, status=ExampleStatus.PROVIDED)


def check_existance(inputs, outputs, fact_files, expt_files):
    e_source, e_source_update, e_view_update = [], [], []
    f = True

    nl_fact = [n[:-len(EExt.FACT)] for n in fact_files]
    nl_expt = [n[:-len(EExt.EXPT)] for n in expt_files]

    message = ''
    # e_source
    for inp in inputs:
        if inp.name not in nl_fact:
            f = False
            message = f'Require source {inp.name}{EExt.FACT} in example!'
        else:
            e_source.append(inp)

    # e_source_update
    for inp in inputs:
        if inp.name + ESuffix.UPDATE not in nl_expt:
            f = False
            message = f'Require updated source {inp.name}{EExt.EXPT} in example!'
        else:
            e_source_update.append(inp)

    # e_view_update
    for outp in outputs:
        if outp.name + ESuffix.UPDATE in nl_fact:
            e_view_update.append(outp)

    if not e_view_update:
        f = False
        err_str = '|'.join(
            [outp.name + ESuffix.UPDATE for outp in outputs]
        )
        message = f'Require updated view ({err_str}){EExt.FACT} in example!'

    if not f:
        raise FileNotFoundError(message)

    return e_source, e_source_update, e_view_update


def make_tables(e_source, e_source_update, e_view_update, path):
    t_source, t_source_update, t_view_update = [], [], []

    for es in e_source:
        t_source.append(
            Table(
                name=es.name,
                types=es.schema,
                base=TableBase.STATE,
                status=TableStatus.ORIGINAL,
                data=load_data(
                    f'{path}/{es.name}{EExt.FACT}'
                )
            )
        )

    for esu in e_source_update:
        t_source_update.append(
            Table(
                name=esu.name,
                types=esu.schema,
                base=TableBase.STATE,
                status=TableStatus.UPDATED,
                data=load_data(
                    f'{path}/{esu.name}{ESuffix.UPDATE}{EExt.EXPT}'
                )
            )
        )

    for evu in e_view_update:
        t_view_update.append(
            Table(
                name=evu.name,
                types=evu.schema,
                base=TableBase.STATE,
                status=TableStatus.UPDATED,
                data=load_data(
                    f'{path}/{evu.name}{ESuffix.UPDATE}{EExt.FACT}'
                )
            )
        )

    return t_source, t_source_update, t_view_update


if __name__ == '__main__':
    import sys
    sql = sys.argv[1]
    path = f'./benchmarks/data/{sql}'

    schema_path = f'{path}/schema/{sql[sql.rfind("/")+1:]}.sc'
    ex_path = f'{path}/example'
    data1 = open(schema_path, 'r').read()
    from synthbx.parser.schema.parser import parse_schema
    schema = parse_schema(data1)

    example = parse_example(ex_path, schema)
    print(example)

    source, view, invent = schema.partition()

    print('------ SOURCE ------')
    print(source)

    print('------ VIEW ------')
    print(view)

    print('------ INVENT ------')
    print(invent)
