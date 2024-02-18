#!/usr/bin/env python
import os, sys
import ROOT
import argparse
import subprocess

ROOT.PyConfig.IgnoreCommandLineOptions = True
from importlib import import_module
from PhysicsTools.NanoAODTools.postprocessing.framework.postprocessor import PostProcessor

from PhysicsTools.NanoAODTools.postprocessing.modules.common.puWeightProducer import *
from PhysicsTools.NanoAODTools.postprocessing.modules.jme.jetmetUncertainties import *
from PhysicsTools.NanoAODTools.postprocessing.modules.jme.jetRecalib import *
from PhysicsTools.NanoAODTools.postprocessing.modules.jme.jetmetHelperRun2 import *
from PhysicsTools.NanoAODTools.postprocessing.modules.common.muonScaleResProducer import *
from PhysicsTools.NanoAODTools.postprocessing.modules.common.PrefireCorr import *

from PhysicsTools.NanoAODTools.postprocessing.wmass.preSelection import *
from PhysicsTools.NanoAODTools.postprocessing.wmass.CSVariables import *
from PhysicsTools.NanoAODTools.postprocessing.wmass.Wproducer import *
from PhysicsTools.NanoAODTools.postprocessing.wmass.genLepSelection import *
from PhysicsTools.NanoAODTools.postprocessing.wmass.lheWeightsFlattener import *
from PhysicsTools.NanoAODTools.postprocessing.wmass.massWeightsCorrection import *

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

parser = argparse.ArgumentParser("")
parser.add_argument('-jobNum',    '--jobNum',   type=int, default=1,      help="")
parser.add_argument('-crab',      '--crab',     type=int, default=0,      help="")
parser.add_argument('-passall',   '--passall',  type=int, default=0,      help="")
parser.add_argument('-isMC',      '--isMC',     type=int, default=1,      help="")
parser.add_argument('-maxEvents', '--maxEvents',type=int, default=-1,	  help="")
parser.add_argument('-dataYear',  '--dataYear', type=int, default=2016,   help="")
parser.add_argument('-jesUncert', '--jesUncert',type=str, default="Total",help="")
parser.add_argument('-redojec',   '--redojec',  type=int, default=0,      help="")
parser.add_argument('-runPeriod', '--runPeriod',type=str, default="B",    help="")
parser.add_argument('-genOnly',    '--genOnly',type=int, default=0,    help="")
parser.add_argument('-trigOnly',    '--trigOnly',type=int, default=0,    help="")
parser.add_argument('-iFile',    '--iFile',type=str, default="",    help="")

args = parser.parse_args()
isMC      = args.isMC
crab      = args.crab
passall   = args.passall
dataYear  = args.dataYear
maxEvents = args.maxEvents
runPeriod = args.runPeriod
redojec   = args.redojec
jesUncert = args.jesUncert
genOnly   = args.genOnly
trigOnly  = args.trigOnly
inputFile=args.iFile
 
print "isMC =", bcolors.OKBLUE, isMC, bcolors.ENDC, \
    "genOnly =", bcolors.OKBLUE, genOnly, bcolors.ENDC, \
    "crab =", bcolors.OKBLUE, crab, bcolors.ENDC, \
    "passall =", bcolors.OKBLUE, passall,  bcolors.ENDC, \
    "dataYear =",  bcolors.OKBLUE,  dataYear,  bcolors.ENDC, \
    "maxEvents =", bcolors.OKBLUE, maxEvents, bcolors.ENDC 

if genOnly and not isMC:
    print "Cannot run with --genOnly=1 option and data simultaneously"
    exit(1)
if trigOnly and not isMC:
    print "Cannot run with --trigOnly=1 option and data simultaneously"
    exit(1)

# run with crab
if crab:
    from PhysicsTools.NanoAODTools.postprocessing.framework.crabhelper import inputFiles,runsAndLumis

################################################ JEC
#Function definition
#createJMECorrector(isMC=True, dataYear=2016, runPeriod="B", jesUncert="Total", jetType="AK4PFchs", noGroom=False,
#                   metBranchName="MET", applySmearing=True, isFastSim=False, applyHEMfix=False, splitJER=False, saveMETUncs=['T1', 'T1Smear'])

jmeCorrections = createJMECorrector(isMC=isMC, dataYear=dataYear, runPeriod=runPeriod, jesUncert=jesUncert, jetType="AK4PFchs", noGroom=False, 
                                    metBranchName="MET", applySmearing=True, isFastSim=False, applyHEMfix=False, splitJER=False, 
                                    saveMETUncs=['T1', 'T1Smear'])
################################################ PU
#pu reweight modules
puWeightProducer = puWeight_2016
if dataYear==2017:
    puWeightProducer = puWeight_2017
elif dataYear==2018:
    puWeightProducer = puWeight_2018

################################################ Muons
#Rochester correction for muons
muonScaleRes = muonScaleRes2016
if dataYear==2017:
    muonScaleRes = muonScaleRes2017
elif dataYear==2018:
    muonScaleRes = muonScaleRes2018
    #print bcolors.OKBLUE, "No module %s will be run" % "muonScaleRes", bcolors.ENDC
