import ROOT
import math
ROOT.PyConfig.IgnoreCommandLineOptions = True

from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection 
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module

##Trigger object matching
def matches_any(mu,trigs,R):
    for t in trigs:        
        dR = math.sqrt((mu.eta-t.eta)**2 + math.acos(math.cos(mu.phi-t.phi))**2) 
        if dR<=R: return True
    return False

def isTriggerObjMatched(mu, trigs, R):
    for t in trigs:        
        dR = math.sqrt((mu.eta - t.eta)**2 + math.acos(math.cos(mu.phi - t.phi))**2) 
        if dR<=R: return True
    return False

###NOTE: basic cut on pT, eta, dxy, dz
def fiducial_muon(mu):
    return (abs(mu.eta)<2.4 and mu.pt>10 and abs(mu.dxy)<0.05 and abs(mu.dz)<0.2)

##NOTE: LooseId + iso
def loose_muon_id(mu):
    return (fiducial_muon(mu) and mu.isPFcand and mu.pfRelIso04_all< 0.25 and mu.pt>15)

##NOTE: LooseId only
def loose_muon_idonly(mu):
    return (fiducial_muon(mu) and mu.isPFcand and mu.pt>15)

##NOTE: MediumId + iso
def medium_muon_id(mu):
    return (fiducial_muon(mu) and mu.mediumId and mu.pfRelIso04_all<=0.15 and mu.pt>20)

##NOTE: MediumId only
def medium_muon_idonly(mu):
    return (fiducial_muon(mu) and mu.mediumId and mu.pt>20)

##NOTE: MediumId + antiIsolated
def medium_aiso_muon_id(mu):
    return (fiducial_muon(mu) and mu.mediumId and mu.pfRelIso04_all> 0.15 and mu.pt>20)

##NOTE: Tag muon
def tag_muon(mu):
    return (fiducial_muon(mu) and mu.tightId and mu.pfRelIso04_all< 0.20 and mu.pt>26)

##NOTE: Probe muon for trk->Id&Iso
def probe_muon_Trk(mu):
    return (abs(mu.eta)<2.4 and mu.pt>20 and abs(mu.dxy)<0.2 and abs(mu.dz)<0.5 and mu.isTracker)

##NOTE: Probe muon for trk&Id&Iso->Trig
def probe_muon_TrkIdIso(mu):
    return (probe_muon_Trk(mu) and medium_muon_id(mu))

##NOTE: Probe muon for trk&Id&IsoLoose->Trig
def probe_muon_TrkIdIsoLoose(mu):
    return (probe_muon_Trk(mu) and loose_muon_id(mu))

##Veto against electron
def veto_electron_id(ele):
    etaSC = ele.eta + ele.deltaEtaSC
    if (abs(etaSC) <= 1.479):
        return (ele.pt>10 and abs(ele.dxy)<0.05 and abs(ele.dz)<0.1 and ele.cutBased>=1 and ele.pfRelIso03_all< 0.30)
    else:
        return (ele.pt>10 and abs(ele.dxy)<0.10 and abs(ele.dz)<0.2 and ele.cutBased>=1 and ele.pfRelIso03_all< 0.30)

