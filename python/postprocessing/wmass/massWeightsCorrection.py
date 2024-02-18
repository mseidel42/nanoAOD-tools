import os
import shutil
import xml.etree.ElementTree as ET
from array import array

from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
from PhysicsTools.NanoAODTools.postprocessing.wmass.LHEinterpreter.createLHEFormatFromROOTFile import *

class massWeightsCorrection(Module):
    def __init__(self):
        self.maxMassShift = 10
        self.massGrid = 10
        self.steps = self.maxMassShift/self.massGrid+1
        self.centralWgt = 1001
        self.cenMassWgt = 1500+int(self.steps/2)
        self.theP = None
        self.tmpDir = 'tmplhe'
        self.count = 0

    def beginJob(self):
        pass
    def endJob(self):
        pass
    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.count = 0
        
        # TODO: clean this after running
        # if os.path.exists(self.tmpDir):
        #     shutil.rmtree(self.tmpDir)
        # os.mkdir(self.tmpDir)
        self.theP = LHEPrinter(inputFile, inputTree, '%s/tmp.lhe' % self.tmpDir)
        self.theP.beginFile()

        
    def initReaders(self, tree):
        self.LHEScaleWeight = tree.arrayReader("LHEScaleWeight")
        self.LHEPdfWeight = tree.arrayReader("LHEPdfWeight")
        self.MEParamWeight = tree.arrayReader("LHEReweightingWeight")
        self._ttreereaderversion = tree._ttreereaderversion
        pass

    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.theP.endFile()
        
        # TODO: run powheg reweighting here and fill tree
        # with open('%s/runPowheg.sh' % self.tmpDir, 'w') as runscript:
            # runscript.write('cd %s\n' % self.tmpDir)
            # # # runscript.write('tar -xzf /afs/cern.ch/work/m/mseidel/generator/CMSSW_10_2_22/src/Wj_slc7_amd64_gcc700_CMSSW_10_2_22_WplusJToMuNu-suggested-nnpdf31-ncalls-doublefsr-q139-ckm-powheg-MiNNLO3-rwl4-correctingMiniAod.tgz\n')
            # runscript.write('sh ./runcmsgrid.sh 1 1 1\n')
        # os.system('sh %s/runPowheg.sh' % self.tmpDir)
        
        # prepare output branches by hand (normal NanoAOD way does not work)
        self.out = wrappedOutputTree
        massValues = {}
        newBranches = {}
        for i in range(self.massGrid, self.maxMassShift+self.massGrid, self.massGrid):
            nameUp = "massCorrectedShift%iMeVUp"   % i
            nameDn = "massCorrectedShift%iMeVDown" % i
            massValues[nameUp] = array('f', [0])
            massValues[nameDn] = array('f', [0])
            newBranches[nameUp] = self.out.tree().Branch(nameUp, massValues[nameUp], nameUp+"/F")
            newBranches[nameDn] = self.out.tree().Branch(nameDn, massValues[nameDn], nameDn+"/F")
        
        # parse LHE file and fill output tree
        xmlTree = ET.parse('%s/cmsgrid_final.lhe' % self.tmpDir)
        xmlEvents = xmlTree.findall('event')
        # print(len(xmlEvents), self.count)
        assert(len(xmlEvents) == self.count)
        xmlCount = 0
        for xmlEvent in xmlEvents:
            xmlCount += 1
            # print(xmlCount)
            massWeights = {}
            for wgt in xmlEvent.iter('wgt'):
                # print(wgt.tag, int(wgt.attrib['id']), float(wgt.text))
                # ('wgt', 1001, 13874.0)
                massWeights[int(wgt.attrib['id'])] = float(wgt.text)
            for i in range(1, self.steps):
                val = i*self.massGrid
                central = massWeights[self.centralWgt]
                massValues["massCorrectedShift%iMeVUp"   % val][0] = massWeights[self.cenMassWgt+i]/central
                massValues["massCorrectedShift%iMeVDown" % val][0] = massWeights[self.cenMassWgt-i]/central
                # print("massCorrectedShift%iMeVUp"   % val, massWeights[self.cenMassWgt+i]/central)
                # print("massCorrectedShift%iMeVDown" % val, massWeights[self.cenMassWgt-i]/central)
                for nb in newBranches:
                    newBranches[nb].Fill()
        self.out.write()
        
    
    def analyze(self, event):
        """process event, return True (go to next module) or False (fail, go to next event)"""

        self.count += 1
        self.theP.process(event)
        
        # self.out.fillBranch("massCorrectedShift100MeVUp", 123.)
        
        '''
        if event._tree._ttreereaderversion > self._ttreereaderversion:
            self.initReaders(event._tree)

        if len(self.LHEScaleWeight) < self.NumScaleWeights:
            raise RuntimeError("Found poorly formed LHE Scale weights")

        for i,varPair in enumerate([("05","05"), ("05","1"), ("05", "2"), ("1", "05"), \
                ("1","1"), ("1","2"), ("2", "05"), ("2", "1"), ("2", "2")]):
            self.out.fillBranch("scaleWeightMuR%sMuF%s" % varPair, self.LHEScaleWeight[i*2])

        for i in range(1, self.maxMassShift/self.massGrid+1):
            val = i*self.massGrid
            self.out.fillBranch("massShift%iMeVUp" % val, self.MEParamWeight[self.cenMassWgt+i])
            self.out.fillBranch("massShift%iMeVDown" % val, self.MEParamWeight[self.cenMassWgt-i])

        if len(self.LHEPdfWeight) < self.NumNNPDFWeights:
            raise RuntimeError("Found poorly formed LHE Scale weights")

        for i in range(self.NumNNPDFWeights):
            self.out.fillBranch("pdfWeightNNPDF%i" % i, self.LHEPdfWeight[i])
        '''

        return True

correctMassWeightsModule = lambda : massWeightsCorrection() 
