"""Configurations for package (internal use only)."""

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DBPath:
    """Dataclass for database paths."""

    cazyme_hmms: Path
    subs_hmms: Path
    subs_mapper: Path
    diamond: Path


@dataclass
class Headers:
    """Dataclass for headers."""

    cazyme: tuple
    sub: tuple
    diamond: tuple
    overview: tuple


# CPUs
avail_cpus = int(os.environ.get("SLURM_CPUS_ON_NODE", os.cpu_count()))

cfg_dir = Path.home() / ".dbcanlight"

db_path = DBPath(
    cazyme_hmms=cfg_dir / "cazyme.hmm",
    subs_hmms=cfg_dir / "substrate.hmm",
    subs_mapper=cfg_dir / "substrate_mapping.tsv",
    diamond=cfg_dir / "cazydb.dmnd",
)

databases_url = {
    "cazyme_hmms": ("https://bcb.unl.edu/dbCAN2/download/Databases/V12/dbCAN-HMMdb-V12.txt", db_path.cazyme_hmms.name),
    "subs_hmms": ("https://bcb.unl.edu/dbCAN2/download/Databases/dbCAN_sub.hmm", db_path.subs_hmms.name),
    "subs_mapper": ("https://bcb.unl.edu/dbCAN2/download/Databases/fam-substrate-mapping-08252022.tsv", db_path.subs_mapper.name),
    "diamond": ("https://bcb.unl.edu/dbCAN2/download/Databases/CAZyDB.07262023.fa", "cazydb.fa"),
}

avail_modes = {"cazyme": "cazymes.tsv", "sub": "substrates.tsv", "diamond": "diamond.tsv"}

cazyme_header = (
    "HMM_Profile",
    "Profile_Length",
    "Gene_ID",
    "Gene_Length",
    "Evalue",
    "Profile_Start",
    "Profile_End",
    "Gene_Start",
    "Gene_End",
    "Coverage",
)

overview_fams = [f"{mode}_fam" for mode in avail_modes]

headers = Headers(
    cazyme=cazyme_header,
    sub=("dbCAN_subfam", "Subfam_Composition", "Subfam_EC", "Substrate") + cazyme_header[1:],
    diamond=(
        "qseqid",
        "sseqid",
        "pident",
        "length",
        "mismatch",
        "gapopen",
        "qstart",
        "qend",
        "sstart",
        "send",
        "evalue",
        "bitscore",
    ),
    overview=("Gene_ID", "EC", *overview_fams, "Substrate", "#ofTools"),
)
