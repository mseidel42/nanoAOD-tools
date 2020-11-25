#!/bin/bash

cd [PWD]
mkdir tmp/[MODEL]/
cd tmp/[MODEL]/
cp [GRIDPACK] .
tar -xvf *.tar.xz
sh runcmsgrid.sh 1 123456 1

source /cms/cmsset_default.sh
cd ./CMSSW_9_3_16/src/
cmsenv

rwgt_dir="[PWD]/tmp/[MODEL]/process/rwgt"
export PYTHONPATH=$rwgt_dir:$PYTHONPATH

cd [PWD]/tmp/[MODEL]/process/
cp [EVENTSFILE] [PWD]/tmp/[MODEL]/process/Events/cmsgrid/events.lhe.gz

echo "0" | ./bin/aMCatNLO reweight cmsgrid 
cp [PWD]/tmp/[MODEL]/process/Events/cmsgrid/events.lhe.gz [OUTPUT].gz

# Cleanup
cd [PWD]
rm -rf ./tmp/[MODEL]/
