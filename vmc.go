//vmc.go
package vmc

import (
	"crypto/sha512"
	"encoding/base64"
	"fmt"
	"github.com/brentp/vcfgo"
	"time"
)

const Version = "v1.0.0"

// Define the VMC struct

type VMCID struct {
	Version    string
	Id         string
	DateTime   time.Time
	Identifier struct {
		Accession string
		Namespace string
	}
	Interval struct {
		Start uint32
		End   uint32
	}
	Location struct {
		Id          string
		Interval    string
		Sequence_id string
	}
	Allele struct {
		Id          string
		Location_id string
		State       string
	}
	Genotype struct {
		id            string
		haplotype_ids []string
		completedness int
	}
	Haplotype struct {
		id            string
		allele_id     []string
		completedness int
	}
}

// ------------------------- //
// VMC functions
// ------------------------- //

// TODO:
// method to build or get seq_id from file or db.

//export VMCRecord
func VMCRecord(v *vcfgo.Variant) *VMCID {

	vmc := VMCID{}
	vmc.Version = Version
	vmc.DateTime = time.Now()
	vmc.Identifier.Namespace = "VMC"

	// Collect values from the vcf read.
	vmc.Interval.Start = v.Start() - 1
	vmc.Interval.End = v.End() + 1
	vmc.Allele.State = v.Alt()[0]

	vmcLocation(&vmc)
	vmcAllele(&vmc)

	return &vmc
}

// ------------------------- //

//export vmcLocation
func vmcLocation(v *VMCID) {

	seqID := v.Location.Sequence_id
	intervalString := fmt.Sprint(v.Interval.Start) + ":" + fmt.Sprint(v.Interval.End)

	location := "<Location:<Identifier:" + seqID + ">:<Interval:" + intervalString + ">>"
	DigestLocation := VMCDigestId([]byte(location), 24)
	id := v.Identifier.Namespace + ":GL_" + DigestLocation

	// Set as dummy id
	v.Location.Sequence_id = v.Identifier.Namespace + ":GS_Ya6Rs7DHhDeg7YaOSg1EoNi3U_nQ9SvO"
	v.Location.Id = id
	v.Location.Interval = intervalString
}

// ------------------------- //

//export vmcAllele
func vmcAllele(v *VMCID) {

	v.Allele.Location_id = v.Location.Id
	state := v.Allele.State

	allele := "<Allele:<Identifier:" + v.Location.Id + ">:" + state + ">"
	DigestAllele := VMCDigestId([]byte(allele), 24)
	id := v.Identifier.Namespace + ":GA_" + DigestAllele

	v.Allele.Id = id
	v.Allele.Location_id = v.Location.Id
}

// ------------------------- //

//export VMCDigestId
func VMCDigestId(bv []byte, truncate int) string {
	hasher := sha512.New()
	hasher.Write(bv)

	sha := base64.URLEncoding.EncodeToString(hasher.Sum(nil)[:truncate])
	return sha
}

// ------------------------- //
