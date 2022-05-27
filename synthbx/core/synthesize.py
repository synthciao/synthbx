import os
import sys
import shutil
import random
from synthbx.parser.schema.parser import parse_schema
from synthbx.parser.program.parser import parse_program
from synthbx.parser.example.parser import parse_example
from synthbx.core.decompose import decompose
from synthbx.core.gcandidate import gen_get_cand
from synthbx.core.pcandidate import build_put_cand
from synthbx.core.fexample import upgrade_to_fexample
import synthbx.core.handler as handler
from synthbx.env.const import EFile, EFolder, ESynth, ESuffix, EPrefix, EExt, ESymbol
from synthbx.env.exception import SpecificationError
from synthbx.util.io import get_ext_files


# flow:
#   synthesize
#   +-- os.system (prosynth get)
#        +--- p_synthesize
#             +---- os.system (prosynth put)


def synthesize(path):
    sc_path = f'{path}/{EFolder.SCHEMA}'
    ex_path = f'{path}/{EFolder.EXAMPLE}'
    sy_path = f'{path}/{EFolder.SYNTH}'

    schema, example = parse_specification(sc_path, ex_path)

    schema_partition = schema.partition()

    ex_path_get = move_g_ex2sy(ex_path, sy_path, schema_partition, example)

    os.system(
        f'python {ESynth.PROSYNTH_PY} {ex_path_get} 0 1 /dev/null {EFile.GET}'
    )

    # write candidates & results after finishing synthesis
    # no effect on synthesis time
    if EFile.PUT in os.listdir(sy_path):
        re_path = f'{path}/{EFolder.RESULT}'

        if os.path.exists(re_path):
            shutil.rmtree(re_path)

        os.makedirs(re_path)

        for f in [EFile.CGET, EFile.GET, EFile.DGET, EFile.CPUT, EFile.PUT]:
            shutil.copy(f'{sy_path}/{f}', f'{re_path}/{f}')

        with open(f'{re_path}/{EFile.DGET}', 'r') as fr:
            prog_d_get = parse_program(fr.read())

        handler.clean_g_directives(prog_d_get, schema_partition)

        with open(f'{re_path}/{EFile.DGET}', 'w') as fw:
            fw.write(str(prog_d_get))


def p_synthesize(path):
    sc_path = f'{path}/{EFolder.SCHEMA}'
    ex_path = f'{path}/{EFolder.EXAMPLE}'
    sy_path = f'{path}/{EFolder.SYNTH}'

    schema, example = parse_specification(sc_path, ex_path)

    schema_partition = schema.partition()

    with open(f'{sy_path}/{EFile.GET}', 'r') as fr:
        prog_get = parse_program(fr.read())

    prog_d_get = decompose(prog_get)

    with open(f'{sy_path}/{EFile.DGET}', 'w') as fw:
        fw.write(str(prog_d_get))

    ex_path_put = move_and_gen_p_ex2sy(ex_path, sy_path, schema_partition)

    upgrade_to_fexample(
        example, schema_partition, prog_d_get.relation_decls, ex_path_put
    )

    prog_c_put, num_c_rules, fv = build_put_cand(
        prog_d_get, example, schema_partition
    )

    # if fv:
    #     handler.make_valid(prog_c_put, schema_partition)
    #     make_evl_fv(ex_path_put, schema_partition)

    with open(f'{sy_path}/{EFile.CPUT}', 'w') as fw:
        fw.write(str(prog_c_put))

    shutil.copy(f'{sy_path}/{EFile.CPUT}',
                f'{ex_path_put}/{ESynth.CANDIDATE_RULE_DL}')

    with open(f'{ex_path_put}/{ESynth.RULENAME_TXT}', 'w') as fw:
        for i in random.sample(list(range(num_c_rules)), num_c_rules):
            fw.write(str(i) + '\n')

    os.system(
        f'python {ESynth.PROSYNTH_PY} {ex_path_put} 0 1 /dev/null {EFile.PUT}'
    )

    with open(f'{sy_path}/{EFile.PUT}', 'r') as fr:
        prog_put = parse_program(fr.read())

    handler.clean_unused_units(prog_put)
    handler.clean_p_directives(prog_put, schema_partition)

    with open(f'{sy_path}/{EFile.PUT}', 'w') as fw:
        fw.write(str(prog_put))


def parse_specification(sc_path, ex_path):
    schema, example = None, None

    # Parse schema
    sc_file = get_ext_files(sc_path, EExt.SC)

    if not sc_file:
        raise SpecificationError(
            f'No *sc file at {sc_path}'
        )
    elif len(sc_file) > 1:
        raise SpecificationError(
            f'Too many *sc files. Please provide only one *.sc file at {sc_path}'
        )

    with open(f'{sc_path}/{sc_file[0]}', 'r') as fr:
        schema = parse_schema(fr.read())

    # Parse example
    try:
        example = parse_example(ex_path, schema)
    except:
        raise SpecificationError(f'Please provide table files at {ex_path}')

    return schema, example


