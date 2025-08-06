from . import AVAIL_MODES

_cazyme_header = (
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


class Headers:
    """Dataclass for headers."""

    cazyme: tuple = _cazyme_header
    sub: tuple = ("dbCAN_subfam", "Subfam_Composition", "Subfam_EC", "Substrate") + _cazyme_header[1:]
    diamond: tuple = (
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
    )
    overview: tuple = ("Gene_ID", "EC", *[f"{mode}_fam" for mode in AVAIL_MODES], "Substrate", "#ofTools")
