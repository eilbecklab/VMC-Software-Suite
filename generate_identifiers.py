import base64, hashlib, sqlite3, requests, re

def GG_template(completeness, GH_list):
    template = "<Genotype:" + completeness + ":["
    for GH in GH_list:
        template = template + "<Identifier:" + GH + ">;"
    return template[:-1] + "]>"

def GH_template(completeness, GA_list):
    template = "<Haplotype:" + completeness + ":["
    for GA in GA_list:
        template = template + "<Identifier:" + GA + ">;"
    return template[:-1] + "]>"

def GA_template(GL, state):
    return "<Allele:<Identifier:" + GL + ">:" + state + ">"

def GL_template(GS, interval):
    return "<Location:<Identifier:" + GS + ">:<Interval:" + interval + ">>"

def digest(blob, n=24):
    try:
        d = hashlib.sha512(blob.encode('ASCII')).digest()
        result = base64.urlsafe_b64encode(d[:n]).decode("ASCII")
        return result
    except:
        print(blob)
    return 'error'

def getFASTA(acc):
    #Get NCBIs GI associated with that Accession.Version (embedded in HTML)
    entry_url = 'https://www.ncbi.nlm.nih.gov/nuccore/' + acc + '?report=fasta'
    r = requests.get(entry_url)
    try:
        m = re.search(r'viewercontent1.+', r.text)
        file_id = m.group(0)
        gi = file_id.split('val=')[1].split("\"")[1]
        # Query NCBI for the FASTA associated with that GI
        try:
            file_url = 'https://www.ncbi.nlm.nih.gov/sviewer/viewer.cgi?tool=portal&save=file&log$=seqview&db=nuccore&' \
                       'report=fasta&id=' + gi + '&extrafeat=null&conwithfeat=on'
            fa = requests.get(file_url).text
            return gi,fa
        except:
            return gi,'GI error'
    except:
        return acc,'Acc error'

def getAccession(rs):
    try:
        #Query dbSNP for an entry of that RS ID
        entry_url = 'https://www.ncbi.nlm.nih.gov/SNP/snp_ref.cgi?rs=' + rs
        r = requests.get(entry_url)
        print('Acc query code: ' + r.status_code)
        #Extract HGVS expressions associated with that RS ID from the HTML
        m = re.findall(r'<ul class="dd_list">.+</ul>', r.text)[0]
        a = re.findall(r'f1">[\w\d\.]+:', m)
        #Select the most recent complete genomic (NC) accession
        max = 0
        max_acc = ''
        for acc in a:
            acc = acc[4:-1]
            if acc[:2] == 'NC':
                version = float(acc[3:])
                if version > max:
                    max = version
                    max_acc = acc
        if max_acc == '':
            return 'RS error'
        return max_acc
    except:
        return 'RS error'

def generateSeqID(ref):
    if ref[0] == 'r':
        rs = ref[2:]
        sql = 'select accession from RS where RS=' + rs
        acc = query(sql)
        #If the RS hasn't been seen before, find it's accession and add it to the RS table
        if acc == '':
            print('Getting accession for ' + rs)
            acc = getAccession(rs)
            with sqlite3.connect("SeqID.db") as db:
                sql = "insert into RS (RS,ACCESSION) values (?,?)"
                cursor = db.cursor()
                cursor.execute(sql, (rs, acc))
                db.commit()
                print('Entering RS|Acc ' + rs + '|' + acc)
            if acc == 'RS error':
                return 'Error: rsID not found at https://www.ncbi.nlm.nih.gov/SNP/snp_ref.cgi?rs=' + rs
        if acc == 'RS error':
            return 'Error: rsID not found at https://www.ncbi.nlm.nih.gov/SNP/snp_ref.cgi?rs=' + rs
    if ref[0] == 'a':
        acc = ref[2:]
    #Check for a seqID already digested for that accession
    sql = 'select VMC_SEQ_ID from Accession where ACCESSION=' + '\'' + acc + '\''
    seqID = query(sql)
    if seqID != '':
        return seqID
    #If it's a new accession
    print('getting FASTA')
    gi,fa = getFASTA(acc)
    print('Done!')
    if fa == 'Acc error':
        return 'Error: ' + acc + ' not recognized at https://www.ncbi.nlm.nih.gov/nuccore'
    if fa == 'GI error':
        return 'Error: Problem downloading FASTA from NCBI using GI: ' + gi + ' for ' + acc
    #Remove the first line of FASTA and remove all newlines
    first = fa.find('\n')
    fa = fa[first:].replace('\n', '')
    #Create the Sequence identifier
    seqID = 'VMC:GS_' + digest(fa)
    #Push the new seqID to the DB
    try:
        pushToDB(seqID,acc,gi)
    except:
        print(ref)
    return seqID

