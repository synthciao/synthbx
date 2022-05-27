# SynthBX: synthesizing well-behaved bidirectional programs on relations

## Project structure

```
<synthbx-proj>
|
+--- benchmarks
|    +-- data : specifications (schema + example)
|    +-- results : candidates, solutions, statistic logs
|
+--- benchmarks.stat.bak : a backup of benchmarking
|    +-- data : specifications (schema + example)
|    +-- results : candidates, solutions, statistic logs
|
+--- synthbx
|    +-- ast
|    +-- core
|    |   +- decompose.py
|    |   +- fexample.py
|    |   +- gcandidate.py
|    |   +- handler.py
|    |   +- pcandidate.py
|    |   +- prosynth.py : an adaptation of ProSynth
|    |   +- synthesize.py
|    +-- env : consts, exceptions
|    +-- parser : example, schema, program
|    +-- souffle : binaries of an adaptation of Soufflé
|    +-- util
|
+--- stat.sh : for benchmarking
```

## Environments
- Python 3
- Bash/Zsh
- Adaptations of [ProSynth](https://github.com/petablox/popl2020-artifact) and [Soufflé](https://github.com/souffle-lang/souffle)

## Adaptations

### ProSynth
- Adaptation is provided at `<synthbx-proj>/synthbx/core/prosynth.py`

### Soufflé

> Build from source
- Clone Soufflé v2.1 and modify `<souffle-proj>/src/include/souffle/provenance/Explain.h`

- Modify the similar file if cloning another version

- Original function
	```
	void printPrompt(const std::string& prompt) override {
		if (isatty(fileno(stdin)) == 0) {
			return;
		}
		std::cout << prompt;
	}
	```

- Updated function
	```
	void printPrompt(const std::string& prompt) override {
		if (isatty(fileno(stdin)) == 0) {
			std::cout << "###" << std::endl << std::flush;
			return;
		}
		std::cout << prompt << std::endl << "###" << std::endl << std::flush;
		}
	```
- [Build Soufflé](https://souffle-lang.github.io/build)

- Move binaries from `<souffle-proj>` to `<synthbx-proj>`
	```
	cp <souffle-proj>/src/souffle{,-compile,-config,-profile} \
		<synthbx-proj>/synthbx/souffle/
	```

> Binaries
  - Pre-compiled binaries for MacOS 12.4 are provided at `<synthbx-proj>/synthbx/souffle/`
  - No test for another version of MacOS and Linux
  - Please compile as above if the binaries could not be used

## Execution

- `cd <synthbx-proj>`
- `export PYTHONPATH=$(pwd)`
- `python synthbx -s <path-to-SPEC>`

	eg.
	```
	python synthbx -s benchmarks/data/hcraft/tokyoac
	```

- See the result at `<path-to-SPEC>/result`
  - cget.dl : candidate of <em>get</em>
  - get.dl : solution of <em>get</em>
  - `dget.dl` : decomposed version of <em>get</em>
  - cput.dl : candidate of <em>put</em>
  - `put.dl` : solution of <em>put</em>

## Run benchmarks

- `./stat.sh <benchmark-folder> <positive-number-of-runs>`
- `<positive-number-of-runs>` = 32 by default
  
	eg.
	```
	./stat.sh benchmarks/data/hcraft/tokyoac
	```


## For another synthesis tasks
- Prepare 01 specification folder, called `SPEC`, including
  - 01 <em>required</em> folder `schema` containing file `SPEC.sc`
  - 01 <em>required</em> folder `example` containing files `source.facts`, `source_update.expected`, `view.facts` where `source` and `view` exist in `SPEC.sc`
  - 01 <em>optional</em> folder `gcandidate` containing 2 files `rules.small.dl` and `ruleNames.small.txt` expressing candidates of <em>get</em>
      - `rules.small.dl`: Souffle program used for the rule selection in ProSynth
      - `ruleNames.small.txt`: names of rules

- Synthesize by executing:
	
	```
	python synthbx -s <path-to-SPEC>
	````

> Preparing schema
```
*<name-of-sourceX>(type_sX_0, type_sX_1, ..., type_sX_nX)
+<name-of-inventY>(type_iY_0, type_iY_1, ..., type_iY_nY)
<name-of-viewZ>(type_vZ_0, type_vZ_1, ..., type_vZ_nZ)
```
> Preparing <em>required</em> example
- Each line in `*.facts` and `*.expected` is `TAB` delimited
- Replace empty field by strings `_null_`

> Preparing <em>optional</em> candidates
- Write a file named `rules.small.dl` with declarations of types and relations according to file `SPEC.sc`
- Add the following declaration and directive:
	```
	.decl Rule(v0: number)
	.input Rule
	```
- Write candidate rules and end their bodies by `Rule(n)` for n is a concrete number. Each rule should be assigned with a unique number of `Rule`
- Write a file named `ruleNames.small.txt` containing all assigned numbers of `Rule`
