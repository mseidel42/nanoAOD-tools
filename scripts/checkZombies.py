import ROOT, sys, os

args = sys.argv
d = sys.argv[1]


allfiles = [i for i in os.listdir(d) if '.root' in i]

print('checking', len(allfiles), 'files')

faultyfiles = []

for f in allfiles:
    
    rf = ROOT.TFile(os.path.join(d,f),'read')
    if rf.IsZombie():
        faultyfiles.append(d+f)

    rf.Close()

print('faulty files:')
print('================')
for i in faultyfiles:
    print i

print('found', len(faultyfiles), 'faulty files')
