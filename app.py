from flask import Flask, flash, render_template, \
    request, redirect, send_from_directory, make_response
import os, generate_identifiers, hgvs_conversion, json_conversion, sqlite3
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

def get_chrs_intervals_and_states(vcf_upload):
    """Takes the VCF file and returns lists of chromosomes, intervals, and states for each variant"""
    intervals = []
    states = []
    chrs = []
    for line in vcf_upload.split('\n'):
        if line != "":
            if line[0] == '#':
                continue
            else:
                line_list = line.split('\t')
                intervals.append(line_list[1] + ":" + str(int(line_list[1]) + len(line_list[4])))
                states.append(line_list[4])
                chrs.append(line_list[0])
    return chrs,intervals,states

def get_seqs(name):
    seqs = []
    with sqlite3.connect("sequence_identifiers.db") as db:
        cursor = db.cursor()
        cursor.execute("SELECT IDENTIFIER FROM Sequence_Identifiers WHERE BUILD=\'"+name+"\'")
        rows = cursor.fetchall()
        for row in rows:
            seqs.append(row[0])
    return seqs

def get_accs(name):
    accs = []
    with sqlite3.connect("sequence_identifiers.db") as db:
        cursor = db.cursor()
        cursor.execute("SELECT ACCESSION FROM Sequence_Identifiers WHERE BUILD=\'"+name+"\'")
        rows = cursor.fetchall()
        for row in rows:
            accs.append(row[0])
    return accs

def add_identifiers(identifiers, vcf_upload):
    print(identifiers)
    final = ""
    idx = 0
    for line in vcf_upload.split('\n'):
        if line != "":
            if line[1] == '#':
                final += line + '\n'
            elif line[0] == '#':
                final = final + """##INFO=<ID=VMCGSID,Number=1,Type=String,Description="VMC Sequence identifier">""" + '\n' + \
                        """##INFO=<ID=VMCGLID,Number=1,Type=String,Description="VMC Location identifier">""" + '\n' + \
                        """##INFO=<ID=VMCGAID,Number=1,Type=String,Description="VMC Allele identifier">\n""" + line
            else:
                line_list = line.split('\t')
                final = final + '\n' + line_list[0] + '\t' + line_list[1] + '\t' + line_list[2] + '\t' + line_list[3] + '\t' + line_list[4] + '\t' + line_list[5] + '\t' + \
                        line_list[6] + '\t' + line_list[7] + identifiers[idx] + '\t' + line_list[8] + '\t' + line_list[9]
                idx += 1
    return final


@APP.route('/', methods=['GET', 'POST'])
def home():
    """
        Displays the example JSON schema, saves the uploaded VCF file to the cache and displays it as well.

    """
    json_schema = get_json_schema()
    if request.method == 'POST':
        #check if the post request has the file part
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        vcf_upload = file.read().decode()
        fileKey = sha256(file.read()).hexdigest()
        #Displays uploaded VCF with example JSON
        r = make_response(render_template('index.html',vcf_upload=vcf_upload,json_schema=json_schema))
        #Set cookies to track the filename and the file key (hash of the file contents)
        r.set_cookie("fileKey", fileKey)
        r.set_cookie("filename", file.filename)
        #Store the uploaded VCF in the cache with the file key
        cache.set(fileKey, vcf_upload, timeout=604800000)
        return r
    #Displays example JSON
    return render_template('index.html',json_schema=json_schema)


