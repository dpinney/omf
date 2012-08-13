#!/usr/bin/env python

import treeParser as tp

model_id = 'Simple Market System'
parsed = tp.parse('./feeders/' + model_id + "/main.glm")
print parsed