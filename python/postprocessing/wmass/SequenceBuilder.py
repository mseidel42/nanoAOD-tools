#!/usr/bin/env python
import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True
from importlib import import_module
#these are POG modules
from PhysicsTools.NanoAODTools.postprocessing.framework.postprocessor import PostProcessor
from PhysicsTools.NanoAODTools.postprocessing.modules.common.puWeightProducer import *
from PhysicsTools.NanoAODTools.postprocessing.modules.jme.jetmetHelperRun2 import *
from PhysicsTools.NanoAODTools.postprocessing.modules.common.muonScaleResProducer import *
from PhysicsTools.NanoAODTools.postprocessing.modules.common.PrefireCorr import *
##these are our custom modules
from PhysicsTools.NanoAODTools.postprocessing.wmass.preSelection import *
from PhysicsTools.NanoAODTools.postprocessing.wmass.CSVariables import *
from PhysicsTools.NanoAODTools.postprocessing.wmass.Vproducer import *
from PhysicsTools.NanoAODTools.postprocessing.wmass.genLepSelection import *
from PhysicsTools.NanoAODTools.postprocessing.wmass.lheWeightsFlattener import *
from PhysicsTools.NanoAODTools.postprocessing.wmass.triggerMatchProducer import *
from PhysicsTools.NanoAODTools.postprocessing.wmass.jetReCleaner import *

class SequenceBuilder:
    def __init__(self, isMC, dataYear, runPeriod, jesUncert, eraVFP, passall, genOnly, addOptional):
        self.isMC=isMC
        self.dataYear=dataYear
        self.runPeriod=runPeriod
        self.jesUncert=jesUncert
        self.passall=passall
        self.genOnly = genOnly
        self.eraVFP = eraVFP
        self.addOptional = addOptional
        self.modules=[]
            
    #this sequence will always be run
    def makeBaselineSequence(self):
        ################################################ JEC
        #Function definition
        #createJMECorrector(isMC=True, dataYear=2016, runPeriod="B", jesUncert="Total", jetType="AK4PFchs", noGroom=False,
        #metBranchName="MET", applySmearing=True, isFastSim=False, applyHEMfix=False, splitJER=False, saveMETUncs=['T1', 'T1Smear'])
        jmeCorrections = createJMECorrector(isMC=self.isMC, dataYear=self.dataYear, runPeriod=self.runPeriod, 
                                            jesUncert=self.jesUncert, jetType="AK4PFchs", noGroom=False, 
                                            metBranchName="MET", applySmearing=True, isFastSim=False, 
                                            applyHEMfix=False, splitJER=False, 
                                            saveMETUncs=['T1', 'T1Smear'])

        ################################################ Muons
        #Rochester correction for muons
        muonScaleRes = muonScaleRes2016
        if self.dataYear==2017:
            muonScaleRes = muonScaleRes2017
        elif self.dataYear==2018:
            muonScaleRes = muonScaleRes2018
        
        #base path which will always be run for data & mc
        basePath=[preSelection(isMC=self.isMC, passall=self.passall, dataYear=self.dataYear),  
                  muonTriggerMatchProducer(saveIdTriggerObject=False, deltaRforMatch=0.3, minNumberMatchedMuons=0),
                  muonScaleRes(), 
                  jmeCorrections()
        ]
        return basePath
                 

    def appendMCweightsSequence(self):
        ################################################ PU
        #pu reweight modules
        puWeightProducer_allData = puWeight_UL2016_allData
        puWeightProducer         = puWeight_UL2016_postVFP if self.eraVFP == "postVFP" else puWeight_UL2016_preVFP
        if self.dataYear==2017:
            puWeightProducer = puWeight_2017
        elif self.dataYear==2018:
            puWeightProducer = puWeight_2018
            
        ################################################PREFIRE Weights
        jetROOT='L1prefiring_jetpt_2016BtoH'
        photonROOT='L1prefiring_photonpt_2016BtoH'
        if self.dataYear == 2017: 
            jetROOT='L1prefiring_jetpt_2017BtoF'
            photonROOT='L1prefiring_photonpt_2017BtoF'
        prefireCorr= lambda : PrefCorr(jetroot=jetROOT + '.root', jetmapname=jetROOT, photonroot=photonROOT + '.root', photonmapname=photonROOT)

        ################################################

        mcweights=[puWeightProducer_allData(), 
                   puWeightProducer(), 
                   prefireCorr(), 
        ]
        return mcweights
            
    #list of modules that will be run only for MC
    def appendGenSequence(self):
        genmodules=[genLeptonSelectModule(), 
                    CSAngleModule(), 
                    VproducerModule(), 
                    flattenLheWeightsModule()]

        return genmodules

    #list of optional or test modules
    def appendOptionalSequence(self):
        optionals=[JetReCleaner(label="Clean", jetCollection="Jet", particleCollection="Muon", deltaRforCleaning=0.4)]

        return optionals

    def buildFinalSequence(self):
        if (not self.genOnly):
            self.modules.extend(self.makeBaselineSequence())
            
            if self.isMC :
                self.modules.extend(self.appendMCweightsSequence())
                self.modules.extend(self.appendGenSequence())
                
            if self.addOptional:
                self.modules.extend(self.appendOptionalSequence())
            
        elif self.genOnly: 
          self.modules.extend(self.appendGenSequence())

        return self.modules
