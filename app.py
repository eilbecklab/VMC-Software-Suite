from flask import abort, Flask, flash, render_template, request, redirect, send_from_directory, make_response, session
import subprocess, generate_identifiers, hgvs_conversion, json_conversion, validate, sqlite3, re
from werkzeug.contrib.cache import FileSystemCache
from hashlib import sha256

# create the application object
APP = Flask(__name__, static_folder='static')
APP.secret_key = "vmcsuite"
APP.config['UPLOAD_FOLDER'] = 'static/uploads'
cache = FileSystemCache('/tmp/vmc-suite')

def get_json_schema():
    """Returns the example JSON schema file as a string"""
    with open("static/schema.json") as f_in:
        return f_in.read()

def get_filename():
    """Returns the name of the uploaded VCF file"""
    return request.cookies.get("filename")

def get_fileKey():
    """Returns the key for the uploaded VCF file"""
    return request.cookies.get("fileKey")

def extract_ref(line_list):
    """Extracts the appropriate reference identifier from a line of the VCF.
        Prioritized as: 1) Accession 2) rsID 3) Chromosome and reference build"""
    #Check for accession in INFO field
    a = re.search(r'HGVS=\w+.\w+', line_list[7])
    if a:
        acc = a.group(0).split('=')[1]
        return 'a_' + acc
    #Check for rsID in ID field
    if 'rs' in line_list[2]:
        rs = line_list[2][2:]
        return 'r_' + rs
    #Check for rsID in INFO field
    m = re.search(r'RS=\d+', line_list[7])
    if m:
        rs = m.group(0).split('=')[1]
        return 'r_' + rs
    #Get chromosome number
    chr = line_list[0]
    #Get the user-specified reference build from the HTML select
    build = request.form.get('reference')
    return 'c_'+ build + '_' + chr

def get_refs_intervals_and_states(vcf_upload):
    """Takes the VCF file and returns lists of reference identifiers, location intervals, and alternate states
        for each variant"""
    intervals = []
    states = []
    refs = []
    for line in vcf_upload.split('\n'):
        if line != "":
            if line[0] == '#':
                continue
            else:
                line_list = line.split('\t')
                start = int(line_list[1]) - 1
                end = start + len(line_list[4])
                state = line_list[4]
                #Check for insertions or deletions
                ref = line_list[3]
                alt = line_list[4]
                #insdel
                if len(alt) > 1 and len(ref) > 1:
                    state = alt
                    end = start + len(alt)
                else:
                    #ins
                    if len(alt) > 1:
                        state = alt[1:]
                        end = start
                    #del
                    if len(ref) > 1:
                        start = start + 1
                        end = start + len(ref[1:])
                        state = ''
                intervals.append(str(start) + ":" + str(end))
                states.append(state)
                refs.append(extract_ref(line_list))
    return refs,intervals,states

def insert_identifiers(identifiers, vcf_upload):
    """Inserts the generated VMC identifiers into the file"""
    final = ""
    idx = 0
    info = 0
    for line in vcf_upload.split('\n'):
        if line != "":
            if line[1] == '#':
                final += line + '\n'
            elif line[0] == '#':
                headers = line.split('\t')
                for i in range(0, len(headers)):
                    if headers[i] == 'INFO':
                        info = i + 1
                final = final + """##INFO=<ID=VMCGSID,Number=1,Type=String,Description="VMC Sequence identifier">""" + '\n' + \
                        """##INFO=<ID=VMCGLID,Number=1,Type=String,Description="VMC Location identifier">""" + '\n' + \
                        """##INFO=<ID=VMCGAID,Number=1,Type=String,Description="VMC Allele identifier">\n""" + line
            else:
                line_list = line.split('\t')
                final = final + '\n' + '\t'.join(line_list[0:info]) + identifiers[idx] + '\t'.join(line_list[info:])
                idx += 1
    return final

@APP.route('/upload-vcf', methods=['POST'])
def upload_vcf():
    r = make_response(redirect(request.referrer))
    #check if the post request has the file part
    if 'file' not in request.files:
        return r
    file = request.files['file']
    # TODO Run VT tool to normalize variants in file, FASTA files already in referenceFASTA folder
    # subprocess.call(['vt', 'normalize', file.filename, '-r', seq.fa, '-o', 'normalized' + file.filename])
    read = file.read()
    vcf_upload = read.decode()
    fileKey = sha256(read).hexdigest()
    #Set cookies to track the filename and the file key (hash of the file contents)
    r.set_cookie("fileKey", fileKey)
    r.set_cookie("filename", file.filename)
    #Store the uploaded VCF in the cache with the file key
    cache.set(fileKey, vcf_upload, timeout=604800000)
    return r

@APP.route('/')
def index():
    return render_template('index.html')

@APP.route('/add_VMC_identifiers', methods=['GET', 'POST'])
def add_VMC_identifiers():
    fileKey = get_fileKey()
    #Check for the uploaded VCF in the cache
    if not fileKey or not cache.has(fileKey):
        return render_template('vcf-add-vmc.html', vcf_upload='No file uploaded')
    vcf_upload = cache.get(fileKey)
    if request.method == 'POST':
        """Checks to see if the transformed VCF already exists in the downloads folder, generates it if not. 
            Also sends the file path for downloading the transformed VCF file."""
        #Check if transformed VCF exists in the cache
        if not cache.has("vmc." + fileKey):
            #Get reference information, location intervals, and base changes for each variant
            refs,intervals,states = get_refs_intervals_and_states(vcf_upload)
            #Get the identifiers for the entire VCF
            identifiers = generate_identifiers.addIdentifiers(refs,intervals,states)
            vmc_vcf = insert_identifiers(identifiers,vcf_upload)
            cache.set("vmc." + fileKey, vmc_vcf, timeout=604800000)
        else:
            vmc_vcf = cache.get("vmc." + fileKey)
        return render_template('vcf-add-vmc.html', vcf_upload=vcf_upload, vmc_vcf=vmc_vcf)
    return render_template('vcf-add-vmc.html', vcf_upload=vcf_upload)

