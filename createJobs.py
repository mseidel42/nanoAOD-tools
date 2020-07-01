import os
import sys
import gzip

args = sys.argv[:]
baseInputLHEDir = args[1] # lhe events as obtained from createLHEFormatFromROOTFile.py
baseGridpack    = args[2] # tar.gz file with the gridpack
templateRun     = args[3] # a .lhe file containing only the banner and general run settings and handle [[[ PLACE YOUR EVENTS HERE ]]] where events should be
baseOutputLHEDir= args[4] # output directory

xMatch = "qwueihdsfjqwbekqwegqwygoifzhkldbflkdsfqwerqew" #In case we want to supress any production
if len(args) >= 6:
  xMatch = args[5]

newOnly = True

#Read empty lhe file
inBase = gzip.open(templateRun,"rb")
baseHeader = inBase.read()
inBase.close()
iJob = 0

#Loop over the chunks to process
for f in os.listdir(baseInputLHEDir):
  print f
  if not "lhe" in f: continue
  if xMatch in f: print "Skip %s"%f; continue
  if newOnly and os.path.isfile(baseOutputLHEDir + "/" + f + ".gz"): continue
  # Copy the lhe format with the chunks events
  print "Creating lhe reweighting job for %s"%f
  short = f.replace("lhe","")
  inEvFile = open(baseInputLHEDir + "/" + f,"rb")
  inEvents = inEvFile.read()
  outEvents = gzip.open(os.path.dirname(os.path.realpath(__file__)) + "/tmp/"+ short + ".lhe.gz","wb")
  outHeader= baseHeader.replace("[[[ PLACE YOUR EVENTS HERE ]]]",inEvents)
  outEvents.write(outHeader)
  outEvents.close()
  inEvFile.close()
  # Now create the job executable
  output = baseOutputLHEDir + "/" + f
  jobTemplate = open("jobTemplate.sh", "rb")
  jobInText = jobTemplate.read()
  jobTemplate.close()
  newjob = open("jobs/_%i.sh"%iJob, "wb")
  newjob.write(jobInText.replace("[PWD]",os.path.dirname(os.path.realpath(__file__))).replace("[MODEL]",f).replace("[GRIDPACK]",baseGridpack).replace("[EVENTSFILE]",os.path.dirname(os.path.realpath(__file__)) + "/tmp/"+ short + ".lhe.gz").replace("[OUTPUT]",output))
  newjob.close()
  iJob +=1
