# SNARS-ZTMParser

The ZTMParser is used for reading ZTM data from .TXT files.

# Example usage

```python
import networkx as nx
import matplotlib.pyplot as plt
from ztm_parser import ZTMParser
 
ztm = ZTMParser(path/to/your/txt/file)
edges = ztm.get_edges()
pos = ztm.get_coordinates()

fig = plt.figure(figsize=(20, 20))

G = nx.Graph()
G.add_edges_from(edges)
pos = ztm.get_coordinates()
nx.draw(G, pos, node_size=5, node_color='red')
plt.show()
```
![Example Image](ztm_network.png)
