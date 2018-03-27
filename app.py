from flask import Flask, flash, render_template, \
    request, redirect, send_from_directory, make_response
import vcf_transform, json_bundle, hgvs_conversion, re, os
from werkzeug.contrib.cache import FileSystemCache

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
        cache.set(file.filename, file.read(), timeout=604800000)
        #Displays uploaded VCF with example JSON
        r = make_response(render_template('index.html',vcf_upload=file.read(),json_schema=json_schema))
        r.set_cookie("filename", file.filename)
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
    filename = get_filename()
    if not cache.has(filename):
            return render_template('index.html', json_schema=json_schema, vcf_upload="No file uploaded", vmc_vcf="No file uploaded")
    vcf_upload = cache.get(filename)
    #Check if transformed VCF exists in the cache
    if not cache.has("vmc." + filename):

        #Use subprocess command to call his command line tool for the transformed VCF
        vmc_vcf = vcf_transform.run(filename)
        cache.set("vmc." + filename, vmc_vcf, timeout=604800000)

    else:
        vmc_vcf = cache.get("vmc." + filename)
    return render_template('index.html', json_schema=json_schema, vcf_upload=vcf_upload, vmc_vcf=vmc_vcf)

@APP.route('/vmc_vcf_download')
def serve_vmc_vcf():
    filename = "vmc." + get_filename()
    if cache.has(filename):
        response = make_response(open(cache.get(filename)).read())
        response.headers = ("Content-Disposition", "attachment; filename=" + filename )
        return response

@APP.route('/json_bundle', methods=['GET', 'POST'])
def display_json_bundle():
    """
        Checks to see if the transformed JSON already exists in the downloads folder, generates it if not from bundle.py, then displays it along with the
        example JSON schema and the original uploaded file. Also sends the filepath for downloading the transformed JSON file.

    """
    json_schema = get_json_schema()
    filename = get_filename()
    if not cache.has(filename):
            return render_template('index.html', json_schema=json_schema, vcf_upload="No file uploaded", vcf_json="No file uploaded")
    vcf_upload = cache.get(filename)
    #Check if transformed JSON exists in the cache
    if not cache.has(filename[0:-4] + '.json'):
        vcf_json = json_bundle.run(filename)
        cache.set(filename[0:-4] + '.json', vcf_json, timeout=604800000)
    else:
        vcf_json = cache.get(filename[0:-4] + '.json')
    return render_template('index.html', json_schema=json_schema, vcf_upload=vcf_upload, vcf_json=vcf_json)

@APP.route('/vcf_json_download')
def serve_vcf_json():
    filename = get_filename()[0:-4] + ".json"
    if cache.has(filename):
        response = make_response(open(cache.get(filename)).read())
        response.headers = ("Content-Disposition", "attachment; filename=" + filename )
        return response

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
