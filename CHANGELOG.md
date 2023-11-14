# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.2] - 2023-10-13

### Changed

- Unify the runner function for cazyme and substrate detections.

### Fixed

- Fix bugs for output from dbcanLight-hmmparser and dbcanLight-subparser.

## [1.0.1] - 2023-09-29

### Fixed

- Fix typo in substrate discovery module which lead to file not found error.

## [1.0.0] - 2023-09-14

### Added

- Implement cazyme and substrate detection with multi-threads supported hmmsearch from pyhmmer.

- Companion commands dbcanLight-hmmparser ([hmmsearch_parser.py](https://github.com/chtsai0105/dbcanLight/blob/v1.0.0/src/dbcanlight/hmmsearch_parser.py)) helps to convert conventional hmmer3 output to dbcan format and dbcanLight-subparser ([substrate_parser.py](https://github.com/chtsai0105/dbcanLight/blob/v1.0.0/src/dbcanlight/substrate_parser.py)) helps to map to the potential substrate (require to search against the [substrate hmm porfile](https://bcb.unl.edu/dbCAN2/download/Databases/dbCAN_sub.hmm)).

- Rewrite the hmmsearch filtering codes initally written in Perl by Yanbin Yin@NIU to a Python function [overlap_filter](https://github.com/chtsai0105/dbcanLight/blob/v1.0.0/src/dbcanlight/hmmsearch_parser.py#L78-L110) under hmmsearch_parser.py.

- Process and filter hmmsearch hits on-the-fly to prevent the out-of-memory issue for large input files.

[1.0.2]: https://github.com/chtsai0105/dbcanLight/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/chtsai0105/dbcanLight/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/chtsai0105/dbcanLight/releases/tag/v1.0.0
