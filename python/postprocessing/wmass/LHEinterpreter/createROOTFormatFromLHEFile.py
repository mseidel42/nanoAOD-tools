import ROOT
import os
import gzip
import copy
import array

class LHEToRootConversor(object):
  def __init__(self, lhefile, dictEntries, defaults):
    """ Transform the output lhe file into a friend-tree like rootfile with the weights as entries
    lhefile     : input lhefile from the reweighting
    dictEntries : a dictionary with pretty labels for the different parameters (i.e. create branches with pretty parameter names instead of things like dim6 1).
    defaults : default values of the parameters (not read from the banner, technically can be random values as it will be overwritten)
    """
    # Load lhe file
    self.lhefile = lhefile
    self.inp     = gzip.open(self.lhefile,"rb")
    print "Loading whole LHE file, this might take a while..."
    self.thelines = self.inp.readlines()
    self.dictEntries = dictEntries
    self.defaults = defaults
    self.central = ""
    
    # Get weights definitions from the banner
    self.loadWeightDefs()
    self.nWeights = len(self.weightVars) 
    
    # Build output file
    self.outputRootFile = ROOT.TFile(self.lhefile.replace(".lhe.gz",".root"), "RECREATE")
    self.sf = self.outputRootFile.mkdir("sf")
    self.outputTree = ROOT.TTree("t","LHEweight tree")
    self.initTree()

    # This is the insideloop function
    self.getEvents()
    self.sf.cd()
 
    # Write and close
    self.outputTree.Write()
    self.outputRootFile.Close()

  def getEvents(self):
    readEvent = False
    readWeight = False
    iev = 0
    events = -1
    iL = 0
    totL = len(self.thelines)
    for l in self.thelines:
      iL += 1
      if "<event" in l: #Start reading event
        iev += 1
        print "Processing event (total number estimated) ... %i/%i"%(iev, (totL)/(iL/iev) )
        readEvent = True
        self.ret = copy.copy(self.branchPointers)
 
      if readEvent: # Check if we should start or stop reading weights and read if we should be doing it
        if "<rwgt" in l: 
          readWeight = True
        if readWeight:
          if "wgt id" in l:
            idw = l.split(">")[0].replace("<wgt id='","").replace("'","")
            val = float(l.split(">")[1].replace("</wgt","").replace(" ",""))
            self.ret["LHERew_weights"][int(idw.replace("rwgt_",""))-1] = val

          if "</rwgt>" in l: 
            readWeight = False
        if "</event>" in l:
          # Normalize to SM value defined as all EFT parameters set to 0
          toNorm = self.ret["LHERew_weights"][self.central]
          for i in range(0, self.nWeights):
            self.ret["LHERew_weights"][i] = self.ret["LHERew_weights"][i]/toNorm
          readEvent = False
          self.branchPointers = self.ret
          self.outputTree.Fill()
     
  def initTree(self):
    # Open and initialize the whole output tree
    self.branchPointers = {}
    for k in self.dictEntries:
      self.branchPointers[k] = array.array('f',[1.]*self.nWeights)
      self.outputTree.Branch("LHERew_"+ self.dictEntries[k], self.branchPointers[k], "LHERew_%s[%i]/F"%(self.dictEntries[k],self.nWeights))
    self.branchPointers["LHERew_weights"] = array.array('f',[1.]*self.nWeights)
    self.outputTree.Branch("LHERew_weights", self.branchPointers["LHERew_weights"], "LHERew_weights[%i]/F"%self.nWeights)
    for i in range(1, self.nWeights):
      for k in self.branchPointers:
         if k=="LHERew_weights": continue
         self.branchPointers[k][i-1] = self.weightVars["rwgt_%i"%i][k]

  def loadWeightDefs(self):
    # Read weight definition from the banner to later save it
    print "Finding weights in banner...."
    readingBlock  = False
    readingWeight = False
    self.weightVars = {}
    iL = 0
    for l in self.thelines:
      #This will get the parameter definitions from the banner
      if "weightgroup name='mg_reweighting'" in l:
        readingBlock = True
      if readingBlock:
        if "/weightgroup" in l: 
          readingBlock = False
        elif "<weight" in l:
          readingWeight     = True
          currentWeightName = l.split(">")[0].replace("<weight id='","").replace("'","")
          self.weightVars[currentWeightName] = copy.copy(self.defaults)
          if "set param" in l.split(">")[1]:
            w = l.split(">")[1].split("#")[0]
            sett, param, mod, entry, value, dummy = w.split(" ")
            self.weightVars[currentWeightName][mod + " " + entry] = float(value)
        elif "set param" in l:
          sett, param, mod, entry, value, dummy = l.split("#")[0].split(" ")
          self.weightVars[currentWeightName][mod + " " + entry] = float(value)
        if "</weight>" in l:
          readingWeight = False
          print currentWeightName, self.weightVars[currentWeightName]
          if all([self.weightVars[currentWeightName][k] == 0 for k in self.weightVars[currentWeightName]]):
            self.central = int(currentWeightName.replace("rwgt_",""))-1
            print "Found all parameters at 0 (SM-like candidate) at weight %s"%currentWeightName

for df in os.listdir("output"):
  print  "Processing file...", df
  if "root" in df: continue
  if os.path.isfile("output/"+df.replace(".lhe.gz",".root")): continue
  LHEToRootConversor("output/" + df, {"dim6 1":"cwww","dim6 2":"cw","dim6 3":"cb", "dim6 4":"cPwww","dim6 5":"cPw", "dim6 6":"cPhid","dim6 7":"cPhiW","dim6 8":"cPhib"}, {"dim6 1":3,"dim6 2":4,"dim6 3":150, "dim6 4":100,"dim6 5":100, "dim6 6":100,"dim6 7":100,"dim6 8":100})