@APP.route('/vmc_vcf', methods=['GET', 'POST'])
def display_vmc_vcf():
    """
        Checks to see if the transformed VCF already exists in the downloads folder, generates it if not from transform.py, then displays it along with the
        example JSON schema and the original uploaded file. Also sends the filepath for downloading the transformed VCF file.
    """
    json_schema = get_json_schema()
    fileKey = get_fileKey()
    #Check for the uploaded VCF in the cache
    if not cache.has(fileKey):
            return render_template('index.html', json_schema=json_schema, vcf_upload="No file uploaded", vmc_vcf="No file uploaded")
    vcf_upload = cache.get(fileKey)
    #Check if transformed VCF exists in the cache
    if not cache.has("vmc." + fileKey):
        #Get the sequence identifiers
        seqs = get_seqs(request.form['reference'])
        #Get chromosome #'s, intervals, and states for each variant
        chrs,intervals,states = get_chrs_intervals_and_states(vcf_upload)
        #Get the identifiers for the entire VCF
        identifiers = generate_identifiers.vcf_to_vmc(seqs,chrs,intervals,states)
        vmc_vcf = add_identifiers(identifiers,vcf_upload)
        cache.set("vmc." + fileKey, vmc_vcf, timeout=604800000)
    else:
        vmc_vcf = cache.get("vmc." + fileKey)

    return render_template('index.html', json_schema=json_schema, vcf_upload=vcf_upload, vmc_vcf=vmc_vcf)

@APP.route('/vmc_vcf_download')
def serve_vmc_vcf():
    filename = "vmc." + get_filename()
    fileKey = "vmc." + get_fileKey()
    if cache.has(fileKey):
        response = make_response(cache.get(fileKey))
        response.headers.set("Content-Disposition", "attachment; filename=" + filename )
        return response

@APP.route('/json_bundle', methods=['GET', 'POST'])
def display_json_bundle():
    """
        Checks to see if the transformed JSON already exists in the downloads folder, generates it if not from bundle.py, then displays it along with the
        example JSON schema and the original uploaded file. Also sends the filepath for downloading the transformed JSON file.

    """
    json_schema = get_json_schema()
    fileKey = get_fileKey()
    if not cache.has(fileKey):
            return render_template('index.html', json_schema=json_schema, vcf_upload="No file uploaded", vcf_json="No file uploaded")
    vcf_upload = cache.get(fileKey)
    #Check if transformed JSON exists in the cache
    cache.delete(fileKey + '.json')
    if not cache.has(fileKey + '.json'):
        #Get the sequence identifiers
        seqs = get_seqs(request.form['reference'])
        #Get the accession numbers
        accs = get_accs(request.form['reference'])
        #Get chromosome #'s, intervals, and states for each variant
        chrs,intervals,states = get_chrs_intervals_and_states(vcf_upload)
        #Get the identifiers for the entire VCF
        identifiers = generate_identifiers.json_to_vmc(seqs,accs,chrs,intervals,states)
        vcf_json = json_conversion.run(identifiers)
        cache.set(fileKey + '.json', vcf_json, timeout=604800000)
    else:
        vcf_json = cache.get(fileKey + '.json')
    return render_template('index.html', json_schema=json_schema, vcf_upload=vcf_upload, vcf_json=vcf_json)

@APP.route('/vcf_json_download')
def serve_vcf_json():
    filename = get_filename()[0:-4] + ".json"
    fileKey = get_fileKey() + ".json"

    if cache.has(fileKey):
        response = make_response(cache.get(fileKey))
        response.headers.set("Content-Disposition", "attachment; filename=" + filename )
        return response

@APP.route('/hgvs', methods=['GET', 'POST'])
def hgvs_to_json():
    """
        Uses conversions.py to convert a HGVS string to a VMC JSON bundle and displays it along with the example JSON schema.

    """
    json_schema = get_json_schema()
    hgvs = request.form['hgvs_string']
    acc = hgvs.split(":")[0]
    sequence_id = "Sequence identifier not found"
    found = False
    with sqlite3.connect("sequence_identifiers.db") as db:
        cursor = db.cursor()
        cursor.execute("SELECT IDENTIFIER FROM Sequence_Identifiers WHERE ACCESSION=\'" + acc + "\'")
        rows = cursor.fetchall()
        for row in rows:
            found = True
            sequence_id = row[0]
    if found:
        hgvs_json = hgvs_conversion.from_hgvs(hgvs,sequence_id)
        return render_template('index.html', json_schema=json_schema, hgvs_json=hgvs_json)
    else:
        response = "No sequence identifier found for " + acc
        return render_template('index.html', json_schema=json_schema, hgvs_json=response)


# start the server with the 'run()' method
if __name__ == '__main__':
    APP.run(debug=True, host="0.0.0.0",port=8000)
