import ROOT, sys, os

args = sys.argv
d = sys.argv[1]


allfiles = [i for i in os.listdir(d) if '.root' in i]

print('checking', len(allfiles), 'files')

faultyfiles = []
nTot = len(allfiles)

for i,f in enumerate(allfiles):
    
    rf = ROOT.TFile(os.path.join(d,f),'read')
    if rf.IsZombie() or rf.TestBit(ROOT.TFile.kRecovered) or rf.GetListOfKeys().GetSize()==0:
        faultyfiles.append(d+f)
    if rf.IsOpen():
        rf.Close()
    sys.stdout.write('>>> File {num}/{tot}   \r'.format(num=i+1,tot=nTot))
    sys.stdout.flush()

print "\n"
print('faulty files:')
print('================')
for i in faultyfiles:
    print i

print('found', len(faultyfiles), 'faulty files')
