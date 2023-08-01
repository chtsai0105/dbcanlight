# dbcanLight
A lightweight rewrite of [run_dbcan] for better multithreading performance.
The current version of run_dbcan is using hmmscan which is reported to be way slow compared to hmmsearch although they're doing the same compute.
It is highly recommended to [use hmmsearch for searching a large sequence database against a profile database][hmmscan_vs_hmmsearch].
To improve the performance and the code readability, I use [pyhmmer], a HMMER3 implementation on python3, instead of the conventional HMMER3 suite to run hmmsearch.

In addition to the main script `dbcanlight.py`, I also provide another 2 scripts to help parse the hmmsearch outputs.
The `hmmsearch_parser.py` is a rewrite of `hmmscan_parser.py` in `run_dbcan` which can be used to filter the overlapped hits
and convert the domtblout format of hmmsearch into the run_dbcan-10-column format.
The `substrate_parser.py` takes the dbcan-formatted substrate output and map against the [substrate convertion table][dbcansub].

## Usage
Use `python3 dbcanlight.py --help` to see more details.
```
options:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        Protein fasta
  -o OUTPUT, --output OUTPUT
                        Output directory (default=stdout)
  -m {cazyme,sub}, --mode {cazyme,sub}
                        mode
  -e EVALUE, --evalue EVALUE
                        Reporting evalue cutoff (default=1e-15)
  -c COVERAGE, --coverage COVERAGE
                        Reporting coverage cutoff (default=0.35)
  -t THREADS, --threads THREADS
                        Total number of cpus allowed to use
  -v, --verbose         Verbose mode for debug
```

Say we have a protein fasta file **protein.faa**. Run the dbcan cazyme search with 8 cpus:
```
python3 dbcanlight.py -i protein.faa -m cazyme -t 8
```
By default the output will direct to stdout. Note that all the logs (below error level) will be suppressed.

Output to file by specifying `-o/--output [output directory]`.
```
python3 dbcanlight.py -i protein.faa -o output -m cazyme -t 8
```
The filename will be "**cazymes.tsv**" with `cazyme` mode and "**substrates.tsv**" with `sub` mode.

### hmmsearch and substrate parser
The script `hmmsearch_parser.py` can be used to process the domtblout format output from cli version hmmsearch.
It uses the Biopython SearchIO module to read the hmmer3 domtblout.
If a gene have multiple hits and these hits are overlapped over 50%, only the hit with the lowest evalue will be reported.
The output will be a 10-column tsv. (hmm_name, hmm_length, gene_name, gene_length, evalue, hmm_from, hmm_to, gene_from, gene_to, coverage)

Use `python3 hmmsearch_parser.py --help` to see more details.
```
options:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        CAZyme searching output in dbcan or hmmsearch format
  -o OUTPUT, --output OUTPUT
                        Output file path (default=stdout)
  -e EVALUE, --evalue EVALUE
                        Reporting evalue cutoff (default=1e-15)
  -c COVERAGE, --coverage COVERAGE
                        Reporting coverage cutoff (default=0.35)
  -v, --verbose         Verbose mode for debug
```

Say we have a file **hmmsearch.out** that come from hmmsearch with --domtblout enabled.
We can filter the results by:
```
python3 hmmsearch_parser.py -i hmmsearch.out
```

The script `substrate_parser.py` is used to map HMM profiles to its potential substrates.
Note that if your results is in domtblout format, you should first use `hmmsearch_parser.py` to convert it to a 10-column tsv.
Use `python3 substrate_parser.py --help` to see more details.
```
options:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        dbcan-sub searching output in dbcan format
  -o OUTPUT, --output OUTPUT
                        Output file path (default=stdout)
  -v, --verbose         Verbose mode for debug
```

## Requirements
- Python >= 3.7
- [Biopython]
- [pyhmmer]

Use the env.yaml to install all the required packages
```
conda env create -f env.yaml
```

[run_dbcan]: https://github.com/linnabrown/run_dbcan
[hmmscan_vs_hmmsearch]: http://cryptogenomicon.org/hmmscan-vs-hmmsearch-speed-the-numerology.html
[pyhmmer]: https://pyhmmer.readthedocs.io/en/stable/index.html
[dbcansub]: http://bcb.unl.edu/dbCAN2/download/Databases/fam-substrate-mapping-08252022.tsv
[Biopython]: https://biopython.org/