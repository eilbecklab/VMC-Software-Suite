import json
from datetime import datetime
from collections import OrderedDict

def assemble_json(ids):
    d = OrderedDict()
    locations = OrderedDict()
    alleles = OrderedDict()
    identifiers = OrderedDict()
    for line in ids:
        print(line)
        b = line.split("\t")
        #Extract elements for JSON
        seq_id = b[0]
        accession = b[1]
        namespace = b[2]
        if seq_id[:5] == 'Error':
            loc_id = ''
            allele_id = ''
            identifiers[loc_id] = [{"namespace": "VMC", "accession": 'Error with Sequence Identifier'}]
            identifiers[allele_id] = [{"namespace": "VMC", "accession": 'Error with Sequence Identifier'}]
        else:
            loc_id = b[4]
            allele_id = b[6]
            identifiers[loc_id] = [{"namespace": "VMC", "accession": loc_id.split(":")[1]}]
            identifiers[allele_id] = [{"namespace": "VMC", "accession": allele_id.split(":")[1]}]
        interval = b[3].split(":")
        start = int(interval[0])
        end = int(interval[1])
        state = b[5]
        #Build dictionary to convert to JSON
        locations[loc_id] = {
            "id":loc_id,
            "interval": {
                "end": end,
                "start": start},
            "sequence_id": seq_id
        }
        alleles[allele_id] = {
            "id": allele_id,
            "location_id": loc_id,
            "state": state
        }
        identifiers[seq_id] = [{"namespace":namespace,"accession":accession}]
    d["locations"] = locations
    d["alleles"] = alleles
    d["haplotypes"] = {"":""}
    d["genotypes"] = {"":""}
    d["identifiers"] = identifiers
    d["meta"] = {"generated_at":str(datetime.now()),"vmc_version":"0.1"}
    return d

def run(ids):
    d = assemble_json(ids)
    return json.dumps(d, ensure_ascii=False, indent=4)
