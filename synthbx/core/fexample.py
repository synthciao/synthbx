from synthbx.ast.example import Example, ExampleStatus
from synthbx.ast.table import Table, TableBase, TableStatus
from synthbx.env.const import EExt, ESuffix
from synthbx.util.io import load_data, store_data, get_ext_files


def upgrade_to_fexample(example, schema_partition, relation_decls, path):
    example.status = ExampleStatus.COMPUTED

    source, view, _ = schema_partition

    # add state-based tables of view
    for v in view:
        example.tables.append(
            Table(
                name=v.name,
                types=v.schema,
                base=TableBase.STATE,
                status=TableStatus.ORIGINAL,
                data=load_data(f'{path}/{v.name}{EExt.EXPT}')
            )
        )

    # add fw and bw state-based tables of middle relations
    source_names = [s.name for s in source]
    view_names = [v.name for v in view]

    mid_files = {f[:-len(EExt.EXPT)] for f in get_ext_files(path, EExt.EXPT)}

    sv_files = set()
    for f in source_names + view_names:
        sv_files.add(f)
        sv_files.add(f + ESuffix.UPDATE)

    mid_files = {f for f in mid_files if f not in sv_files}

    mid_names = set()

    for m in mid_files:
        t_name, t_types, t_status = None, None, None

        if m.endswith(ESuffix.UPDATE):
            t_name = m[:-len(ESuffix.UPDATE)]
            t_status = TableStatus.UPDATED
        else:
            t_name = m
            t_status = TableStatus.ORIGINAL

        mid_names.add(t_name)

        for rd in relation_decls:
            if rd.name == t_name:
                t_types = rd.schema
                break

        example.tables.append(
            Table(
                name=t_name,
                types=t_types,
                base=TableBase.STATE,
                status=t_status,
                data=load_data(f'{path}/{m}{EExt.EXPT}')
            )
        )

    # add operation-based tables
    mid_names = list(mid_names)

    for name in source_names + mid_names + view_names:
        rl_insert, rl_delete = load_operation_based_data(example, name)

        t_types = None
        for t in example.tables:
            if t.name == name:
                t_types = t.types
                break

        example.tables.append(
            Table(
                name=name,
                types=t_types,
                base=TableBase.OPERATION,
                status=TableStatus.INSERTED,
                data=rl_insert
            )
        )

        example.tables.append(
            Table(
                name=name,
                types=t_types,
                base=TableBase.OPERATION,
                status=TableStatus.DELETED,
                data=rl_delete
            )
        )

        # save operation-based tables to new expected files
        if name not in view_names:
            store_data(
                f'{path}/{name}{ESuffix.SDT_INSERT}{EExt.EXPT}', rl_insert
            )
            store_data(
                f'{path}/{name}{ESuffix.SDT_DELETE}{EExt.EXPT}', rl_delete
            )

        if name not in source_names:
            store_data(
                f'{path}/{name}{ESuffix.VDT_INSERT}{EExt.EXPT}', rl_insert
            )
            store_data(
                f'{path}/{name}{ESuffix.VDT_DELETE}{EExt.EXPT}', rl_delete
            )


def load_operation_based_data(example, name):
    t_original, t_updated = None, None

    for t in example.tables:
        if t.name == name and t.is_original():
            t_original = t
            break

    for t in example.tables:
        if t.name == name and t.is_updated():
            t_updated = t
            break

    rl_insert = [row for row in t_updated.data
                 if row not in t_original.data
                 ]
    rl_delete = [row for row in t_original.data
                 if row not in t_updated.data
                 ]
    return rl_insert, rl_delete


if __name__ == '__main__':
    pass