class preSelection(Module):
    def __init__(self, isMC=True, passall=False, dataYear=2016, trigOnly=False):
        self.isMC = isMC
        self.passall = passall
        self.dataYear = str(dataYear)
        self.trigOnly = trigOnly

        # baded on https://twiki.cern.ch/twiki/bin/view/CMS/MissingETOptionalFiltersRun2
        # val = 2*(IS FOR DATA) + 1*(IS FOR MC)
        self.met_filters = {
            "2016": { "goodVertices" : 3,
                      "globalSuperTightHalo2016Filter": 3,
                      "HBHENoiseFilter": 3,
                      "HBHENoiseIsoFilter" : 3,
                      "EcalDeadCellTriggerPrimitiveFilter": 3,
                      "BadPFMuonFilter": 3,
                      },
            "2017": { "goodVertices": 3,
                      "globalSuperTightHalo2016Filter": 3,
                      "HBHENoiseFilter": 3,
                      "HBHENoiseIsoFilter": 3,
                      "EcalDeadCellTriggerPrimitiveFilter": 3,
                      "BadPFMuonFilter": 3,
                      #"BadChargedCandidateFilter": 3,
                      #"eeBadScFilter" : 2,
                      #"ecalBadCalibFilter": 3, # needs to be rerun
                      },
            "2018": { "goodVertices": 3,
                      "globalSuperTightHalo2016Filter": 3,
                      "HBHENoiseFilter": 3,
                      "HBHENoiseIsoFilter": 3,
                      "EcalDeadCellTriggerPrimitiveFilter": 3,
                      "BadPFMuonFilter" : 3,
                      #"BadChargedCandidateFilter" : 3,
                      #"eeBadScFilter" : 2,
                      #"ecalBadCalibFilter": 3,  # needs to be rerun 
                      },
            }
        pass
    def beginJob(self):
        pass
    def endJob(self):
        pass
    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree
        self.out.branch("HLT_SingleMu24", "B", title="Event passes OR of HLT triggers at 24 GeV")
        self.out.branch("HLT_SingleMu27", "B", title="Event passes OR of HLT triggers at 27 GeV")
        self.out.branch("Idx_mu1", "I", title="index of W-like muon / index of Z-like 1st muon")
        self.out.branch("Idx_mu2", "I", title="index of Z-like 2nd muon")
        self.out.branch("Vtype", "I", title="0: promptT; 1: fakeT; 2: multi-promptL")
        self.out.branch("Vtype_subcat", "I", title="0: OS-promptL/promptL; 1: SS-promptL/promptL; 2: OS-promptL/fakeL; 3: SS-promptL/fakeL; 4: OS-fakeL/fakeL; 5: SS-fakeL/fakeL")
        self.out.branch("MET_filters", "I", title="AND of all MET filters")
        self.out.branch("nVetoElectrons", "I", title="Number of veto electrons")

    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass
    def analyze(self, event):
        """process event, return True (go to next module) or False (fail, go to next event)"""

        # Trigger bit
        if self.isMC==False:
            triggers24_OR = ["IsoMu24", "IsoTkMu24"]
            triggers27_OR = ["IsoMu27"]
        else:
            triggers24_OR = ["IsoMu24", "IsoTkMu24"]
            triggers27_OR = ["IsoMu27"]
        HLT_pass24, HLT_pass27 = False, False
        for hlt in triggers24_OR:
            if not hasattr(event, "HLT_"+hlt): continue
            HLT_pass24 |= getattr(event, "HLT_"+hlt)
        self.out.fillBranch("HLT_SingleMu24", int(HLT_pass24))
        for hlt in triggers27_OR:
            if not hasattr(event, "HLT_"+hlt): continue
            HLT_pass27 |= getattr(event, "HLT_"+hlt)
        self.out.fillBranch("HLT_SingleMu27", int(HLT_pass27))

        # MET filters
        met_filters_AND = True
        for key,val in self.met_filters[self.dataYear].items():
            met_filters_AND &=  (not (val & (1 << (1-int(self.isMC)) )) or getattr(event, "Flag_"+key))
        self.out.fillBranch("MET_filters", int(met_filters_AND))

        # Muon selection
        all_muons = Collection(event, "Muon")

        ##This enumerate part should always be on all_muons
        loose_muons       = [ [mu,imu] for imu,mu in enumerate(all_muons) if loose_muon_id(mu) ]
        medium_muons      = [ [mu,imu] for imu,mu in enumerate(all_muons) if medium_muon_id(mu)]
        medium_aiso_muons = [ [mu,imu] for imu,mu in enumerate(all_muons) if medium_aiso_muon_id(mu)]
        looseIdonly_muons = [ [mu,imu] for imu,mu in enumerate(all_muons) if loose_muon_idonly(mu) ]

        loose_muons.sort( key = lambda x: x[0].pt, reverse=True )
        medium_muons.sort(key = lambda x: x[0].pt, reverse=True )
        medium_aiso_muons.sort(key = lambda x: x[0].pt, reverse=True )
        looseIdonly_muons.sort(key = lambda x: x[0].pt, reverse=True )

        # Electron selection
        all_electrons  = Collection(event, "Electron")    
        veto_electrons = [ [ele,iele] for iele,ele in enumerate(all_electrons) if veto_electron_id(ele) ]
        self.out.fillBranch("nVetoElectrons", len(veto_electrons))

        event_flag = -1        
        event_flag_subcat = -1        
        (idx1, idx2) = (-1, -1)

        # Multilepton-like event
        if len(loose_muons)>=2:
            event_flag = 2
        # W-like event: 1 loose, 1 medium
        elif len(medium_muons)==1:
            event_flag = 0
            (idx1, idx2) = (medium_muons[0][1], -1)
        # Fake-like event
        elif len(medium_muons)==0 and len(medium_aiso_muons)==1:
            event_flag = 1
            (idx1, idx2) = (medium_aiso_muons[0][1], -1)
        else:   
            event_flag = -1

        # Z-like event
        if len(looseIdonly_muons)>=2:
            loose_muons_idxs = [mu[1] for imu,mu in enumerate(loose_muons) ]
            (idx1, idx2) = (looseIdonly_muons[0][1], looseIdonly_muons[1][1])
            charge = all_muons[idx1].charge + all_muons[idx2].charge
            if (idx1 in loose_muons_idxs) and (idx2 in loose_muons_idxs):
                event_flag_subcat = 0 if charge==0 else 1            
            elif (idx1 in loose_muons_idxs and idx2 not in loose_muons_idxs) or \
                 (idx2 in loose_muons_idxs and idx1 not in loose_muons_idxs):
                event_flag_subcat = 2 if charge==0 else 3
            elif not (idx1 in loose_muons_idxs) and not (idx2 in loose_muons_idxs):
                event_flag_subcat = 4 if charge==0 else 5 
            else:
                event_flag_subcat = -1                

        ##Selected muon trigger object matching
        #all_trigs = Collection(event, "TrigObj")
        #v6 filter bits info: 1 = TrkIsoVVL, 2 = Iso, 4 = OverlapFilter PFTau, 8 = IsoTkMu for Muon
        #muon_trigs = [ trig for trig in all_trigs if trig.id==13 and ((trig.filterBits>>0 & 1 ) or (trig.filterBits>>1 & 1 ))]

        ##for tang-and-probe
        self.out.fillBranch("Idx_mu1", idx1)
        self.out.fillBranch("Idx_mu2", idx2)
        self.out.fillBranch("Vtype", event_flag)
        self.out.fillBranch("Vtype_subcat", event_flag_subcat)

        if self.trigOnly:
            if event_flag not in [0,1] :
                return (False or self.passall)
            else:
                return True
        
        if not (HLT_pass24 or HLT_pass27): 
            return (False or self.passall)

        return True

# define modules using the syntax 'name = lambda : constructor' to avoid having them loaded when not needed

preSelectionModule = lambda : preSelection() 
