
# VMC Test Suite

The Variant Modelling Collaboration (VMC) has developed both a standard representation format for DNA and RNA variants as well as an algorithm for generating unique identifiers based on that representation format. The notation, reference build used, and many other aspects of the new representation format are fed into this hash-bashed digest algorithm which will generate a unique identifier. If two variants are identical and are being correctly formatted to the new VMC standard, then the algorithm will generate matching identifiers. This is important because it allows for institution A to share variant information with institution B with institution B being able to compare their VMC identifiers with those provided from institution A. If they are identical then both institutions can be sure that they are talking about the exact same variant. This standard also opens the door for a variety of research and clinical tools which rely on consistent data representation.

This web tool is designed to perform the following functions:
### With a user-uploaded VCF file
    -Add VMC unique identifiers for each variant, and return the transformed file to the user.
    -Return a VMC bundle (represented in JSON) which contains identifiers for all variants in the VCF file.

### Without a user-uploaded VCF file
    -Return a VMC bundle (represented in JSON) which contains identifiers for a user-entered HGVS expression.
    -Validate a user-entered VMC identifier to ensure proper implementation of the VMC specification.
