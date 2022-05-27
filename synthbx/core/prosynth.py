#!/usr/bin/env python3

########################################################################################################################
# Prosynth: Provenance-Guided Synthesis of Datalog Programs
# The Ad-hoc Clause Learning Algorithm with Coprovenance Analysis and Delta Debugging-based Why Not Provenance

# Invocation: ./scripts/prosynth PROBLEM_DIR USE_COPROV USE_DELTA_WHYNOTS

# The PROBLEM_DIR folder is expected to contain:
# 1. rules.dl: Specifies the signatures of the EDB and IDB relations, and the set of candidate rules
# 			Also contains a one-place input relation named Rule(n)
# 2. ruleNames.txt: Provides the set of valid rule names, which can be used to populate the Rule.facts file
# 3. R.facts, for each input relation R other than Rule: Specifies the EDB
# 4. R.expected, for each output relation R: Specified the expected IDB
# 5. a.out: Executable produced by Souffle with -t explain enabled

# rules.dl and R.facts are expected to be a in a format recognized by Souffle

# If synthesis is successful, then it prints to stdout one subset of rules with the desired input-output behavior

########################################################################################################################


# -------------------------------------------------------------------------
# IMPORTANT:: We directly make an adaptation in the source code of PROSYNTH
# -------------------------------------------------------------------------


from synthbx.util.io import yprint, cprint
from synthbx.env.const import ESynth, EFolder, EFile
import shutil

# 1. Prelude

import json
import logging
import os
import random
import re
import subprocess
import sys
import time
import z3
import copy
import atexit

prevConstraints, currConstraints = (-1, 0)
numLoops = 0

currRuleSetLarge = set()
# currIgnoreSetLarge = set()
numWhy = 0
numWhyNot = 0

problemDirName = sys.argv[1]
setting_coprov = sys.argv[2]
setting_delta = sys.argv[3]
data_file = sys.argv[4]

progr = sys.argv[5]

scriptStartTime = time.clock_gettime(0)
mark0 = [scriptStartTime, scriptStartTime]
synthTime = [0, 0]

souffle_exec = ESynth.SOUFFLE_EXE
candidateProgFile = f'{problemDirName}/{ESynth.CANDIDATE_RULE_DL}'
ruleNameFile = f'{problemDirName}/{ESynth.RULENAME_TXT}'

cmd_args = [souffle_exec, '-w', '-t', 'explain', '-F', problemDirName,
            '-D', problemDirName, candidateProgFile]

n_get = 0

cprint(f'[+] Synthesizing {progr[:-3]}')


def printLog():
    global callsToZ3
    global callsToSouffle

    with open(data_file, 'a+') as f:
        dataLogStr = f"""{{name: '{problemDirName},
	z3: {callsToZ3}, souffle: {callsToSouffle},
	runtime: {time.clock_gettime(0) - scriptStartTime},
	setting_delta: {setting_delta}}}"""
        print(dataLogStr, file=f)


def printTimer():
    cprint(f'[+] Exit Synthesizing {progr[:-3]}')
    print(
        f"SynthTime ({progr}): {synthTime}"
    )
    print(
        f"Total runtime ({progr}): {str(time.clock_gettime(0) - scriptStartTime)}"
    )
    if progr == EFile.GET:
        print(
            f"Number of found gets ({progr}):{n_get}"
        )


atexit.register(printTimer)

logging.basicConfig(
    level=logging.INFO,
    format=" %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
    datefmt="%H:%M:%S"
)

# 1a. Load the set of rules and IDB relations

allRuleNames = {name.strip() for name in open(ruleNameFile) if name.strip()}
allRuleNames = {name: z3.Bool(name) for name in allRuleNames}


def loadRelation(filename):
    ans = {line.strip() for line in open(filename) if line.strip()}
    ans = {tuple(line.split('\t')) for line in ans}
    return ans


idbRelationsExpected = {name for name in os.listdir(
    problemDirName) if name.endswith('.expected')}
idbRelationsExpected = {name[:-len('.expected')]
                        for name in idbRelationsExpected}
idbRelationsExpected = {name: loadRelation(
    problemDirName + '/' + name + '.expected') for name in idbRelationsExpected}

outputSet = set()
with open(candidateProgFile, 'r') as fr:
    for line in fr:
        if re.search(r'\.output (\w+)', line.strip()):
            outputSet.add(line.strip()[len('.output '):])

