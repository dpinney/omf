

import helperfuncs
import feederSetup
reload(helperfuncs)
reload(feederSetup)
from helperfuncs import *
from feederSetup import *

print len(problemlinks), "node-link-node configs with AT LEAST one phase mismatch"
print
print len(filter(twoOutta3, problemlinks)), "node-link-node configs with EXACTLY one phase mismatch"
print
print len(filter(invalidPhaseNum, problemlinks)), "node-link-node configs with AT LEAST one invalid phase number"
print
print len(filter(lambda x: twoOutta3(x) and invalidPhaseNum(x), problemlinks)), "node-link-node configs with EXACTLY one phase mismatch and AT LEAST one invalid phase number"

print
xxx = filter(lambda x: not twoOutta3(x) and not invalidPhaseNum(x), problemlinks)
print len(xxx), "more than one mismatch, no invalid phase numbers"
print
# print len(filter(lambda x: not twoOutta3(x) and not invalidPhaseNum(x), problemlinks))
notInvalid = filter(lambda x: not invalidPhaseNum(x), problemlinks)
print len(notInvalid), "at least one mismatch, no invalid phase numbers"
print
whatevs = filter(lambda x: twoOutta3(x) and not invalidPhaseNum(x), problemlinks)
print len(whatevs), "exactly one mismatch, no invalid phase numbers"
print
lineneut = filter(lambda x: x["ldata"]["phases"] == "N", notInvalid)
print len(lineneut), "at least one mismatch, no invalid phase numbers, line object just has N phase"
print
nodeneut= filter(lambda x: x["fromnode"]["phases"] == "N" or x["tonode"]["phases"] == "N", problemlinks)
print len(nodeneut), "configs where a node just has N"



# One Mismatch One Invalid
omov = filter(lambda x: exactlyOneInvalid(x) and twoOutta3(x), problemlinks)
print len(omov), "exactly one mismatch and exactly one invalid.  Logical deduction: the invalid phase is the mismatch"

# Mismatch but one object's phases are a superset of the other two's
mmbss = filter(oneIsSuperset, problemlinks)
print
print len(mmbss), "mismatched, but one object is a superset of the others"

def lineInvalid(lnk):
	return is_invalid(lnk["ldata"]["phases"])

justLine = filter(lambda x: lineInvalid(x), omov)
print len(justLine), "only the line is invalid.  Possibly the easiest fix - just set the line to the phases of its nodes, which are the same"