################################################ GEN
Wtypes = ['bare', 'preFSR', 'dress']
################################################PREFIRE Weights
jetROOT='L1prefiring_jetpt_2016BtoH'
photonROOT='L1prefiring_photonpt_2016BtoH'
if dataYear == 2017: 
    jetROOT='L1prefiring_jetpt_2017BtoF'
    photonROOT='L1prefiring_photonpt_2017BtoF'
prefireCorr= lambda : PrefCorr(jetroot=jetROOT + '.root', jetmapname=jetROOT, photonroot=photonROOT + '.root', photonmapname=photonROOT)
################################################

##This is temporary for testing purpose
#input_dir = "/gpfs/ddn/srm/cms/store/"
input_dir = "root://cms-xrd-global.cern.ch//eos/cms/store/"

ifileMC = ""
if dataYear==2016:
    ifileMC="/cmst3/group/wmass/w-mass-13TeV/NanoAOD/DYJetsToMuMu_M-50_TuneCP5_13TeV-powhegMiNNLO-pythia8-photos/NanoAODv7/201025_173845/0000/SMP-RunIISummer16NanoAODv7-00336_1.root"
elif dataYear==2017:
    ifileMC = "mc/RunIIFall17NanoAODv5/WJetsToLNu_Pt-50To100_TuneCP5_13TeV-amcatnloFXFX-pythia8/NANOAODSIM/PU2017_12Apr2018_Nano1June2019_102X_mc2017_realistic_v7-v1/20000/B1929C77-857F-CA47-B352-DE52C3D6F795.root"
elif dataYear==2018:
    ifileMC = "mc/RunIIAutumn18NanoAODv5/WJetsToLNu_Pt-50To100_TuneCP5_13TeV-amcatnloFXFX-pythia8/NANOAODSIM/Nano1June2019_102X_upgrade2018_realistic_v19-v1/100000/FEF8F001-02FD-E449-B1FC-67C8653CDCEC.root"

ifileDATA = ""
if not isMC: 
    input_dir = 'root://xrootd.ba.infn.it//store/'
    if dataYear==2016:
        ifileDATA = "/data/Run2016C/SingleMuon/NANOAOD/Nano25Oct2019-v1/40000/F7FC207B-943C-3B48-9147-D83B838BE473.root"
    elif dataYear==2017:
        ifileDATA = "data/Run2017F/BTagCSV/NANOAOD/Nano1June2019-v1/40000/030D3C6F-240B-3247-961D-1A7C0922DC1F.root"
    elif dataYear==2018:
        ifileDATA = "data/Run2018B/DoubleMuon/NANOAOD/Nano1June2019-v1/40000/20FCA3B4-6778-7441-B63C-307A21C7C2F0.root"

input_files = []
modules = []
if isMC:
    if inputFile == '' :     #this will run on the hardcoded file above
        input_files.append( input_dir + ifileMC )
    else : input_files.append( inputFile )
    if (not genOnly and not trigOnly):
        modules = [puWeightProducer(), 
                    preSelection(isMC=isMC, passall=passall, dataYear=dataYear),  
                    prefireCorr(),
                    jmeCorrections(),
	                genLeptonSelectModule(),
		            CSAngleModule(), 
	                WproducerModule(),
	                flattenLheWeightsModule(),
                    correctMassWeightsModule(),
                   ]
        # add before recoZproducer
        if muonScaleRes!= None: modules.insert(3, muonScaleRes())
    elif genOnly: 
        modules = [genLeptonSelectModule(),
                   CSAngleModule(),
                   WproducerModule()
               ]
    elif trigOnly: 
        modules = [puWeightProducer(),preSelection(isMC=True, passall=passall, dataYear=dataYear, trigOnly=True)]
    else:
        modules = []
else:
    if inputFile == '' : #this will run on the hardcoded file above     
        input_files.append( input_dir + ifileDATA )
    else : input_files.append( inputFile )
    modules = [preSelection(isMC=isMC, passall=passall, dataYear=dataYear), 
               ]
    if jmeCorrections!=None: modules.insert(1,jmeCorrections())
    if muonScaleRes!=None:   modules.insert(1, muonScaleRes())

treecut = ("Entry$<" + str(maxEvents) if maxEvents > 0 else None)
kd_file = "keep_and_drop"
if isMC:
    kd_file += "_MC"
    if genOnly: kd_file+= "GenOnly"
    elif trigOnly: kd_file+= "TrigOnly"
else:
    kd_file += "_Data"
kd_file += ".txt"

print "Keep drop file used:", kd_file

p = PostProcessor(outputDir=".",  
                  inputFiles=(input_files if crab==0 else inputFiles()),
                  cut=treecut,      
                  modules=modules,
                  provenance=True,
                  outputbranchsel=kd_file,
                  fwkJobReport=(False if crab==0 else True),
                  jsonInput=(None if crab==0 else runsAndLumis()),
                  compression="LZMA:9"
                  )
p.run()

print "DONE"
# os.system("ls -lR")
