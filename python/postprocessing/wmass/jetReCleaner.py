import ROOT
import os
import numpy as np
ROOT.PyConfig.IgnoreCommandLineOptions = True

from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
from PhysicsTools.NanoAODTools.postprocessing.tools import stringToLeafType

class JetReCleaner(Module):
    def __init__(self,label,jetCollection="Jet", particleCollection="Muon", deltaRforCleaning=0.4, variables=None):
        self.label = "_"+particleCollection+label
        self.jetCollection = jetCollection
        self.particleCollection = particleCollection
        self.deltaRforCleaning = deltaRforCleaning
        # will create new collection whose only variable is the id of the corresponding jet, so one can easily use the original collection but only
        # referencing cleaned jets (so all the original variables are available)
        # if convenient, new variables can be created (e.g. pt, eta, etc) in self.vars, for instance  as self.vars = ["pt", "eta"]
        self.jetidvar = "jetIdx"
        self.vars = [] if variables == None else [str(x) for x in variables]
        #
        if "jetReCleanerHelper.cc_cc.so" not in ROOT.gSystem.GetLibraries():
            print "Load C++ Worker"
            ROOT.gROOT.ProcessLine(".L %s/src/PhysicsTools/NanoAODTools/python/postprocessing/helpers/jetReCleanerHelper.cc+" % os.environ['CMSSW_BASE'])
        self._worker = ROOT.JetReCleanerHelper(self.deltaRforCleaning)
    def beginJob(self):
        pass
    def endJob(self):
        pass
    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.initReaders(inputTree) # initReaders must be called in beginFile
        self.out = wrappedOutputTree
        self.out.branch("n"+self.jetCollection+self.label, "i") # I is Int_t, i is UInt_t
        self.out.branch(self.jetCollection+self.label+"_"+self.jetidvar, "I", lenVar="n"+self.jetCollection+self.label)
        for V in self.vars:
            # get leaf type to keep the same with the new branch
            leafType = inputTree.GetLeaf(self.jetCollection+"_"+V).GetTypeName()
            ltype = stringToLeafType(leafType, setUnknownToDefault=False)
            self.out.branch(self.jetCollection+self.label+"_"+V, ltype, lenVar="n"+self.jetCollection+self.label)
    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass

    def initReaders(self,tree): # this function gets the pointers to Value and ArrayReaders and sets them in the C++ worker class
        # need generic name for jet collection attached to self, while the reader must be initialized with the proper collection
        setattr(self, "nPartToClean", tree.valueReader("n"+ self.particleCollection))
        setattr(self, "nJetDummy", tree.valueReader("n"+self.jetCollection))
        for B in "eta", "phi" : 
            setattr(self,"PartToClean_"+B, tree.arrayReader(self.particleCollection+"_"+B))
            setattr(self,"JetDummy_"+B, tree.arrayReader(self.jetCollection+"_"+B))

        self._worker.setLeptons(self.nPartToClean,self.PartToClean_eta,self.PartToClean_phi)
        self._worker.setJets(self.nJetDummy,self.JetDummy_eta,self.JetDummy_phi)
        for v in self.vars:
            if not hasattr(self,"JetDummy_"+v): setattr(self,"JetDummy_"+v, tree.arrayReader(self.jetCollection+"_"+v))
        self._ttreereaderversion = tree._ttreereaderversion # self._ttreereaderversion must be set AFTER all calls to tree.valueReader or tree.arrayReader

    def analyze(self, event):
        """process event, return True (go to next module) or False (fail, go to next event)"""
        ret={}
        jets = Collection(event,self.jetCollection)
        #isDataEvent = event.isData
        for V in self.vars:
            branch = getattr(self, "JetDummy_"+V)
            ret[self.jetCollection+self.label+"_"+V] = [getattr(j,V) for j in jets]
        if event._tree._ttreereaderversion > self._ttreereaderversion: # do this check at every event, as other modules might have read further branches
            self.initReaders(event._tree)
        # do NOT access other branches in python between the check/call to initReaders and the call to C++ worker code
        ## Algo
        cleanJets = self._worker.run()
        ## Output
        self.out.fillBranch('n'+self.jetCollection+self.label, len(cleanJets))
        self.out.fillBranch(self.jetCollection+self.label+"_"+self.jetidvar, [ int(j) for j in cleanJets ])
        for V in self.vars:
            self.out.fillBranch(self.jetCollection+self.label+"_"+V, [ ret[self.jetCollection+self.label+"_"+V][j] for j in cleanJets ])

        return True

# define modules using the syntax 'name = lambda : constructor' to avoid having them loaded when not needed

# label is added to original jetCollection name, e.g. if using "Jet" a new collection named "Jet_"+particleCollection+label is created
# one has to choose a collection of objects to clean the jets from (e.g. Muon to consider only jets not matched to muons)
# can be further developed to clean with respect to more collections, but for now it is not attempted
jetReCleaner = lambda : JetReCleaner(label="Clean", jetCollection="Jet", particleCollection="Muon", deltaRforCleaning=0.4)
#jetReCleaner_testVar = lambda : JetReCleaner(label="Clean", jetCollection="Jet", particleCollection="Muon", deltaRforCleaning=0.4, variables=["pt","eta","phi"])
