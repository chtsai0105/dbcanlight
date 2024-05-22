import logging
import sys
from pathlib import Path
from typing import Iterator
from functools import wraps

from dbcanlight.config import headers


def check_db(*dbs: Path) -> None:
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            dbmissingList = []
            for db in dbs:
                dbmissingList.append(db) if not db.exists() else None
            if dbmissingList:
                print(
                    f"Database file {*dbmissingList,} missing. "
                    "Please follow the instructions in https://github.com/chtsai0105/dbcanLight#requirements and download the required databases."
                )
                sys.exit(1)
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def writer(results: Iterator[list], output) -> None:
    first_line = next(results)
    if isinstance(output, Path):
        output.mkdir(parents=True, exist_ok=True)

        if len(first_line) == len(headers.hmmsearch):
            header = headers.hmmsearch
            output = output / "cazymes.tsv"
        elif len(first_line) == len(headers.substrate):
            header = headers.substrate
            output = output / "substrates.tsv"
        else:
            raise Exception("The length of the results doesn't match to any form of headers.")

        logging.info(f"Write output to {output}")
        output = open(output, "w")
        print("\t".join([str(x) for x in header]), file=output)

    print("\t".join([str(x) for x in first_line]), file=output)
    for line in results:
        print("\t".join([str(x) for x in line]), file=output)
