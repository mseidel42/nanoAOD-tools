import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True

from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection 
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module

class leptonSelection(Module):
    def __init__(self):
        pass
    def beginJob(self):
        pass
    def endJob(self):
        pass
    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree
        self.out.branch("GenPart_preFSRLepIdx1", "I")
        self.out.branch("GenPart_preFSRLepIdx2", "I")
        self.out.branch("genVtype", "I")
        
    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass
    def analyze(self, event):
        """process event, return True (go to next module) or False (fail, go to next event)"""

        genParticles = Collection(event, "GenPart")

        status746leptons = []
        otherleptons = []
        prefsrleptons =[]
        gPartIdx1=-99
        gPartIdx2=-99
        
        for i,g in enumerate(genParticles) :
            if ( abs(g.pdgId) < 11 or abs(g.pdgId) > 16 or g.genPartIdxMother < 0): ## only look at leptons. genPartIdx sometimes -1 for low-pt electrons
                continue
            if (abs(genParticles[g.genPartIdxMother].pdgId) in [23, 24]): ## this works for the new powheg samples
                if (g.status == 746):  ## status 746 is pre photos FSR in new powheg samples. so if they exist we want those.
                    status746leptons.append( (i,g) )
                else: # if they don't exist, we move to any leptons that have the W/Z as mother
                    otherleptons.append( (i,g) )
            else: ## in madgraph5_aMC@NLO there are some events without a W/Z, those have status 23 leptons (tested on >1M events)
                if (g.status == 23):
                    otherleptons.append( (i,g) )

            ## this code isn't used after all...
            #elif (g.status == 1 and ( (g.statusFlags  >> 8) & 1)): ## if those don't exist, take status 1 and the correct status flag
            #    otherleptons.append( (i,g) )

        if len(otherleptons) > 2:
            otherleptons = [i for i in otherleptons if ((i[1].statusFlags >> 8 ) & 1)]
            
        if   (len(status746leptons)) == 2:
            prefsrleptons=status746leptons
        elif (len(status746leptons) == 1 and len(otherleptons) == 1):
            prefsrleptons=status746leptons+otherleptons
        elif (len(status746leptons) == 0 and len(otherleptons) == 2):
            prefsrleptons=otherleptons

        prefsrleptons.sort(key = lambda x: x[1].pt, reverse=True ) #order by pt in decreasing order
        if not len(prefsrleptons) == 2:
            print 'found', len(prefsrleptons), 'leptons'
            print 'did not find exactly 2 proper leptons. check your code!'
            for (i,g) in status746leptons+otherleptons:
                print g.pdgId, g.pt, g.eta, g.status, g.statusFlags, genParticles[g.genPartIdxMother].pdgId
                
        gVtype=0
        ## save signed 11, 13, or 15 for the Vtype
        if len(prefsrleptons) == 0:
            pdg1, pdg2 = 0, 0
        elif len(prefsrleptons) == 1:
            pdg1, pdg2 = prefsrleptons[0][1].pdgId, 0
            gPartIdx1 = prefsrleptons[0][0]
            gVtype = pdg1     
        else:
            pdg1, pdg2 = prefsrleptons[0][1].pdgId, prefsrleptons[1][1].pdgId
            gPartIdx1 = prefsrleptons[0][0] if abs(prefsrleptons[0][1].pdgId) < 0 else prefsrleptons[1][0]
            gPartIdx2 = prefsrleptons[1][0] if abs(prefsrleptons[0][1].pdgId) < 0 else prefsrleptons[0][0]
            ## get sign of the odd-pdgid lepton and multiply by -1 to get the charge of the boson
            vcharge = -1*pdg1/abs(pdg1) if pdg1%2 else -1*pdg2/abs(pdg2)

            ## for the Z this will save the charge of the highest pT lepton. which is fair enough
            ## for splitting the dataset in two charges at random. if desired, uncomment the following
            ## two lines to save the charge as positive...
            ## if pdg1 == -1*pdg2: ## for the Z define charge as 1
            ##     vcharge = 1
            gVtype = vcharge*int((abs(pdg1)+abs(pdg2))/2.)

        ## some printouts for debugging
        ## print('======')
        ## for (i,g) in status746leptons+otherleptons:
        ##     print g.pdgId, g.pt, g.eta, g.status, g.statusFlags, genParticles[g.genPartIdxMother].pdgId

        self.out.fillBranch("genVtype", gVtype)
        self.out.fillBranch("GenPart_preFSRLepIdx1", gPartIdx1)
        self.out.fillBranch("GenPart_preFSRLepIdx2", gPartIdx2)
        

        return True


# define modules using the syntax 'name = lambda : constructor' to avoid having them loaded when not needed

genLeptonSelectModule = lambda : leptonSelection() 
 