outputSet |= idbRelationsExpected.keys()

# 1b. Initialize the constraint solver

solver = z3.Solver()
# solver.add(z3.And([z3.BoolVal(True)] + [allRuleNames[str(r)] for r in range(0,7) ]))


def satisfyingRuleSet(default):
    global callsToZ3
    global prevConstraints
    global currConstraints
    global numLoops
    # Determines the set of rules that should be switched on to satisfy the current set of constraints
    # Includes presently unconstrained rules iff default is true

    currTime = time.clock_gettime(0)
    prevConstraints = currConstraints
    if solver.check() == z3.unsat or time.clock_gettime(0) - scriptStartTime > 3600:
        printLog()
        print('Z3 reports error in generating a model. Problem unsat.')
        sys.exit(1)
    m = solver.model()
    # logging.info("z3 model generated")
    callsToZ3 += 1
    return {ruleName for ruleName, ruleVar in allRuleNames.items() if m[ruleVar] in [True, None]}


def doSanity():
    global prevConstraints
    global currConstraints
    try:
        # yprint(f'doSanity: solver = {solver}')
        solver.push()
        if solver.check() == z3.unsat:
            printLog()
            print('Z3 reports error in generating a model. Problem unsat.')
            sys.exit(1)
        solver.model()
        solver.pop()
        return True
    except z3.Z3Exception:
        return False


doSanity()

# 1c. Helper method to create Rule.facts file


def printRuleEDB(ruleSet):
    with open(problemDirName + '/Rule.facts', 'w') as outFile:
        for name in ruleSet:
            print(name, file=outFile)

########################################################################################################################
# 3. Repeatedly add constraints until a satisfying assignment is found


iterationNum = 0
callsToZ3 = 0
callsToSouffle = 0

list_solutions = []
list_visited_cands = []
max_n_cands = 0
firstFlag = True
nEmptyRMinus = 0

