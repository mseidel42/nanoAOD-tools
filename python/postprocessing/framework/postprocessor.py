#!/usr/bin/env python
from PhysicsTools.NanoAODTools.postprocessing.framework.jobreport import JobReport
from PhysicsTools.NanoAODTools.postprocessing.framework.preskimming import preSkim
from PhysicsTools.NanoAODTools.postprocessing.framework.output import FriendOutput, FullOutput
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import eventLoop
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import InputTree
from PhysicsTools.NanoAODTools.postprocessing.framework.branchselection import BranchSelection
import os
import time
import hashlib
import subprocess
import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True


class PostProcessor:
    def __init__(
            self, outputDir, inputFiles, cut=None, branchsel=None, modules=[],
            compression="LZMA:9", friend=False, postfix=None, jsonInput=None,
            noOut=False, justcount=False, provenance=False, haddFileName=None,
            fwkJobReport=False, histFileName=None, histDirName=None,
            outputbranchsel=None, maxEntries=None, firstEntry=0, prefetch=False,
            longTermCache=False, saveHistoGenWeights=False, allowNoPostfix=False
    ):
        self.outputDir = outputDir
        self.inputFiles = inputFiles
        self.cut = cut
        self.modules = modules
        self.compression = compression
        self.postfix = postfix
        self.allowNoPostfix = allowNoPostfix
        self.json = jsonInput
        self.noOut = noOut
        self.friend = friend
        self.justcount = justcount
        self.provenance = provenance
        self.jobReport = JobReport() if fwkJobReport else None
        self.haddFileName = haddFileName
        self.saveHistoGenWeights = saveHistoGenWeights
        self.histFile = None
        self.histDirName = None
        if self.jobReport and not self.haddFileName:
            print("Because you requested a FJR we assume you want the final " \
                "hadd. No name specified for the output file, will use tree.root")
            self.haddFileName = "tree.root"
        self.branchsel = BranchSelection(branchsel) if branchsel else None
        if outputbranchsel is not None:
            self.outputbranchsel = BranchSelection(outputbranchsel)
        elif outputbranchsel is None and branchsel is not None:
            # Use the same branches in the output as in input
            self.outputbranchsel = BranchSelection(branchsel)
        else:
            self.outputbranchsel = None

        self.histFileName = histFileName
        self.histDirName = histDirName
        # 2^63 - 1, largest int64
        self.maxEntries = maxEntries if maxEntries else 9223372036854775807
        self.firstEntry = firstEntry
        self.prefetch = prefetch  # prefetch files to TMPDIR using xrdcp
        # keep cached files across runs (it's then up to you to clean up the temp)
        self.longTermCache = longTermCache

    def prefetchFile(self, fname, verbose=True):
        tmpdir = os.environ['TMPDIR'] if 'TMPDIR' in os.environ else "/tmp"
        if not fname.startswith("root://"):
            return fname, False
        rndchars = "".join([hex(ord(i))[2:] for i in os.urandom(
            8)]) if not self.longTermCache else "long_cache-id%d-%s" \
            % (os.getuid(), hashlib.sha1(fname).hexdigest())
        localfile = "%s/%s-%s.root" \
            % (tmpdir, os.path.basename(fname).replace(".root", ""), rndchars)
        if self.longTermCache and os.path.exists(localfile):
            if verbose:
                print("Filename %s is already available in local path %s " \
                    % (fname, localfile))
            return localfile, False
        try:
            if verbose:
                print("Filename %s is remote, will do a copy to local path %s"\
                    % (fname, localfile))
            start = time.time()
            subprocess.check_output(["xrdcp", "-f", "-N", fname, localfile])
            if verbose:
                print("Time used for transferring the file locally: %.2f s"\
                    % (time.time() - start))
            return localfile, (not self.longTermCache)
        except:
            if verbose:
                print("Error: could not save file locally, will run from remote")
            if os.path.exists(localfile):
                if verbose:
                    print("Deleting partially transferred file %s" % localfile)
                try:
                    os.unlink(localfile)
                except:
                    pass
            return fname, False

    def run(self):
        outpostfix = self.postfix if self.postfix is not None else (
            "_Friend" if self.friend else "_Skim")
        if self.allowNoPostfix and self.postfix is None:
            outpostfix = ""
        if not self.noOut:

            if self.compression != "none":
                ROOT.gInterpreter.ProcessLine("#include <Compression.h>")
                (algo, level) = self.compression.split(":")
                compressionLevel = int(level)
                if algo == "LZMA":
                    compressionAlgo = ROOT.ROOT.kLZMA
                elif algo == "ZLIB":
                    compressionAlgo = ROOT.ROOT.kZLIB
                elif algo == "LZ4":
                    compressionAlgo = ROOT.ROOT.kLZ4
                else:
                    raise RuntimeError("Unsupported compression %s" % algo)
            else:
                compressionLevel = 0
            print("Will write selected trees to " + self.outputDir)
            if not self.justcount:
                if not os.path.exists(self.outputDir):
                    os.system("mkdir -p " + self.outputDir)
        else:
            compressionLevel = 0

        if self.noOut:
            if len(self.modules) == 0:
                raise RuntimeError(
                    "Running with --noout and no modules does nothing!")

        # Open histogram file, if desired
        if (self.histFileName is not None and self.histDirName is None) or (self.histFileName is None and self.histDirName is not None):
            raise RuntimeError(
                "Must specify both histogram file and histogram directory!")
        elif self.histFileName is not None and self.histDirName is None:
            self.histFile = ROOT.TFile.Open(self.histFileName, "RECREATE")
        else:
            self.histFile = None

        for m in self.modules:
            if hasattr(m, 'writeHistFile') and m.writeHistFile:
                m.beginJob(histFile=self.histFile,
                           histDirName=self.histDirName)
            else:
                m.beginJob()

        fullClone = (len(self.modules) == 0)
        outFileNames = []
        t0 = time.time()
        totEntriesRead = 0
        for fname in self.inputFiles:
            ffnames = []
            if "," in fname:
                fnames = fname.split(',')
                fname, ffnames = fnames[0], fnames[1:]

            # open input file
            if self.prefetch:
                ftoread, toBeDeleted = self.prefetchFile(fname)
                inFile = ROOT.TFile.Open(ftoread)
            else:
                inFile = ROOT.TFile.Open(fname)

            if not inFile:
                print 'ERROR: file does not exist, check!'
                print '    filename:', fname
                exit(0)

            # get input tree
            inTree = inFile.Get("Events")
            if inTree is None:
                inTree = inFile.Get("Friends")
            nEntries = min(inTree.GetEntries() -
                           self.firstEntry, self.maxEntries)
            # first check that the histogram with weights is not already in the file
            hasWeightHistograms = False
            if inFile.GetListOfKeys().Contains("hGenWeights") and inFile.GetListOfKeys().Contains("hNumWeights"):
                hasWeightHistograms = True
                print "Histogram hGenWeights already exists, I will just copy it without recreating it"
            if self.saveHistoGenWeights and inTree.GetName() == "Events" and not hasWeightHistograms:
                print "Histogram hGenWeights does not exist yet, I will create it"
                # check that the tree contains all the original events, otherwise the sum of gen weights will miss some
                tmpTreeRuns = inFile.Get("Runs")
                for ievt,event in enumerate(tmpTreeRuns):
                    if ievt: break # only need first event (but there should be only 1 here)
                    nGenEvents = event.genEventCount
                if nGenEvents != inTree.GetEntries():
                    raise RuntimeError(
                        "I am creating the histogram with genWeight, but tree Events has less entries than genEventCount in tree Runs (%s instead of %s). The sum of weights will thus be wrong, please check" % (str(inTree.GetEntries()),str(nGenEvents)))

                # saving distribution of genWeight for offline usage
                # idea is to fill the distribution of Log10(genWeight) with the sign, so to have a histogram from about -10 to 10
                # with about 10k bins (genWeights can take valus spanning several orders of magnitude, especially for fancy weights)
                # then one can compute the sum of genWeight in a given range using its integral (using Log10(threshold) ).
                # This somehow relies on having always |genWeight|>1, should it be < 1 the Log would change the sign.
                # So for the purpose of choosing the bin to be filled, we use |value| or 1.001, whatever is larger (this will not affect the integral)
                # then, need a second histogram to keep the integer number of events in each bin, so to allow for clipping of large weights
                hGenWeights = ROOT.TH1D("hGenWeights","distribution of Log10(genWeight)",4800,-12.0,12.0)                
                hNumWeights = ROOT.TH1D("hNumWeights","distribution of Log10(genWeight) (unweighted)",4800,-12.0,12.0)                
                drawResult = inTree.Draw("TMath::Sign(1.0,genWeight)*TMath::Log10(max(1.001,abs(genWeight)))>>hGenWeights","genWeight","goff",nEntries,self.firstEntry)               
                drawResult = inTree.Draw("TMath::Sign(1.0,genWeight)*TMath::Log10(max(1.001,abs(genWeight)))>>hNumWeights","1","goff",nEntries,self.firstEntry)               
            totEntriesRead += nEntries
            # pre-skimming
            elist, jsonFilter = preSkim(
                inTree, self.json, self.cut, maxEntries=self.maxEntries, firstEntry=self.firstEntry)
            if self.justcount:
                print('Would select %d / %d entries from %s (%.2f%%)' % (elist.GetN() if elist else nEntries, nEntries, fname, (elist.GetN() if elist else nEntries) / (0.01 * nEntries) if nEntries else 0))
                if self.prefetch:
                    if toBeDeleted:
                        os.unlink(ftoread)
                continue
            else:
                print('Pre-select %d entries out of %s (%.2f%%)' % (elist.GetN() if elist else nEntries, nEntries, (elist.GetN() if elist else nEntries) / (0.01 * nEntries) if nEntries else 0))
                inAddFiles = []
                inAddTrees = []
            for ffname in ffnames:
                inAddFiles.append(ROOT.TFile.Open(ffname))
                inAddTree = inAddFiles[-1].Get("Events")
                if inAddTree is None:
                    inAddTree = inAddFiles[-1].Get("Friends")
                inAddTrees.append(inAddTree)
                inTree.AddFriend(inAddTree)

            if fullClone:
                # no need of a reader (no event loop), but set up the elist if available
                if elist:
                    inTree.SetEntryList(elist)
            else:
                # initialize reader
                inTree = InputTree(inTree, elist)

            # prepare output file
            if not self.noOut:
                outFileName = os.path.join(self.outputDir, os.path.basename(
                    fname).replace(".root", outpostfix + ".root"))
                outFile = ROOT.TFile.Open(
                    outFileName, "RECREATE", "", compressionLevel)
                outFileNames.append(outFileName)
                if compressionLevel:
                    outFile.SetCompressionAlgorithm(compressionAlgo)
                # prepare output tree
                if self.friend:
                    outTree = FriendOutput(inFile, inTree, outFile)
                else:
                    outTree = FullOutput(
                        inFile,
                        inTree,
                        outFile,
                        branchSelection=self.branchsel,
                        outputbranchSelection=self.outputbranchsel,
                        fullClone=fullClone,
                        maxEntries=self.maxEntries,
                        firstEntry=self.firstEntry,
                        jsonFilter=jsonFilter,
                        provenance=self.provenance)
            else:
                outFile = None
                outTree = None
                if self.branchsel:
                    self.branchsel.selectBranches(inTree)

            # process events, if needed
            if not fullClone:
                eventRange = range(self.firstEntry, self.firstEntry +
                                    nEntries) if nEntries > 0 and not elist else None
                (nall, npass, timeLoop) = eventLoop(
                    self.modules, inFile, outFile, inTree, outTree,
                    eventRange=eventRange, maxEvents=self.maxEntries
                )
                print('Processed %d preselected entries from %s (%s entries). Finally selected %d entries' % (nall, fname, nEntries, npass))
            else:
                nall = nEntries
                print('Selected %d / %d entries from %s (%.2f%%)' % (outTree.tree().GetEntries(), nall, fname, outTree.tree().GetEntries() / (0.01 * nall) if nall else 0))

            # now write the output
            if not self.noOut:
                outTree.write()
                if not hasWeightHistograms:
                    if self.saveHistoGenWeights:
                        hGenWeights.Write(hGenWeights.GetName())
                        hNumWeights.Write(hNumWeights.GetName())
                outFile.Close()
                print("Done %s" % outFileName)
            if self.jobReport:
                self.jobReport.addInputFile(fname, nall)
            if self.prefetch:
                if toBeDeleted:
                    os.unlink(ftoread)

        for m in self.modules:
            m.endJob()

        print("Total time %.1f sec. to process %i events. Rate = %.1f Hz." % ((time.time() - t0), totEntriesRead, totEntriesRead / (time.time() - t0)))

        if self.haddFileName:
            haddnano = "./haddnano.py" if os.path.isfile(
                "./haddnano.py") else "haddnano.py"
            os.system("%s %s %s" %
                      (haddnano, self.haddFileName, " ".join(outFileNames)))
        if self.jobReport:
            self.jobReport.addOutputFile(self.haddFileName)
            self.jobReport.save()
