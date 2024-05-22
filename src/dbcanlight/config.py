import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DBPath:
    cazyme_hmms: Path
    subs_hmms: Path
    subs_mapper: Path


@dataclass
class Headers:
    hmmsearch: tuple
    substrate: tuple


# CPUs
avail_cpus = int(os.environ.get("SLURM_CPUS_ON_NODE", os.cpu_count()))

cfg_dir = Path.home() / ".dbcanlight"

db_path = DBPath(
    cazyme_hmms=cfg_dir / "cazyme.hmm", subs_hmms=cfg_dir / "substrate.hmm", subs_mapper=cfg_dir / "substrate_mapping.tsv"
)


hmmsearch_header = [
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
]

headers = Headers(
    hmmsearch=tuple(hmmsearch_header),
    substrate=tuple(["dbCAN_subfam", "Subfam_Composition", "Subfam_EC", "Substrate"] + hmmsearch_header[1:]),
)
