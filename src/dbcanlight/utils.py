import logging
import sys

if sys.version_info >= (3, 9):
    from collections.abc import Iterator
else:
    from typing import Iterator

from pathlib import Path


def check_db(*dbs: Path) -> None:
    dbmissingList = []
    for db in dbs:
        dbmissingList.append(db) if not db.exists() else None
    if dbmissingList:
        print(
            f"Database file {*dbmissingList,} missing. "
            "Please follow the instructions in https://github.com/chtsai0105/dbcanLight#requirements and download the required database."
        )
        sys.exit(1)


def writer(results: Iterator[list], output, header: list = []) -> None:
    first_line = next(results)
    if isinstance(output, Path):
        logging.info(f"Write output to {output}")
        output = open(output, "w")
        if len(header) == len(first_line):
            print("\t".join([str(x) for x in header]), file=output)
        else:
            raise Exception("The length of results and header is not consistent")

    print("\t".join([str(x) for x in first_line]), file=output)
    for line in results:
        print("\t".join([str(x) for x in line]), file=output)
