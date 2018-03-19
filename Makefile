all:
	go get "github.com/brentp/vcfgo"
	go get "github.com/brentp/xopen"
	go get "github.com/mwatkin8/copy_go-vmc/vmc"
	go build -buildmode=c-shared -o govcf-vmc.so govcf-vmc.go
