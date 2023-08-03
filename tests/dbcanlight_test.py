from dbcanlight.dbcanlight import cazyme_finder, substrate_finder

input = "tests/example.faa"


def test_cazyme_finder(tmpdir):
    file = tmpdir.join("cazymes.tsv")
    cazyme_finder(input=input, output=tmpdir, evalue=1e-15, coverage=0.35)
    header = [
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
    with open(file) as f:
        line_1 = f.readline().strip("\n").split("\t")
        line_2 = f.readline().strip("\n").split("\t")
    assert header == line_1 and len(line_2) == 10


def test_substrate_finder(tmpdir):
    file = tmpdir.join("substrates.tsv")
    substrate_finder(input=input, output=tmpdir, evalue=1e-15, coverage=0.35)
    header = [
        "dbCAN_subfam",
        "Subfam_Composition",
        "Subfam_EC",
        "Substrate",
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
    with open(file) as f:
        line_1 = f.readline().strip("\n").split("\t")
        line_2 = f.readline().strip("\n").split("\t")
    assert header == line_1 and len(line_2) == 13
