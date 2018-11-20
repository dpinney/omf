/* Could these functions be used to validate all data models? I'm not sure, so I called this file 
"distDataValidation" instead of "dataValidation". These are just prototype functions right now.
*/

//prototype
const nodeTreeMap = {
    /*treeIndex is used to find the matching tree object.
    This map returns every node as a bad node because longitude and latitude are mixed up! So I'll switch them temporarily.
    */
    name: "name",
    x: "latitude",
    y: "longitude",
    px: "latitude",
    py: "longitude",
    //x: "longitude",
    //y: "latitude",
    //px: "longitude",
    //py: "latitude",
    objectType: "object"
}

// return true if the node matched its partner, otherwise false. 
function objectMatchesPartner(obj, partner, map) {
    return Object.keys(obj).every(key => {
        if (map[key]) {
            if (obj[key] === partner[map[key]]) {
                return true;
            } else if (key === "objectType") {
                if (obj[key] === "gridNode" && partner["object"] === "node") {
                    return true;
                }
            }
            return false;
        }        
        return true;
    });
}

//We get 53 nodes, some of which have mismatching x/latitude values and/or y/longitude values 
const badNodes = feeder.nodes.filter(node => !objectMatchesPartner(node, feeder.tree[node.treeIndex.toString()], nodeTreeMap));
console.log("bad nodes: ");
console.log(badNodes);
//prototype
