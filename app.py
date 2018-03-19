from flask import Flask, flash, render_template, \
    request, redirect, send_from_directory
import vcf_transform, json_bundle, hgvs_conversion, re, os

# create the application object
APP = Flask(__name__, static_folder='static')
APP.secret_key = "vmcsuite"
APP.config['UPLOAD_FOLDER'] = 'static/uploads'

def get_upload(filename):
    """Returns the uploaded VCF file as a string"""
    with open("static/uploads/" + filename) as f_in:
        return f_in.read()

def get_vmc_vcf(filename):
    """Returns the transformed VCF file as a string"""
    with open(filename) as f_out:
        return f_out.read()

def get_json_schema():
    """Returns the example JSON schema file as a string"""
    with open("static/schema.json") as f_in:
        return f_in.read()

def get_json_bundle(filename):
    """Returns the transformed JSON file as a string"""
    with open(filename) as f_in:
        return f_in.read()

def get_filename():
    """Returns the name of the uploaded VCF file"""
    r = re.compile('.+.vcf')
    return list(filter(r.match, os.listdir("static/uploads")))[0]

def get_download_paths():
    """Creates paths to transformed VCF and JSON files ready for download"""
    r = re.compile('.+.vcf')
    filename = list(filter(r.match, os.listdir("static/uploads")))[0]
    json = "static/downloads/" + filename.split(".")[0] + ".json"
    vcf = "static/downloads/vmc_" + filename
    return json,vcf


@APP.route('/', methods=['GET', 'POST'])
def home():
    """
        Displays the example JSON schema, saves the uploaded VCF file to the uploads folder and then displays it as well.

    """
    json_schema = get_json_schema()
    if request.method == 'POST':
        #check if the post request has the file part
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        file.save(os.path.join(APP.config['UPLOAD_FOLDER'], file.filename))
        vcf_upload = get_upload(file.filename)
        #Displays uploaded VCF with example JSON
        return render_template('index.html',vcf_upload=vcf_upload,json_schema=json_schema)
    #Displays example JSON
    return render_template('index.html',json_schema=json_schema)


@APP.route('/vmc_vcf', methods=['GET', 'POST'])
def display_vmc_vcf():
    """
        Checks to see if the transformed VCF already exists in the downloads folder, generates it if not from transform.py, then displays it along with the
        example JSON schema and the original uploaded file. Also sends the filepath for downloading the transformed VCF file.
    """
    json_schema = get_json_schema()
    filename = get_filename()
    json_path,vmc_vcf_path = get_download_paths()
    vcf_upload = get_upload(filename)
    #Check if transformed VCF exists in downloads folder
    r = re.compile('.+.vcf')
    if filter(r.match, os.listdir("static/downloads")):
        vcf_transform.run(filename, vmc_vcf_path)
        vmc_vcf = get_vmc_vcf(vmc_vcf_path)
    else:
        vmc_vcf = get_vmc_vcf(vmc_vcf_path)
    return render_template('index.html', json_schema=json_schema, vcf_upload=vcf_upload, vmc_vcf=vmc_vcf, vmc_vcf_path=vmc_vcf_path)


@APP.route('/json_bundle', methods=['GET', 'POST'])
def display_json_bundle():
    """
        Checks to see if the transformed JSON already exists in the downloads folder, generates it if not from bundle.py, then displays it along with the
        example JSON schema and the original uploaded file. Also sends the filepath for downloading the transformed JSON file.

    """
    json_schema = get_json_schema()
    filename = get_filename()
    json_path,vmc_vcf_path = get_download_paths()
    vcf_upload = get_upload(filename)
    #Check if transformed JSON exists in downloads folder
    r = re.compile('.+.json')
    if filter(r.match, os.listdir("static/downloads")):
        json_bundle = get_json_bundle(json_path)
    else:
        json_bundle.run(filename, json_path)
        json_bundle = get_json_bundle(json_path)
    return render_template('index.html', json_schema=json_schema, vcf_upload=vcf_upload, json_bundle=json_bundle, json_path=json_path)


@APP.route('/hgvs', methods=['GET', 'POST'])
def hgvs_to_json():
    """
        Uses conversions.py to convert a HGVS string to a VMC JSON bundle and displays it along with the example JSON schema.

    """
    json_schema = get_json_schema()
    hgvs = request.form['hgvs_string']
    hgvs_json = hgvs_conversion.from_hgvs(hgvs)
    return render_template('index.html', json_schema=json_schema, hgvs_json=hgvs_json)


# start the server with the 'run()' method
if __name__ == '__main__':
    APP.run(debug=True, host="0.0.0.0",port=8000)