def move_g_ex2sy(ex_path, sy_path, schema_partition, example):
    if os.path.exists(sy_path):
        shutil.rmtree(sy_path)

    ex_path_get = f'{sy_path}/{EFolder.GET}'

    if not os.path.exists(ex_path_get):
        os.makedirs(ex_path_get)

    # move candidates of get to ex_path_get
    gcand_path = f'{ex_path[:-len(EFolder.EXAMPLE)]}{EFolder.GCANDIDATE}'

    if os.path.exists(gcand_path) \
        and ESynth.CANDIDATE_RULE_DL in os.listdir(gcand_path) \
            and ESynth.RULENAME_TXT in os.listdir(gcand_path):
        shutil.copy(
            f'{gcand_path}/{ESynth.CANDIDATE_RULE_DL}', ex_path_get
        )
        shutil.copy(
            f'{gcand_path}/{ESynth.RULENAME_TXT}', ex_path_get
        )
    else:
        prog_c_get, num_c_rules = gen_get_cand(example, schema_partition)
        with open(f'{ex_path_get}/{ESynth.CANDIDATE_RULE_DL}', 'w') as fw:
            fw.write(str(prog_c_get))
        with open(f'{ex_path_get}/{ESynth.RULENAME_TXT}', 'w') as fw:
            # for i in random.sample(list(range(num_c_rules)), num_c_rules):
            for i in range(num_c_rules):
                fw.write(str(i) + '\n')

    shutil.copy(f'{ex_path_get}/{ESynth.CANDIDATE_RULE_DL}',
                f'{sy_path}/{EFile.CGET}')

    # move (source_update, view_update) files to ex_path_get WITH renaming
    source, view, _ = schema_partition

    for s in source:
        shutil.copy(f'{ex_path}/{s.name}{ESuffix.UPDATE}{EExt.EXPT}',
                    f'{ex_path_get}/{s.name}{EExt.FACT}')

    for v in view:
        shutil.copy(f'{ex_path}/{v.name}{ESuffix.UPDATE}{EExt.FACT}',
                    f'{ex_path_get}/{v.name}{EExt.EXPT}')

    return ex_path_get


def move_and_gen_p_ex2sy(ex_path, sy_path, schema_partition):
    ex_path_put = f'{sy_path}/{EFolder.PUT}'

    if os.path.exists(ex_path_put):
        shutil.rmtree(ex_path_put)

    os.makedirs(ex_path_put)

    source, view, _ = schema_partition

    # move (source_update.EXPT) files to ex_path_put WITH renaming to (source.FACT)
    # call SOUFFLE_EXE to evaluate dget to gen backward tables then renaming to _update
    for s in source:
        shutil.copy(f'{ex_path}/{s.name}{ESuffix.UPDATE}{EExt.EXPT}',
                    f'{ex_path_put}/{s.name}{EExt.FACT}')

    os.system(
        f'{ESynth.SOUFFLE_EXE} -w -F {ex_path_put} -D {ex_path_put} {sy_path}/{EFile.DGET}'
    )

    for f in os.listdir(ex_path_put):
        if f.endswith(EExt.FACT):
            nf = f[:-len(EExt.FACT)] + \
                ESuffix.UPDATE + EExt.EXPT
            os.rename(f'{ex_path_put}/{f}',
                      f'{ex_path_put}/{nf}')
        elif f.endswith(EExt.CSV):
            nf = f[:-len(EExt.CSV)] + \
                ESuffix.UPDATE + EExt.EXPT
            os.rename(f'{ex_path_put}/{f}',
                      f'{ex_path_put}/{nf}')

    for v in view:
        os.rename(f'{ex_path_put}/{v.name}{ESuffix.UPDATE}{EExt.EXPT}',
                  f'{ex_path_put}/{v.name}{ESuffix.UPDATE}{EExt.FACT}')

    # move (source.FACT) files to ex_path_put WITHOUT renaming
    # call SOUFFLE_EXE to evaluate dget to gen forward tables
    for s in source:
        shutil.copy(f'{ex_path}/{s.name}{EExt.FACT}',
                    f'{ex_path_put}/{s.name}{EExt.FACT}')

    os.system(
        f'{ESynth.SOUFFLE_EXE} -w -F {ex_path_put} -D {ex_path_put} {sy_path}/{EFile.DGET}'
    )

    for f in os.listdir(ex_path_put):
        if f.endswith(EExt.CSV):
            nf = f[:-len(EExt.CSV)] + EExt.EXPT
            os.rename(f'{ex_path_put}/{f}',
                      f'{ex_path_put}/{nf}')

    return ex_path_put


def make_evl_fv(ex_path_put, schema_partition):
    source, _, _ = schema_partition

    with open(f'{ex_path_put}/{EPrefix.FLAG_V}{EExt.EXPT}', 'w') as fw:
        fw.write(ESymbol.FLAG_V.replace('"', '') + '\n')

    with open(f'{ex_path_put}/{EPrefix.FLAG_R}{EExt.EXPT}', 'w') as fw:
        pass

    # for s in source:
    #     shutil.copy(f'{ex_path_put}/{s.name}{ESuffix.UPDATE}{EExt.EXPT}',
    #                 f'{ex_path_put}/{s.name}{ESuffix.EVL_UPDATE}{EExt.EXPT}')


if __name__ == '__main__':
    path = sys.argv[1]

    synthesize(path)
