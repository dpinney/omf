import matplotlib.pyplot as plt
import matplotlib.patheffects as PathEffects
import numpy as np

ax2 = plt.subplot(132)
arr = np.arange(25).reshape((5,5))
ax2.imshow(arr)

cntr = ax2.contour(arr, colors="k")
clbls = ax2.clabel(cntr, fmt="%2.0f", use_clabeltext=True)
plt.setp(clbls, path_effects=[PathEffects.withStroke(linewidth=3, foreground="w")])

plt.show()
