from copy import deepcopy
from types import SimpleNamespace
from pathlib import Path

db_path = SimpleNamespace()
cfg_dir = Path.home() / ".dbcanlight"
db_path.cazyme_hmms = cfg_dir / "cazyme.hmm"
db_path.subs_hmms = cfg_dir / "substrate.hmm"
db_path.subs_mapper = cfg_dir / "substrate_mapping.tsv"

header = SimpleNamespace()
header.hmmsearch = [
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

header.substrate = deepcopy(header.hmmsearch)
header.substrate.pop(0)
header.substrate[0:0] = ["dbCAN_subfam", "Subfam_Composition", "Subfam_EC", "Substrate"]
