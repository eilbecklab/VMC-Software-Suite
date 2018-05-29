from vmc import models, computed_id
import base64, hashlib

def build_seq(ref):
    seqID = "VMC:GS_" + digest(ref.encode("ASCII"))
    return seqID

def build_loc(seq_id, start):
    interval = models.Interval(start=start, end=start+1)
    location = models.Location(sequence_id=seq_id, interval=interval)
    location.id = computed_id(location)
    return location.id

def build_allele(loc_id, state):
    allele = models.Allele(location_id=loc_id, state=state)
    allele.id = computed_id(allele)
    return allele.id

def digest(blob, n=24):
    d = hashlib.sha512(blob).digest()
    return base64.urlsafe_b64encode(d[:n]).decode("ASCII")
