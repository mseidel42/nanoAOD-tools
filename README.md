# nanoAOD-tools
Tools for working with NanoAOD (requiring only python + root, not CMSSW)

## Checkout instructions

You need to setup python 2.7 and a recent ROOT version first.

    cmsrel CMSSW_10_6_18/
    cd CMSSW_10_6_18/src/
    cmsenv	   
    voms-proxy-init --voms cms
    source /cvmfs/cms.cern.ch/crab3/crab.sh
    git clone https://github.com/sroychow/nanoAOD-tools.git PhysicsTools/NanoAODTools
    cd PhysicsTools/NanoAODTools
    git checkout wmassul
    scram b -j 8

## Run local tests

The basic syntax of the command is the following:

    cd python/wmass/
    python postproc.py --isMC 1 --passall 0 --dataYear 2016 --runPeriod B --jesUncert Total --redojec 1 --maxEvents 1000 --genOnly 1
    # all possible configuarations can be run with ./run_test.sh

Here is a summary of its features:
* the `--isMC` option is `1` when running on MC and `0` otherwise.
* the `--passall` option set to `1` makes the postprocessor run on every event. It is `0` by default.
* the `--dataYear` option refers to the run era. Currently accepted values are `2016` and `2017`.
* the `--runPeriod` option is used only for `--isMC=0`. Needed to map the correct JEC file.
* the `--jesUncert` option sets the level of JES uncertainty splitting. `Total` is the default.
* the `--redojec` option set to `1` re-runs the JEC on all jets and propagates it to the MET.
* the `--maxEvents` option pre-selects a certaint number of events for fast checks.
* the `--genOnly` option will produce ntuples with gen-level only information and no skim

## Run on crab

The basic syntax of the command is the following:

    cd crab/
    python crab_cfg.py --isMC 1 --dataYear 2016 --tag TEST --redojec 0 --run debug --genOnly 1

Here is a summary of its features:
* the `--isMC` option is `1` when running on MC and `0` otherwise.
* the `--dataYear` option refers to the run era. Currently accepted values are `2016`, `2017`, `2018`.
* the `--tag` option flags a given production. The output files will be stored under `/gpfs/ddn/srm/cms/store/user/USERNAME/NanoAODYY-ZZ`, with `YY`=`dataYear` and `ZZ`=`tag`
* the `--redojec` option set to `1` re-runs the JEC on all jets and propagates it to the MET.
* the `--run` option can be either `debug` (execute script, do not call crab), `dryrun` (execute script, execute `crab --dryrun submit` for a local test of the task), and `submit` (execute script, execute `crab submit`)
* the `--genOnly` option will produce ntuples with gen-level only information and no skim

The output is a text file called `postcrab_XXsamples_YY_ZZ.txt` with `XX`=`data`,`mc`, `YY`=`2016`,`2017`, and 'ZZ'=tag

## Post-crab

After the crab submission has finished, the following script harvests the production and runs `haddnano.py`:

      cd crab/ 
      python postjob.py --tag TEST --isMC 1 --dataYear 2016 --run shell --pushback 0

The script assumes that the file `postcrab_XXsamples_YY_ZZ.txt` is present.
Here is a summary of its features:
* the `--isMC` option is `1` when running on MC and `0` otherwise.
* the `--dataYear` option refers to the run era. Currently accepted values are `2016` and `2017`.
* the `--tag` option flags a given production. The output files are to be found under `/gpfs/ddn/srm/cms/store/user/USERNAME/NanoYY-ZZ`, with `YY`=`dataYear` and `ZZ`=`tag`
* the `--run` option can be either `shell` (interactive running) or `batch` (one job per sample will be run in the lsbatch).
* the `--pushback` option set to `1` will use the scratch space as a temporary space for hadding the files, and then force the hadded file to be pushed back to the SRM. The scratch space is then cleaned. If `0`, the hadded file will remain in the scratch space under `/gpfs/ddn/cms/user/USERNAME/NanoAODYY-ZZ` 
