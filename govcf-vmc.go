package main

import "C"

import (
	"fmt"
	//"reflect"
	"os"
	"github.com/brentp/vcfgo"
	"github.com/brentp/xopen"
	"github.com/mwatkin8/copy_go-vmc/vmc"
	"log"
)

//export Transform
func Transform(filename string) {

	fh, err := xopen.Ropen("static/uploads/HG00177_sml.vcf")
	eCheck(err)
	defer fh.Close()

	rdr, err := vcfgo.NewReader(fh, false)

	// Add VMC INFO to the header.
	rdr.AddInfoToHeader("VMCGSID", "1", "String", "VMC Sequence identifier")
	rdr.AddInfoToHeader("VMCGLID", "1", "String", "VMC Location identifier")
	rdr.AddInfoToHeader("VMCGAID", "1", "String", "VMC Allele identifier")

	eCheck(err)
	defer rdr.Close()

	out := ""
    bundle := ""
	for {
		variant := rdr.Read()
		if variant == nil {
			break
		}

		// Check for alternate alleles.
		altAllele := variant.Alt()
		if len(altAllele) > 1 {
			log.Panicln("multiallelic variants found, please pre-run vt decomposes.")
		}

		// set variant line to build vmc
		record := vmc.VMCRecord(variant)

		//fmt.Println(record.Location)
		//fmt.Println(variant.String())

		out += ";VMCGSID=" + record.Location.Id + ";VMCGLID=" + record.Location.Interval + ";VMCGAID=" + record.Location.Sequence_id + "\n"
        bundle += record.Location.Id + "\t" + record.Location.Interval + "\t" + record.Location.Sequence_id + "\t" + record.Allele.Id + "\t" + record.Allele.State + "\t" +  "TEST_NM_000551.2" + "\t" + "NCBI" + "\n"
    }
	vcf_file, vcf_err := os.Create("go.vcf")
    if vcf_err != nil {
        log.Fatal("Cannot create file", vcf_err)
    }
    defer vcf_file.Close()
		fmt.Fprintf(vcf_file, out)

    bundle_file, bundle_err := os.Create("go.bundle")
    if bundle_err != nil {
        log.Fatal("Cannot create file", bundle_err)
    }
    defer bundle_file.Close()
        fmt.Fprintf(bundle_file, bundle)

	//fmt.Println(reflect.TypeOf(out))
	//return out
}

func main() {}

//export eCheck
func eCheck(p error) {
	if p != nil {
		panic(p)
	}
}
