import json
from pathlib import Path
import omf
from omf import feeder

class Test_treeToNxGraph:

    def test_newNetworkxAPI_returns_sameGraphAsOldNetworkXAPI(self):
        '''
        Two unequal objects CAN have the same hash value. 
        - networkx.Graph instances define __eq__ and __hash__, but that does not mean two unequal Graph objects will have different has values. Don't use hashes for comparison
        '''
        with open(Path(omf.omfDir) / 'static/publicFeeders/Olin Barre Geo.omd') as inFile:
            tree = json.load(inFile)['tree']
        nxG = feeder.treeToNxGraph(tree) # networkx 2.4 API
        with open (Path(__file__).parent / 'olin-barre-geo-nx-graph.json') as f: # Data generated with networkx 1.11
            nx_graph_json = json.load(f)
        nx_graph_json['edges'] = [(e[0], e[1]) for e in nx_graph_json['edges']]
        assert list(nxG.nodes()) == nx_graph_json['nodes']
        assert list(nxG.edges()) == nx_graph_json['edges']


class Test_latLonNxGraph:

    def test_newNetworkxAPI_returns_sameGraphAsOldNetworkXAPI(self):
        with open(Path(omf.omfDir) / 'static/publicFeeders/Olin Barre Geo.omd') as inFile:
            tree = json.load(inFile)['tree']
        nxG = feeder.treeToNxGraph(tree) # networkx 2.4 API
        x = latLonNxGraph(nxG)


if __name__ == '__main__':
    t = Test_latLonNxGraph()
    t.test_newNetworkxAPI_returns_sameGraphAsOldNetworkXAPI()