import ROOT

originalFile = ROOT.TFile("mc94X2016_NANO.root","READ")
tree = originalFile.Get("Events")
lhefile = open("events.lhe","r")

theWeights = [[] for i in range(125)]
theWeightsNew = [[] for i in range(125)]
iEv = 0
for ev in tree:
    iEv += 1
    print iEv
    weights = ev.LHEReweightingWeight
    for i, w in enumerate(weights):
        theWeights[i] = theWeights[i] + [w*ev.LHEWeight_originalXWGTUP]


readingEvent = False
iEv = 0
for line in lhefile.readlines():
  if "<event" in line and not "<\\event" in line:
    readingEvent = True
    iEv += 1
    print iEv
  elif "<\\event" in line and not "<event" in line:
    readingEvent = False
  elif readingEvent:
    if "<wgt id=" in line: # Then we are looking at the reweighting part
      words = line.split(" ")
      idNum = int(words[1].replace("id='rwgt_","").replace("'>",""))-249
      weight = float(words[2])
      theWeightsNew[idNum] = theWeightsNew[idNum] + [weight]


theH = ROOT.TH1F("hW","hW", 100,-1.,1.)
for i in range(124):
  for j in range(100):
    print i,j , theWeights[i][j], theWeightsNew[i][j]
    theH.Fill( (theWeights[i][j] - theWeightsNew[i][j])/(theWeights[i][j]))

theH.GetXaxis().SetTitle("(w_{Old} - w_{New})/ w_{Old}")
theH.GetYaxis().SetTitle("Weights")

theH.SetTitle("")

c = ROOT.TCanvas("c1","c1",800,600)
theH.Draw("hist")
c.SaveAs("test.pdf")
