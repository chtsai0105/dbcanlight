[![Build](https://img.shields.io/github/actions/workflow/status/chtsai0105/dbcanlight/python-versions.yml?branch=main&logo=github)](https://github.com/chtsai0105/dbcanlight/actions/workflows/python-versions.yml)
[![Bioconda](https://img.shields.io/conda/v/bioconda/dbcanlight?logo=anaconda&color=orange)][Bioconda]
[![Python](https://img.shields.io/badge/python-3.7_%7C_3.8_%7C_3.9_%7C_3.10_%7C_3.11_%7C_3.12-blue?logo=python)](https://github.com/chtsai0105/dbcanlight/actions/workflows/python-versions.yml)
[![License](https://img.shields.io/github/license/chtsai0105/dbcanlight?label=license)](https://github.com/chtsai0105/dbcanlight/blob/master/LICENSE)

# dbcanlight

A lightweight rewrite of [run_dbcan] for better multithread performance. The previous version of run_dbcan uses hmmscan, which is
reported to be way slow compared to hmmsearch although they're doing the same compute. It is highly recommended to [use hmmsearch
for searching a large sequence database against a profile database][hmmscan_vs_hmmsearch] and in the latest update [run_dbcan]
finally switch to use hmmsearch. To further improve the performance and the code readability, [pyhmmer], a Cython bindings to
HMMER3, was used instead of the cli HMMER3 suite to run hmmsearch. My implementation also address another issue possessed in the
original [run_dbcan] - under-performance and cpu over-spawning issue when the input contains over million of sequences. dbcanlight
can run faster and with much lower memory consumption than the original implementation.

The main program `dbcanlight` comprises 3 modules - `download`, `search` and `conclude`. The download module help to download the
required databases from dbcan website. (Not implemented yet!) The search module searches against protein HMM, substrate HMM or
diamond databases and reports the hits separately. The conclude module gathers all the results made by each module and reports a
brief overview.

In addition to the main program, another 2 programs are also included to help parse the hmmsearch outputs if users have done their
own searches by cli HMMER3 suite. The `dbcanlight-hmmparse` is a rewrite of `hmmscan_parser.py` in `run_dbcan` which can be used
to filter the overlapped hits and convert a domtblout format file output from hmmer3 suite into a dbcan-10-column format. The
`dbcanlight-subparser` takes the dbcan-formatted substrate output and map against the [substrate conversion table][dbcansub]. Here
I slightly re-organize the output - the original [run_dbcan] output the same substrate several times for a gene that hits multiple
profiles with the same substrate; in dbcanlight we only report it once.

The output of dbcanlight is fully compatible with the original [run_dbcan]. However, dbcanlight only re-implemented the core
features of [run_dbcan], that is searching for CAZyme and substrate matches by hmmer/diamond/dbcansub. Submodules like signalP,
CGCFinder, etc. are not included. If you tend to use these features, please use the original version of [run_dbcan].

## Usage

Before the first execution, please make sure the [required data](#required_data) have already been downloaded before use. (will be
done by the `download` module in the future update)

To test run on the example files, please cd into the folder **example**.

```
cd example
```

A protein fasta file **example.faa** can be found under the folder. In additional, there is a domtblout output
**hmmsearch_output**, which is generated from **example.faa** using cli hmmsearch against dbcan substrate database.

### Search

Search module contains 3 modes - `cazyme`, `sub` and `diamond`.

Run the dbcan cazyme search with 8 cpus:

```
dbcanlight search -i example.faa -m cazyme -t 8
```

The results will be output with the file name "**cazymes.tsv**" under `cazyme` mode, "**substrates.tsv**" under `sub` mode and
"**diamond.tsv**" under `diamond` mode. By default it is output to the current folder (`.`). Users can output to a specific
location by specifying `-o/--output [output directory]`.

```
dbcanlight search -i example.faa -o output -m cazyme -t 8
```

All the methods report the predictions with certain threshold. dbcanlight uses 1e-15 for hmm-based analysis (cazyme/sub) and
1e-102 for diamond for the evalue and 0.35 for coverage cutoff, as confirmed empirically in [dbcan's paper][dbcan2_paper]. Users
can adjust these cutoff by specifying `-e/--evalue` and `-c/--coverage`. Here we run the `diamond` mode with adjusted evalue and
coverage:

```
dbcanlight search -i example.faa -o output -m diamond -e 1e-150 -c 0.5 -t 8
```

When searching within a very large sequence database, such as one containing over 1,000,000 sequences, the keep adding up hits
sometimes might exceed the memory limit. To avoid this issue, dbcanlight performs search with 100,000 sequence per batch by
default. Users are allowed to adjust the blocksize to fit their own needs.

The example below demonstrates searching for substrates with a block containing 10,000 sequences on each iteration, repeating the
process until all the sequences have been processed.

```
dbcanlight search -i example.faa -o output -m sub -b 10000 -t 8
```

Please use `dbcanlight search --help` to see more details.

### Conclude

After generate all the results by different tools, conclude module can be used to help making an overview table and summarizing
the predictions made by all the tools.

```
dbcanlight conclude output
```

Note that you need to have results from at least 2 tools. The conclude module will cast an error if you have only 1 results.

### hmmsearch and substrate parser

The script `dbcanlight-hmmparser` can be used to process the domtblout format output came from cli version hmmsearch. It uses the
Biopython SearchIO module to read the hmmer3 domtblout. If a gene have multiple hits and these hits are overlapped over 50%, only
the hit with the lowest evalue will be reported. The output will be a 10-column tsv. (hmm_name, hmm_length, gene_name,
gene_length, evalue, hmm_from, hmm_to, gene_from, gene_to, coverage)

A file **hmmsearch_output** under **example** was from cli hmmsearch with `--domtblout` enabled. We can filter the results and
converted to the 10-column tsv by:

```
dbcanlight-hmmparser -i hmmsearch_output -o hmmsearch_output_parsed.tsv
```

Please use `dbcanlight-hmmparser --help` to see more details.

The script `dbcanlight-subparser` is used to map HMM profiles to its potential substrates.

```
dbcanlight-hmmparser -i hmmsearch_output_parsed.tsv -o substrate_from_hmmsearch_output.tsv
```

Use `dbcanlight-subparser --help` to see more details.

## Requirements

- Python >= 3.7
- [Biopython]
- [pyhmmer]

## Install

dbcanlight is available on [Bioconda], you can install it through:

```
conda install -c bioconda dbcanlight
```

Note that the bioconda dependencies require python to be >= 3.9 when installing via conda.

Alternatively, you can build from the source code. Download the source code from the [latest
release](https://github.com/chtsai0105/dbcanlight/releases/latest) and decompress it. To avoid messing around the base
environment, try to create a conda/virturl env and install it inside it.

Install the package through pip

```
cd dbcanlight-1.0.2
pip install .
```

<a name="required_data"></a>Please also download the required hmm profile databases and the substrate mapping table with the
following cmds:

```
mkdir -p $HOME/.dbcanlight && \
curl -o $HOME/.dbcanlight/substrate_mapping.tsv https://bcb.unl.edu/dbCAN2/download/Databases/fam-substrate-mapping-08252022.tsv && \
curl -o $HOME/.dbcanlight/cazyme.hmm https://bcb.unl.edu/dbCAN2/download/Databases/V12/dbCAN-HMMdb-V12.txt && \
curl -o $HOME/.dbcanlight/substrate.hmm https://bcb.unl.edu/dbCAN2/download/Databases/dbCAN_sub.hmm
curl -o $HOME/.dbcanlight/cazydb.fa https://bcb.unl.edu/dbCAN2/download/Databases/CAZyDB.07262023.fa
```

Next, build the diamond database by the following cmd:

```
diamond makedb --in ~/.dbcanlight/cazydb.fa --db ~/.dbcanlight/cazydb.dmnd -t 4
```

### Install additional package for developing (developer only)

Developer should clone the GitHub project directly instead of downloading from the releases. Some of the files for developing
purpose only are not included in the releases.

In addition to the requirements listed above, the following packages are required for developing environment.

- [pre-commit] >= 3.4.0
- [pytest] >= 8.0.0
- [pytest-cov] >= 5.0.0

Developer can install it with conda by:

```
conda install pre-commit>=3.4.0 pytest>=8.0.0 pytest-cov>=5.0.0
```

For convenience we also provide the additional conda env file. Please use the `dev_additional_packages.yml` to install the additional packages.

```
conda env update -f dev_additional_packages.yml
```

## Benchmark

The performance test was done on a protein fasta predicted by Prodigal with 9,360 sequences (3.0 MB in size). 3 rounds of test
were run on cazyme detection mode (`--tools hmmer` in run_dbcan and `-m cazyme` in dbcanlight) and substrate detection
mode(`--tools dbcansub` in run_dbcan and `-m sub` in dbcanlight). All tests were run on the same machine with 8 cpus.

![performance](misc/performance_comparison.svg)

The memory usage test was done on a protein fasta predicted by Prodigal with 471,613 sequences. (168 MB in size). 3 rounds of test
were done on cazyme detection mode (`-m cazyme` in dbcanlight) with different blocksizes. All tests were run on the same machine
with 8 cpus. The result shows that process the sequences in batch is able to limit the memory consumption but do not affect the
speed.

![Memory](misc/performance_blocksize.svg)

## Notes

Although hmmscan and hmmsearch are doing the same thing, the results may differ a bit since the evalue would be affected by the
size of the database.

[run_dbcan]: https://github.com/linnabrown/run_dbcan
[hmmscan_vs_hmmsearch]: http://cryptogenomicon.org/hmmscan-vs-hmmsearch-speed-the-numerology.html
[pyhmmer]: https://pyhmmer.readthedocs.io/en/stable/index.html
[dbcansub]: http://bcb.unl.edu/dbCAN2/download/Databases/fam-substrate-mapping-08252022.tsv
[dbcan2_paper]: https://doi.org/10.1093/nar/gky418
[Biopython]: https://biopython.org/
[Bioconda]: https://anaconda.org/bioconda/dbcanlight
[pytest]: https://docs.pytest.org/en/stable/
[pytest-cov]: https://pytest-cov.readthedocs.io/en/stable/
