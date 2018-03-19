import os, json
from datetime import datetime
from collections import OrderedDict
from ctypes import cdll

def generate_identifiers(filename):
    vmc_lib = cdll.LoadLibrary('./govcf-vmc.so')
    print('Generating the VMC unique IDs')
    vmc_lib.Transform(filename)

def assemble_json(bundle):
    d = OrderedDict()
    d["$schema"] = "http://json-schema.org/schema#"
    locations = OrderedDict()
    alleles = OrderedDict()
    identifiers = OrderedDict()
    for line in bundle:
        b = line.split("\t")
        #Extract elements for JSON
        loc_id = b[0]
        interval = b[1].split(":")
        start = interval[0]
        end = interval[1]
        seq_id = b[2]
        all_id = b[3]
        state = b[4]
        accession = b[5]
        namespace = b[6].strip()
        #Build dictionary to convert to JSON
        locations[loc_id] = {
            "id":loc_id,
            "interval":{
                "end":end,
                "start":start},
            "sequence_id":seq_id
        }
        alleles[all_id] = {
            "id":all_id,
            "location_id":loc_id,
            "state":state
        }
        identifiers[seq_id] = {"namespace":namespace,"accession":accession}
        identifiers[loc_id] = {"namespace":"VMC","accession":loc_id.split(":")[1]}
        identifiers[all_id] = {"namespace":"VMC","accession":all_id.split(":")[1]}
    d["locations"] = locations
    d["alleles"] = alleles
    d["haplotypes"] = {"":""}
    d["genotypes"] = {"":""}
    d["identifiers"] = identifiers
    d["meta"] = {"generated_at":str(datetime.now()),"vmc_version":"0.1"}
    return d

def run(filename, out):
    """
        Checks for go.bundle which is an intermediary file used to generate identifiers to be used in the JSON representation. If it doesn't exist, then it calls govcf-vmc to
        generate it then assembles the JSON using ordered dictionaries.
    """
    if "go.bundle" not in os.listdir():
        generate_identifiers(filename)
    with open("go.bundle","r") as bundle:
        d = assemble_json(bundle)
        with open(out,"w") as f_out:
            f_out.write(json.dumps(d, ensure_ascii=False, indent=4))
