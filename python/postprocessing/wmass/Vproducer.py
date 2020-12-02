import ROOT
import math
ROOT.PyConfig.IgnoreCommandLineOptions = True

from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection 
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module

def getVvariables(muon, neutrino):

    m = ROOT.TLorentzVector()
    n = ROOT.TLorentzVector()
    w = ROOT.TLorentzVector()
        
    m.SetPtEtaPhiM(muon.pt, muon.eta, muon.phi, 0.105)
    n.SetPtEtaPhiM(neutrino.pt, neutrino.eta, neutrino.phi, 0.)
        
    w = m + n

    return w.Pt(), w.Rapidity(), w.Phi(), w.M()


class Vproducer(Module):
    def __init__(self):
        pass
    def beginJob(self):
        pass
    def endJob(self):
        pass
    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree
        
        self.out.branch("Vpt_preFSR", "F")
        self.out.branch("Vrap_preFSR", "F")
        self.out.branch("Vphi_preFSR", "F")
        self.out.branch("Vmass_preFSR", "F")
        
    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass

    def analyze(self, event):
        """process event, return True (go to next module) or False (fail, go to next event)"""

        genParticles = Collection(event, "GenPart")

        # reobtain the indices of the good muons and the neutrino
        
        preFSRLepIdx1 = event.GenPart_preFSRLepIdx1
        preFSRLepIdx2 = event.GenPart_preFSRLepIdx2

        if preFSRLepIdx1 >= 0 and preFSRLepIdx2 >= 0:
            Vpt_preFSR, Vrap_preFSR, Vphi_preFSR, Vmass_preFSR = getVvariables(genParticles[preFSRLepIdx1], genParticles[preFSRLepIdx2])
        else:
            Vpt_preFSR, Vrap_preFSR, Vphi_preFSR, Vmass_preFSR = -999., -999., -999., -999.

        event.massV = Vmass_preFSR

        self.out.fillBranch("Vpt_preFSR",Vpt_preFSR)
        self.out.fillBranch("Vrap_preFSR",Vrap_preFSR)
        self.out.fillBranch("Vphi_preFSR",Vphi_preFSR)
        self.out.fillBranch("Vmass_preFSR",Vmass_preFSR)

        return True


# define modules using the syntax 'name = lambda : constructor' to avoid having them loaded when not needed

VproducerModule = lambda : Vproducer() 
