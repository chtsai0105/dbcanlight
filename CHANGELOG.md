# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic
Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.0] - 2024-08-30

### Added

- Diamond as the third tool for prediction.

- Conclude module to report an overview of the predictions made by each tool.

### Changed

- Use a menu to display all the available modules.

### Removed

- Output to stdout and input from stdin in not available anymore.

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

- Companion commands dbcanLight-hmmparser
  ([hmmsearch\_parser.py](https://github.com/chtsai0105/dbcanLight/blob/v1.0.0/src/dbcanlight/hmmsearch_parser.py)) helps to
  convert conventional hmmer3 output to dbcan format and dbcanLight-subparser
  ([substrate\_parser.py](https://github.com/chtsai0105/dbcanLight/blob/v1.0.0/src/dbcanlight/substrate_parser.py)) helps to map to
  the potential substrate (require to search against the [substrate hmm
  profile](https://bcb.unl.edu/dbCAN2/download/Databases/dbCAN_sub.hmm)).

- Rewrite the hmmsearch filtering codes initially written in Perl by Yanbin Yin@NIU to a Python function
  [overlap\_filter](https://github.com/chtsai0105/dbcanLight/blob/v1.0.0/src/dbcanlight/hmmsearch_parser.py#L78-L110) under
  hmmsearch\_parser.py.

- Process and filter hmmsearch hits on-the-fly to prevent the out-of-memory issue for large input files.

[Unreleased]: https://github.com/chtsai0105/dbcanlight/compare/v1.1.0...HEAD

[1.1.0]: https://github.com/chtsai0105/dbcanlight/compare/v1.0.2...v1.1.0

[1.0.2]: https://github.com/chtsai0105/dbcanlight/compare/v1.0.1...v1.0.2

[1.0.1]: https://github.com/chtsai0105/dbcanlight/compare/v1.0.0...v1.0.1

[1.0.0]: https://github.com/chtsai0105/dbcanlight/releases/tag/v1.0.0
