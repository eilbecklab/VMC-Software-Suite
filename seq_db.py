import sqlite3, subprocess

def create_table():
    db_name = "sequence_identifiers.db"
    sql = """create table Sequence_Identifiers
            (BUILD text,
            NAMESPACE text,
            ACCESSION text,
            CHR text,
            IDENTIFIER text)"""
    with sqlite3.connect(db_name) as db:
        cursor = db.cursor()
        cursor.execute(sql)
        db.commit()

def insert_identifiers(identifiers):
    with sqlite3.connect("sequence_identifiers.db") as db:
        cursor = db.cursor()
        sql = "insert into Sequence_Identifiers (BUILD, NAMESPACE, ACCESSION, CHR, IDENTIFIER) values (?,?,?,?,?)"
        for identifier in identifiers:
            cursor.execute(sql, identifier)
        db.commit()

def create_identifiers():
    seqs = ['chr1.fa', 'chr2.fa','chr3.fa','chr4.fa','chr5.fa','chr6.fa','chr7.fa','chr8.fa','chr9.fa','chr10.fa','chr11.fa','chr12.fa',\
        'chr13.fa','chr14.fa','chr15.fa','chr16.fa','chr17.fa','chr18.fa','chr19.fa','chr20.fa','chr21.fa','chr22.fa','chrX.fa','chrY.fa']
    acc_37 = ['NC_000001.10','NC_000002.11','NC_000003.11','NC_000004.11','NC_000005.9','NC_000006.11','NC_000007.13','NC_000008.10','NC_000009.11',\
            'NC_000010.10','NC_000011.9','NC_000012.11','NC_000013.10','NC_000014.8','NC_000015.9','NC_000016.9','NC_000017.10','NC_000018.9',\
            'NC_000019.9','NC_000020.10','NC_000021.8','NC_000022.10','NC_000023.10','NC_000024.9']
    namespace = "NCBI"
    identifiers = []
    for i in range(len(seqs)):
        seq = seqs[i]
        print(seq)
        name = 'ref_seqs/' + seq
        seq_id = str(subprocess.check_output(['vmccl','--fasta', name]))
        build = "GRCh37"
        chr = seq
        identifiers.append((build, namespace, acc[i], chr, seq_id.split(' ')[6][:-3]))
    return identifiers

def get_seqs(name):
    seqs = []
    with sqlite3.connect("sequence_identifiers.db") as db:
        cursor = db.cursor()
        cursor.execute("SELECT IDENTIFIER FROM Sequence_Identifiers WHERE BUILD=\'"+name+"\'")
        rows = cursor.fetchall()
        for row in rows:
            seqs.append(row[0])
    print(seqs)
    return seqs

if __name__=="__main__":
    create_table()
    identifiers = create_identifiers()
    insert_identifiers(identifiers)
    #get_seqs("GRCh38")
