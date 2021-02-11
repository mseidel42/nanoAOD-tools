import ROOT
import math
ROOT.PyConfig.IgnoreCommandLineOptions = True

from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection 
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module

def muonPassSelection(mu, skipIsolation=False):
    # this might be looser than the actual analysis selection, to be more flexible
    if mu.pt > 24 and mu.mediumId == 1 and (skipIsolation or mu.pfRelIso04_all < 0.15) and abs(mu.dxy) < 0.05 and abs(mu.dz) < 0.2:
        return True
    else:
        return False

class skimmer(Module):
    def __init__(self, isWlike=False):
        self.isWlike = isWlike
    def beginJob(self):
        pass
    def endJob(self):
        pass
    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass
    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass
    def analyze(self, event):
        """process event, return True (go to next module) or False (fail, go to next event)"""

        # Muon selection
        all_muons = Collection(event, "Muon")
        nMuons = len(all_muons)
        pass_muons = [mu for mu in all_muons if muonPassSelection(mu, skipIsolation=True)]
        if self.isWlike:
            if nMuons < 2: return False
            # require that at least two muons pass the selection except isolation
            if len(pass_muons) < 2: return False
        else:
            if nMuons < 1: return False
            # require that at least one muon passes the selection except isolation
            if len(pass_muons) < 1: return False

        return True

# define modules using the syntax 'name = lambda : constructor' to avoid having them loaded when not needed

skimmerWmassModule = lambda : skimmer(isWlike=False) 
skimmerWlikeModule = lambda : skimmer(isWlike=True) 
