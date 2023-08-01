import logging
from pathlib import Path
from copy import deepcopy


class header:
    hmmsearch = [
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

    substrate = deepcopy(hmmsearch)
    substrate.pop(0)
    substrate[0:0] = ["dbCAN_subfam", "Subfam_Composition", "Subfam_EC", "Substrate"]


def writer(results, output, header=[]):
    if isinstance(output, Path):
        logging.info(f"Write output to {output}")
        out = open(output, "w")
        if len(header) == len(results[0]):
            print("\t".join([str(x) for x in header]), file=out)
    else:
        out = output
    for line in results:
        print("\t".join([str(x) for x in line]), file=out)