@APP.route('/vcf-download')
def vcf_download():
    filename = "vmc." + get_filename()
    fileKey = "vmc." + get_fileKey()
    if not cache.has(fileKey):
        abort(400)
    response = make_response(cache.get(fileKey))
    response.headers.set("Content-Disposition", "attachment; filename=" + filename )
    return response

@APP.route('/vcf-to-json', methods=['GET', 'POST'])
def vcf_to_json():
    json_schema = get_json_schema()
    fileKey = get_fileKey()
    if not fileKey or not cache.has(fileKey):
        return render_template('vcf-to-json.html', json_schema=json_schema, vcf_upload='No file uploaded')
    vcf_upload = cache.get(fileKey)
    if request.method == 'POST':
        """Checks to see if the transformed JSON already exists in the downloads folder, generates it if not, 
                then displays it along with the example JSON schema and the original uploaded file. 
                Also sends the file path for downloading the transformed JSON file."""
        #Check if transformed JSON exists in the cache
        if not cache.has(fileKey + '.json'):
            # Get reference information, location intervals, and base changes for each variant
            refs,intervals,states = get_refs_intervals_and_states(vcf_upload)
            #Get the identifiers for the entire VCF
            identifiers = generate_identifiers.generateJSON(refs,intervals,states)
            vcf_json = json_conversion.run(identifiers)
            cache.set(fileKey + '.json', vcf_json, timeout=604800000)
        else:
            vcf_json = cache.get(fileKey + '.json')
        return render_template('vcf-to-json.html', json_schema=json_schema, vcf_upload=vcf_upload, vcf_json=vcf_json)
    return render_template('vcf-to-json.html', json_schema=json_schema, vcf_upload=vcf_upload)

@APP.route('/vcf-to-json-download', methods=['GET', 'POST'])
def vcf_to_json_download():
    filename = get_filename()[0:-4] + ".json"
    fileKey = get_fileKey() + ".json"
    if not cache.has(fileKey):
        abort(400)
    response = make_response(cache.get(fileKey))
    response.headers.set("Content-Disposition", "attachment; filename=" + filename )
    return response

@APP.route('/hgvs-to-json', methods=['GET', 'POST'])
def hgvs_to_json():
    json_schema = get_json_schema()
    if request.method == 'POST':
        """ Uses conversions.py to convert a HGVS string to a VMC JSON bundle and displays it along with the example JSON schema."""
        hgvs = request.form['hgvs_string'].strip()
        acc = hgvs.split(":")[0]
        sequence_id = "Sequence identifier not found"
        found = False
        with sqlite3.connect("SeqID.db") as db:
            sql = "SELECT VMC_SEQ_ID FROM Accession WHERE ACCESSION=\'" + acc + "\'"
            cursor = db.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
            for row in rows:
                found = True
                sequence_id = row[0]
        if found:
            hgvs_json = hgvs_conversion.from_hgvs(hgvs,sequence_id)
            return render_template('hgvs-to-json.html', json_schema=json_schema, hgvs_string=hgvs, hgvs_json=hgvs_json)
        else:
            response = "No sequence identifier found for " + acc
            return render_template('hgvs-to-json.html', json_schema=json_schema, hgvs_string=hgvs, hgvs_json=response)
    return render_template('hgvs-to-json.html')

'''
@APP.route('/validator', methods=['GET', 'POST'])
def validation():
    if request.method == 'POST':
        select_type = request.form.get('select_type')
        #Validation for a sequence identifier
        if select_type == "seq":
            user_seq = request.form['user_seq']
            seqID = get_seqID(select_type, request)
            if user_seq == seqID:
                return render_template('validator.html', valid=True, message="Valid identifier!")
            else:
                return render_template(
                    'validator.html',
                    valid=False,
                    message="Invalid identifier: &emsp;" + user_seq + "<br/>&emsp;&emsp;&emsp;What we computed: " + seqID
                )

        #Validation for a location identifier
        elif select_type == "loc":
                print("loc requested")
                user_loc = request.form['user_loc']
                seqID = get_seqID(select_type, request)
                start = request.form['loc_start_loc']
                locID = validate.build_loc(seqID, int(start))
                if locID == user_loc:
                    return render_template('validator.html', valid=True, message="Valid identifier!")
                else:
                    return render_template(
                        'validator.html',
                        valid=False,
                        message="Invalid identifier: " + user_loc + "<br/>&emsp;&emsp;&emsp;What we computed: " + locID
                    )

            #Validation for a allele identifier
        elif select_type == "allele":
                print("allele requested")
                user_allele = request.form['user_allele']
                seqID = get_seqID(select_type, request)
                start = request.form['allele_start_loc']
                locID = validate.build_loc(seqID, int(start))
                print("locID: " + locID)
                state = request.form['state']
                print("state: " + state)
                alleleID = validate.build_allele(locID, state)
                print("alleleID: " + alleleID)
                if alleleID == user_allele:
                    return render_template('validator.html', valid=True, message="Valid identifier!")
                else:
                    return render_template(
                        'validator.html',
                        valid=False,
                        message="Invalid identifier: " + user_allele + "<br/>&emsp;&emsp;&emsp;What we computed: " + alleleID
                    )
        #Invalid selection
        else:
            return render_template('validator.html')

    #Invalid selection
    else:
        return render_template('validator.html')

'''

# start the server with the 'run()' method
if __name__ == '__main__':
    APP.run(debug=True, host="0.0.0.0",port=8000)