while True:

    currRuleSetLarge = satisfyingRuleSet(True)
    if firstFlag:
        max_n_cands = 2 ** len(currRuleSetLarge)
        # firstFlag = False

    if len(list_visited_cands) == max_n_cands:
        print('Exhausted! No solutions!')
        exit(0)

    if sorted(currRuleSetLarge) in list_visited_cands:
        added = z3.Not(z3.And([z3.BoolVal(True)] +
                              [allRuleNames[ruleName] for ruleName in sorted(currRuleSetLarge)]))
        solver.add(added)
        try:
            doSanity()
            continue
        except:
            print(
                'Z3 reports error in generating a model. Problem unsat.')
            quit()

    list_visited_cands.append(sorted(currRuleSetLarge))

    solved = True

    iterationNum += 1
    yprint(f'--------Iteration {iterationNum} --------')
    # yprint(f'rPlus: {sorted(currRuleSetLarge)}')
    # yprint(f'rMinus: {sorted(set(allRuleNames) - currRuleSetLarge)}')
    yprint(f"""Calls to z3: {callsToZ3}, Calls to Souffle: {callsToSouffle}
Culumative Number of Constraints - - Why: {numWhy}, Whynot: {str(numWhyNot)}
""")

    printRuleEDB(currRuleSetLarge)
    logging.info("rPlus printed to Rule.facts")

    currTime = time.clock_gettime(0)
    os.system(f'rm -rf {problemDirName}/*.csv 2> /dev/null')

    with subprocess.Popen(
            args=cmd_args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            universal_newlines=True) as souffleProc:

        ################################################################################################################
        # 3a. Set up communication with Souffle

        logging.info("Souffle invoked")
        callsToSouffle += 1
        while souffleProc.stdout.readline().strip() != '###':
            pass
        while souffleProc.stdout.readline().strip() != '###':
            pass

        def execSouffleCmd(cmd):
            print(cmd, file=souffleProc.stdin)
            souffleProc.stdin.flush()

            response = [souffleProc.stdout.readline().strip()]
            if response[-1] == '':
                # logging.info('Error reading 1')
                # doesn't deal with underlying problem, just passes error through and skips question
                return "error reading"
                # return execSouffleCmd(cmd)
            while response[-1] != '###':
                response.append(souffleProc.stdout.readline().strip())
            response = response[:-1]
            ans = '\n'.join(response)
            # logging.info('souffle to prosynth: ' + ans)
            return ans

        execSouffleCmd('format json')
        execSouffleCmd('setdepth 200000')

        ################################################################################################################
        # 3b. Functions to print and parse tuples in the Souffle executable format

        def printSouffleString(relName, t):
            t = tuple('"{}"'.format(x) for x in t)
            t = ', '.join(t)
            return '{}({})'.format(relName, t)

        def parseSouffleString(string):
            xs = string.split('(')
            assert(len(xs) == 2)
            relName = xs[0].strip()
            xs = xs[1]
            xs = xs.split(')')[0].strip()
            xs = [x.strip() for x in xs.split(',')]
            # for x in xs:
            # assert(x.startswith('"') and x.endswith('"'))
            xs = tuple([x[1:-1].strip() for x in xs])
            return (relName, xs)

        ################################################################################################################
        # 3b. Functions to query provenance
        #		The provenance object returned by Souffle is a list of hypothesis provenance objects H*, each of which is
        #		of the form:
        #		1. { 'axiom': T }, for a tuple T, or
        #		2. { 'premises': T, 'children': H* }, for a tuple T, and a list of hypothesis provenance objects, H*

        def cleanProvenanceJson(provenance):
            orgProvenance = provenance

            def cleanProvenanceJsonInt(p):
                if type(p) is dict:
                    p = {key: value
                         for key, value in p.items() if key != 'rules'}
                    p = {key: value
                         for key, value in p.items() if key != 'rule-number'}
                    p = {key: cleanProvenanceJsonInt(value)
                         for key, value in p.items()}
                elif type(p) is list:
                    p = [cleanProvenanceJsonInt(value) for value in p]
                return p
            provenance = cleanProvenanceJsonInt(provenance)
            assert(len(provenance) == 1)
            assert('proof' in provenance)
            if 'children' not in provenance['proof']:
                # yprint(orgProvenance)
                logging.info('Error reading 2')
                return "error reading"
            provenance = provenance['proof']['children']
            return provenance

        def squashDesirableConclusions(provenance):
            if type(provenance) is dict:
                if 'premises' in provenance:
                    premiseRel, premiseT = parseSouffleString(
                        provenance['premises'])
                    if premiseRel in idbRelationsExpected and premiseT in idbRelationsExpected[premiseRel]:
                        provenance = {'axiom': provenance['premises']}
                    else:
                        provenance = {key: squashDesirableConclusions(
                            value) for key, value in provenance.items()}
            elif type(provenance) is list:
                provenance = [squashDesirableConclusions(
                    elem) for elem in provenance]
            return provenance

        def collectIntermediateConclusions(provenance):
            if type(provenance) is dict:
                premises = {premise for key, value in provenance.items(
                ) for premise in collectIntermediateConclusions(value)}
                if 'premises' in provenance:
                    premises = premises | {
                        parseSouffleString(provenance['premises'])}
                return premises
            elif type(provenance) is list:
                return {premise for elem in provenance for premise in collectIntermediateConclusions(elem)}
            else:
                return set()

        def collectRules(provenance):
            if type(provenance) is dict:
                rules = {rule for key, value in provenance.items()
                         for rule in collectRules(value)}
                if 'axiom' in provenance and provenance['axiom'].startswith('Rule'):
                    rules = rules | {provenance['axiom'][len('Rule') + 1:-1]}
                return rules
            elif type(provenance) is list:
                rules = {
                    rule for elem in provenance for rule in collectRules(elem)}
                return rules
            else:
                return set()

        def getProvenance(relName, t):
            provenance1 = execSouffleCmd(
                'explain ' + printSouffleString(relName, t))
            if provenance1 == "error reading":
                # logging.info('Error reading 3')
                return "error reading"
            provenance2 = json.loads(provenance1)
            provenance3 = cleanProvenanceJson(provenance2)
            if provenance3 == "error reading":
                # logging.info('Error reading 4')
                return "error reading"
            provenance4 = squashDesirableConclusions(provenance3)
            # if provenance3 != provenance4:
            #     #logging.info(provenance3)
            #     #logging.info(provenance4)
            return provenance4

        def why(relName, t):
            # global currIgnoreSetLarge

            provenance = getProvenance(relName, t)
            if provenance == "error reading":
                # logging.info('Error reading 5')
                return ("error reading", False)
            # for hypRelName, hypT in collectIntermediateConclusions(provenance):
            #	if hypRelName in idbRelationsExpected and hypT not in idbRelationsExpected[hypRelName]:
            #		logging.debug('Tuple {} depends on absurd hypothesis {}'.format((relName, t), (hypRelName, hypT)))
            #		return None
            rules = collectRules(provenance)
            # logging.info('Tuple {} depends on rules {}'.format((relName, t), sorted(rules)))

            ans = z3.BoolVal(True)
            currentRuleList = []
            for ruleName in rules:
                currentRuleList.append(ruleName)

            currentRuleList = sorted(currentRuleList)

            # currIgnoreSetLarge |= set(currentRuleList)

            if not currentRuleList:
                return (False, ans)

            outputStr = "WHY constraint added: [not (" + \
                " and ".join([str(ruleName) for ruleName in currentRuleList]) + \
                ")] because " + str(relName) + str(t) + \
                " is undesirable and produced"
            logging.info(outputStr)

            ans = z3.And([z3.BoolVal(True)] + [allRuleNames[ruleName]
                         for ruleName in currentRuleList])
            # for ruleName in (currentRuleList):
            # 	ans = z3.And(ans, allRuleNames[ruleName])
            # logging.info('adding constraint: not [%s]' % ' and '.join(map(str, sorted(currentRuleList))))

            return (True, ans)

        def breakIntoPieces(l, numPieces):
            avg = len(l) / float(numPieces)
            out = []
            last = 0.0

            while last < len(l):
                out.append(l[int(last):int(last+avg)])
                last += avg

            return out

        def whyNotDelta(relName, t, currRuleSetLarge):
            global callsToSouffle

            divisions = 2

            rMinus = set(allRuleNames) - currRuleSetLarge
            rPlus = currRuleSetLarge

            if not rMinus:
                rMinus = currRuleSetLarge
                rPlus = set()

            code = list(rMinus)
            # logging.info(relName + '(' + str(t) + ')')

            while True:
                # logging.info(divisions)
                for codeChunk in breakIntoPieces(code, divisions):
                    currRMinus = rMinus - set(codeChunk)
                    currRPlus = rPlus.union(set(codeChunk))

                    printRuleEDB(currRPlus)
                    # #logging.info("currRPlus printed to Rule.facts [within whyNotDelta]")
                    subproc = subprocess.Popen(
                        [souffle_exec, '-w', '-t', 'explain', '-F',
                            problemDirName, '-D', problemDirName, candidateProgFile],
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        universal_newlines=True
                    )
                    # logging.info("Souffle invoked [within whyNotDelta]")
                    callsToSouffle += 1
                    subproc.communicate()
                    relProduced = loadRelation(
                        problemDirName + '/' + relName + '.csv')
                    bugProduced = True
                    for tt in relProduced:
                        if tt == t:
                            bugProduced = False

                    if bugProduced:
                        rMinus = currRMinus
                        rPlus = currRPlus

                if divisions == len(code):
                    break
                divisions = min(len(code), divisions*2)
                if divisions == 0:
                    break

            outputStr = "WHYNOT constraint added: [" + \
                " or ".join([str(ruleName) for ruleName in list(rMinus)]) + \
                "] because " + str(relName) + str(t) + \
                " is desirable and unproduced"
            logging.info(outputStr)

            return sorted(rMinus)

        def whyNot():
            ans = z3.BoolVal(False)

            outputStr = "WHYNOT constraint added: ["
            for ruleName in allRuleNames:
                if ruleName not in currRuleSetLarge:
                    ans = z3.Or(ans, allRuleNames[ruleName])
                    outputStr += str(ruleName) + " or "
            outputStr = outputStr[:len(outputStr)-4]
            outputStr += "] because "
            outputStr += "there exists some tuple that is desirable and unproduced"
            logging.info(outputStr)

            return ans

        ################################################################################################################
        # 3c. Iterate over all tuples
        # if setting_coprov == "1":
        #     pass
            # printRuleEDB(currRuleSetLarge)
            # #logging.info("rPlus printed to Rule.facts")
            # myProc = subprocess.Popen(
            # 	[problemDirName + '/souffle_notexists.small.out', '-F', problemDirName, '-D', problemDirName])
            # #logging.info("Souffle_notexists invoked")
            # callsToSouffle += 1
            # myProc.communicate()
            # for relName in idbRelationsExpected:
            # 	tE = idbRelationsExpected[relName]

            # 	notExistsData = {line.strip() for line in open(problemDirName + '/' + relName + '_notexists.csv') if line.strip()}
            # 	notExistsData = {tuple(line.split('\t')) for line in notExistsData}

            # 	coprov = dict()
            # 	for rel in notExistsData:
            # 		coprov[rel[:len(rel)-1]] = set()

            # 	for rel in notExistsData:
            # 		coprov[rel[:len(rel)-1]].add(rel[len(rel) - 1])

            # 	for cp in coprov.keys():
            # 		coprov[cp] = currRuleSetLarge - coprov[cp]

            # 	neededRules = set()
            # 	for t in tE:
            # 		if t in coprov:
            # 			# if coprov[t] != None:
            # 			#    #logging.info(str(t) + " has coprov " + str(coprov[t]))
            # 			neededRules = neededRules.union(set(coprov[t]))

            # 	if len(neededRules) != 0:
            # 		smallRMinus = set(allRuleNames) - currRuleSetLarge

            # 		outputStr = "COPROV constraint added: ("

            # 		allNotRMinus = z3.BoolVal(True)
            # 		for ruleName in smallRMinus:
            # 			allNotRMinus = z3.And(allNotRMinus, z3.Not(allRuleNames[ruleName]))
            # 			outputStr += "not " + str(ruleName) + " and "
            # 		allNeededRules = z3.BoolVal(True)

            # 		outputStr = outputStr[:len(outputStr)-5]

            # 		outputStr += ") => ("

            # 		for ruleName in neededRules:
            # 			allNeededRules = z3.And(allNeededRules, allRuleNames[ruleName])
            # 			outputStr += str(ruleName) + " and "

            # 		outputStr = outputStr[:len(outputStr)-5]
            # 		outputStr += ")"
            # 		#logging.info(outputStr)

            # 		solver.add(z3.Implies(allNotRMinus, allNeededRules))
            # 		currConstraints = currConstraints + 1

        whyNotFlag = True
        whyFlag = False

        for relName in idbRelationsExpected:
            relProduced = loadRelation(problemDirName + '/' + relName + '.csv')

            # 3c(i) Tuples which are expected and produced
            # We do not have anything to learn from these tuples
            # for t in relProduced & idbRelationsExpected[relName]:
            # logging.info('Solution produces desirable tuple: ' + printSouffleString(relName, t))

            # 3c(ii) Tuples which are unexpected but still produced
            # Here, we ask the question: ``Why was this tuple produced?''

            newWhys = 0
            currUndesiredTuples = list(
                relProduced - idbRelationsExpected[relName])

            random.shuffle(currUndesiredTuples)
            for i, t in enumerate(currUndesiredTuples):
                solved = False
                whyRelT = why(relName, t)
                if whyRelT[0] == "error reading":
                    logging.info(f"\n{relName}{t}: Error reading 6")
                    break
                elif whyRelT[1] != None:
                    if whyRelT[0] == True:
                        if hash(whyRelT[1]) not in [hash(c) for c in solver.assertions()]:
                            solver.add(z3.Not(whyRelT[1]))
                            currConstraints += 1
                            numWhy += 1
                            whyFlag = True
                            doSanity()
                if i > 20:
                    break

            # 3c(iii) Tuples which were expected but not produced
            # Here, we ask the question: ``Why was this tuple not produced?''
        if firstFlag & whyFlag:
            firstFlag = False
            continue

        for relName in idbRelationsExpected:
            relProduced = loadRelation(problemDirName + '/' + relName + '.csv')

            if whyNotFlag:
                unproducedDesirable = False
                oldCRSL = copy.deepcopy(currRuleSetLarge)

                for t in (idbRelationsExpected[relName] - relProduced):
                    currRuleSetLarge = copy.deepcopy(oldCRSL)
                    solved = False

                    whyNotRelT = z3.BoolVal(False)

                    if setting_delta == "1":
                        smallRMinus = whyNotDelta(relName, t, currRuleSetLarge)
                        if sorted(smallRMinus) == sorted(currRuleSetLarge):
                            whyNotFlag = False
                            added = z3.Not(z3.And([z3.BoolVal(True)] +
                                           [allRuleNames[ruleName] for ruleName in sorted(currRuleSetLarge)]))
                            whyNotRelT = added
                        elif not smallRMinus:
                            nEmptyRMinus += 1
                            if nEmptyRMinus < 10:
                                whyNotFlag = False
                                added = z3.Not(z3.And([z3.BoolVal(True)] +
                                                      [allRuleNames[ruleName] for ruleName in sorted(currRuleSetLarge)]))
                                whyNotRelT = added
                        else:
                            for ruleName in smallRMinus:
                                whyNotRelT = z3.Or(
                                    whyNotRelT, allRuleNames[ruleName])
                    else:
                        whyNotRelT = whyNot()

                    if whyNotRelT != None:
                        solver.add(whyNotRelT)
                        currConstraints += 1
                        numWhyNot += 1
                        unproducedDesirable = True
                        try:
                            doSanity()
                        except:
                            dataLogStr = "{" + f"name: '{problemDirName}', " + \
                                f"z3: {callsToZ3}, souffle: {callsToSouffle}, " + \
                                f"runtime: {time.clock_gettime(0) - scriptStartTime}, " + \
                                f"setting_delta: {setting_delta}" + "}"
                            with open(data_file, 'a+') as f:
                                print(dataLogStr, file=f)
                            print(
                                'Z3 reports error in generating a model. Problem unsat.')
                            quit()

                    break

                if not whyNotFlag:
                    break

        ################################################################################################################
        # 3d. Find useful rules

        if solved:
            printLog()
            ans = set()

            if not firstFlag:
                for relName in outputSet:
                    if relName in idbRelationsExpected:
                        for t in idbRelationsExpected[relName]:
                            for ruleName in collectRules(getProvenance(relName, t)):
                                ans.add(ruleName)
            else:
                ans = set(currRuleSetLarge)

            s_ans = ans
            if sorted(s_ans) in list_solutions:
                continue
            list_solutions += [sorted(s_ans)]

            p_ans = sorted([int(i) for i in ans])
            ans = r'Rule\(({})\)'.format('|'.join([str(i) for i in p_ans]))
            logging.info(ans)
            ans = re.compile(ans)

            # mod
            with open(candidateProgFile, 'r') as fr:
                with open(problemDirName + '/../' + progr, 'w') as fw:
                    wr = []
                    for line in fr:
                        line = line.replace('\n', '')
                        if line.startswith('.'):
                            if 'Rule' not in line:
                                wr += [line]
                        else:
                            pat1 = r',[ \t]*Rule\(\d+\)[ \t]*\.'
                            pat2 = r' :- Rule\(\d+\).'
                            if not re.findall(pat1, line) and not re.findall(pat2, line):
                                wr += [line]
                            elif ans.search(line):
                                if re.findall(pat1, line):
                                    wr += [re.sub(pat1, '.', line)]
                                else:
                                    wr += [re.sub(pat2, '.', line)]
                    fw.write('\n'.join(wr))

            if progr == EFile.GET:
                n_get += 1
                mark1 = time.clock_gettime(0)
                synthTime[0] += (mark1 - mark0[0])
                mark0[0] = mark1
                path = f'{problemDirName}/../..'
                try:
                    from synthbx.core.synthesize import p_synthesize
                    p_synthesize(path)
                except FileNotFoundError:
                    if EFile.PUT not in os.listdir(f'{path}/{EFolder.SYNTH}'):
                        yprint(f'No put could pair with get {str(s_ans)}')

                    mark2 = time.clock_gettime(0)
                    synthTime[1] += mark2 - mark1
                    mark0[0] = mark2

                    added = z3.Or([z3.BoolVal(False)] +
                                  [z3.Not(allRuleNames[r]) for r in s_ans])
                    if hash(added) not in [hash(c) for c in solver.assertions()]:
                        currConstraints += 1
                        solver.add(added)
                        doSanity()
                    continue
            elif progr == EFile.PUT:
                mark1 = time.clock_gettime(0)
                synthTime[1] += mark1 - mark0[1]
                mark0[1] = mark1
            else:
                raise Exception("Unknown progr")

            # logging.info(
                # f'Calls to Z3: {callsToZ3}, Calls to Souffle: {callsToSouffle}')
            break
        else:
            firstFlag = False