def pushToDB(seqID,acc,gi):
    with sqlite3.connect("SeqID.db") as db:
        cursor = db.cursor()
        sql = "insert into Accession (VMC_SEQ_ID,ACCESSION,GI) values (?,?,?)"
        cursor.execute(sql, (seqID,acc,gi))
        db.commit()

def checkDB(ref):
    if ref[0] == 'c':
        build = '\'' + ref[2:6] + '\''
        chr = ref[7:]
        sql = 'select VMC_SEQ_ID from Chromosome where BUILD=' + build + ' and CHROMOSOME=' + chr
        return query(sql)
    if ref[0] == 'a':
        acc = '\'' + ref[2:] + '\''
        sql = 'select VMC_SEQ_ID from Accession where ACCESSION=' + acc
        return query(sql)
    return ''

def query(sql):
    with sqlite3.connect("SeqID.db") as db:
        cursor = db.cursor()
        cursor.execute(sql)
        data = cursor.fetchall()
        if not data:
            return ''
        else:
            return data[0][0]

def getSeqID(ref):
    """Ref should be accession (prefix: a_, if exists in VCF),
                or rsID (prefix: r_, if no accession in VCF),
                or chromosome and build (prefix: c_, if no rsID in VCF)"""
    seqID = checkDB(ref)
    if seqID == '':
        seqID = generateSeqID(ref)
    return seqID

def addIdentifiers(refs,intervals,states):
    results = []
    for i in range(len(refs)):
        seqID = getSeqID(refs[i])
        if seqID[:5] == 'Error':
            results.append(";VMCGSID=" + seqID)
        else:
            # Generate the location identifier
            GL = "VMC:GL_" + digest(GL_template(seqID,intervals[i]))
            #Generate the allele identifier
            GA = "VMC:GA_" + digest(GA_template(GL,states[i]))
            #Compile them into an appropriate string
            results.append(";VMCGSID=" + seqID + ";VMCGLID=" + GL + ";VMCGAID=" + GA)
    return results

def generateJSON(refs,intervals,states):
    results = []
    for i in range(len(refs)):
        ref = refs[i]
        print(ref)
        seqID = getSeqID(ref)
        if seqID[:5] == 'Error':
            results.append(seqID + '\t' + ref[2:] + '\t' + 'dbSNP' + '\t' + intervals[i] + '\t' + 'Error with Sequence Identifier' + '\t' + states[i] + '\t' + 'Error with Sequence Identifer')
        else:
            # Generate the location identifier
            GL = "VMC:GL_" + digest(GL_template(seqID, intervals[i]))
            # Generate the allele identifier
            GA = "VMC:GA_" + digest(GA_template(GL, states[i]))
            if ref[0] == 'a':
                results.append(seqID + '\t' + ref[2:] + '\t' + 'NCBI' + '\t' + intervals[i] + '\t' + GL + '\t' + states[i] + '\t' + GA)
            elif ref[0] == 'r':
                results.append(seqID + '\t' + ref[2:] + '\t' + 'dbSNP' + '\t' + intervals[i] + '\t' + GL + '\t' + states[i] + '\t' + GA)
            else:
                build = ref[2:6]
                if build == 'hg19':
                    build = 'GRCh37'
                if build == 'hg38':
                    build = 'GRCh38'
                chr = ref[7:]
                results.append(seqID + '\t' + chr + '\t' + build + '\t' + intervals[i] + '\t' + GL + '\t' + states[i] + '\t' + GA)
    return results
