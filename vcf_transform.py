from ctypes import cdll
import os

def parse_ids():
    """
        Returns a list of the new VMC identifiers from go.vcf which is an intermediary file created from the Golang transformation code in govcf.go.

    """
    id_list = []
    with open('go.vcf', 'r') as go_vcf:
        for line in go_vcf:
            id_list.append(line.strip())
    return id_list

def parse_info(filename):
    """
        Parses the header information from the uploaded VCF and adds INFO entries to the meta-information section. Gets the new VMC identifiers from parse_ids()
        and adds them to the info fields of the variants. Combines the header information with the updated variants.

    """
    in_path = 'static/uploads/' + filename
    with open(in_path) as transform:
        header = ''
        cols = ''
        id_list = parse_ids()
        idx = 0
        variants = ""
        for line in transform:
            if line[1] == '#':
                header += line
            elif line[0] == '#':
                cols += line
                header += """##INFO=<ID=VMCGSID,Number=1,Type=String,Description="VMC Sequence identifier">\n""" \
                    + """##INFO=<ID=VMCGLID,Number=1,Type=String,Description="VMC Location identifier">\n""" \
                    + """##INFO=<ID=VMCGAID,Number=1,Type=String,Description="VMC Allele identifier">\n"""
            else:
                line_list = line.split('\t')
                print(line_list)
                var = line_list[0] + '\t' + line_list[1] + '\t' + line_list[2] + '\t' + line_list[3] + '\t' + line_list[4] + '\t' + \
                line_list[5] + '\t' + line_list[6] + '\t' + line_list[7] + id_list[idx] + '\t' + line_list[8] + '\t' + line_list[9]

                variants += var
                idx += 1
        return header + cols + variants

def run(filename, out_path):
    """
        Calls the Go code which creates the VMC identifiers in the intermediary file go.vcf.
        It then calls parse() to gather the updated file, transforms it, and writes it to the download folder with the prefic vmc_.

    """
    vmc_lib = cdll.LoadLibrary('./govcf-vmc.so')
    print('Generating the VMC unique IDs')
    vmc_lib.Transform(filename)
    #Write out to transformed file that the user can download
    with open(out_path, 'w') as out:
        out.write(parse_info(filename))
