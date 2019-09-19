//<script>
"use strict";
const rawTree = {
    // weirdNode1
    "0": {
        "timezone": "PST+8PDT", 
        "stoptime": "'2000-01-02 00:00:00'", 
        "starttime": "'2000-01-01 00:00:00'", 
        "clock": "clock"
    }, 
    // weirdNode2
    "1": {
        "omftype": "#set", 
        "argument": "minimum_timestep=60"
    }, 
    // node1
    "245000": {
        "phases": "ABC", 
        "name": "nodeT10263825298", 
        "object": "node", 
        "longitude": "571.1273158682793", 
        "nominal_voltage": "7200.0", 
        "latitude": "279.0611346507024"
    }, 
    // node1Line1
    "368700": {
        "phases": "BS", 
        "from": "nodeT10263825298", 
        "name": "T10263_B", 
        "object": "transformer", 
        "to": "nodeS1707-03-015T10263_B", 
        "configuration": "1807--T325_B-CONFIG"
    }, 
    // node1Line1End
    "285800": {
        "phases": "BS", 
        "name": "nodeS1707-03-015T10263_B", 
        "object": "triplex_meter", 
        "longitude": "594.4864602890987", 
        "nominal_voltage": "120", 
        "latitude": "255.701990229883"
    }, 
    // node1Line1EndChild1
    "326000": {
        "phases": "BS", 
        "power_12": "2668.11+1983.57j", 
        "name": "S1707-03-015_B", 
        "parent": "nodeS1707-03-015T10263_B", 
        "object": "triplex_node", 
        "longitude": "622.0927218773398", 
        "nominal_voltage": "120", 
        "latitude": "253.57843164617213"
    }, 
    // node1Line2
    "368500": {
        "phases": "AS", 
        "from": "nodeT10263825298", 
        "name": "T10263_A", 
        "object": "transformer", 
        "to": "nodeS1707-03-015T10263_A", 
        "configuration": "T10285_A-CONFIG"
    }, 
    // node1Line2End
    "285600": {
        "phases": "AS", 
        "name": "nodeS1707-03-015T10263_A", 
        "object": "triplex_meter", 
        "longitude": "619.4382736477013", 
        "nominal_voltage": "120", 
        "latitude": "297.6422560567061"
    }, 
    // node1Line2EndChild1
    "325800": {
        "phases": "AS", 
        "power_12": "2668.11+1983.57j", 
        "name": "S1707-03-015_A", 
        "parent": "nodeS1707-03-015T10263_A", 
        "object": "triplex_node", 
        "longitude": "605.104253207653", 
        "nominal_voltage": "120", 
        "latitude": "320.47051083159784"
    }, 
    // node1Line3
    "368600": {
        "phases": "CS", 
        "from": "nodeT10263825298", 
        "name": "T10263_C", 
        "object": "transformer", 
        "to": "nodeS1707-03-015T10263_C", 
        "configuration": "1807--T325_C-CONFIG"
    }, 
    // node1Line3End
    "285700": {
        "phases": "CS", 
        "name": "nodeS1707-03-015T10263_C", 
        "object": "triplex_meter", 
        "longitude": "563.6948608252912", 
        "nominal_voltage": "120", 
        "latitude": "243.49152837354555"
    }, 
    // node1Line3EndChild1
    "325900": {
        "phases": "CS", 
        "power_12": "2668.11+1983.57j", 
        "name": "S1707-03-015_C", 
        "parent": "nodeS1707-03-015T10263_C", 
        "object": "triplex_node", 
        "longitude": "545.644612863749", 
        "nominal_voltage": "120", 
        "latitude": "228.09572864164187"
    }, 
    // node1Line4
    "116900": {
        "phases": "ACB", 
        "from": "node825298923940", 
        "name": "825298", 
        "object": "underground_line", 
        "longitude": "529.037660472", 
        "to": "nodeT10263825298", 
        "length": "621", 
        "latitude": "284.670992574", 
        "configuration": "825456-LINECONFIG"
    }, 
    // node2 === node1Line4End (node off the main part of ABEC)
    "244900": {
        "phases": "ABC", 
        "name": "node825298923940", 
        "object": "node", 
        "longitude": "529.037660472", 
        "nominal_voltage": "7200.0", 
        "latitude": "274.670992574"
    }, 
    // node2Line1
    "117200": {
        "phases": "B", 
        "from": "node825298923940", 
        "name": "923941", 
        "object": "underground_line", 
        "longitude": "534.263309411", 
        "to": "nodeT6247418245957866", 
        "length": "417", 
        "latitude": "258.557647233", 
        "configuration": "825117-LINECONFIG"
    }, 
    // node2Line1End == node3
    // node2Line2
    "116800": {
        "phases": "ACB", 
        "from": "node7055970558", 
        "name": "923940", 
        "object": "underground_line", 
        "longitude": "524.65806898", 
        "to": "node825298923940", 
        "length": "630", 
        "latitude": "263.265155066", 
        "configuration": "923991-LINECONFIG"
    }, 
    // node2Line2End
    "140120": {
        "phases": "ABCN", 
        "name": "node7055970558", 
        "object": "node", 
        "longitude": "558.3859643660142", 
        "nominal_voltage": "7200.0", 
        "latitude": "312.50718234414836"
    }, 
    // node2Line2EndChild1
    "60720": {
        "control": "VOLT", 
        "dwell_time": "0.0", 
        "object": "capacitor", 
        "name": "CAP134", 
        "parent": "node7055970558", 
        "capacitor_B": "0.10 MVAr", 
        "capacitor_C": "0.10 MVAr", 
        "capacitor_A": "0.10 MVAr", 
        "phases": "ABCN", 
        "longitude": "620.7180398965284", 
        "time_delay": "300.0", 
        "switchC": "CLOSED", 
        "nominal_voltage": "2401.7771", 
        "voltage_set_high": "2350.0", 
        "voltage_set_low": "2340.0", 
        "latitude": "470.93253526327317", 
        "control_level": "INDIVIDUAL", 
        "switchA": "CLOSED", 
        "switchB": "CLOSED", 
        "phases_connected": "ABCN", 
        "pt_phase": "ABCN"
    }, 
    // node2Line3
    "117600": {
        "phases": "ACB", 
        "from": "node825298923940", 
        "name": "923942", 
        "object": "underground_line", 
        "longitude": "563.750899855", 
        "to": "nodeT6246217033670559", 
        "length": "1904", 
        "latitude": "244.93844218", 
        "configuration": "923991-LINECONFIG"
    }, 
    // node2Line3End
    "140220": {
        "phases": "ABCN", 
        "name": "nodeT6246217033670559", 
        "object": "node", 
        "longitude": "522.8163580888573", 
        "nominal_voltage": "7200.0", 
        "latitude": "345.42234039166664"
    }, 
    // node2Line3EndLine
    "52220": {
        "phases": "AN", 
        "from": "nodeT6246217033670559", 
        "name": "17127", 
        "object": "overhead_line", 
        "longitude": "622.2431817865727", 
        "to": "nodeF526917127", 
        "length": "25.2353", 
        "latitude": "469.0231890245341", 
        "configuration": "18949line_configuration24501"
    }, 
    // node2Line3EndLineEnd
    "140320": {
        "phases": "AN", 
        "name": "nodeF526917127", 
        "object": "node", 
        "longitude": "546.7063921556045", 
        "nominal_voltage": "7200.0", 
        "latitude": "360.28725047764266"
    }, 
    // node3 === node2Line1End (main node of 3 houses)
    "136420": {
        "phases": "AN", 
        "name": "nodeT6247418245957866", 
        "object": "node", 
        "longitude": "454.528228025527", 
        "nominal_voltage": "7200.0", 
        "latitude": "377.2278969234081"
    }, 
    // node3Line1
    "46420": {
        "phases": "AS", 
        "from": "nodeT6247418245957866", 
        "name": "T62474182459", 
        "object": "transformer", 
        "longitude": "104.18010219805728", 
        "to": "node62474182499T62474182459", 
        "latitude": "666.852052925009", 
        "configuration": "T62474206624transformer_configuration90001"
    }, 
    // node3Line1End (parent of 3 houses)
    "136520": {
        "phases": "AS", 
        "name": "node62474182499T62474182459", 
        "object": "triplex_meter", 
        "longitude": 410.7928844905687,
        "nominal_voltage": "120", 
        "latitude": 467.61430322224993
    }, 
    // node3Line1EndChild1 (house with 2 children)
    "172262": {
        "schedule_skew": "761", 
        "name": "house172262", 
        "parent": "node62474182499T62474182459", 
        "floor_area": "2200", 
        "cooling_COP": "3.4", 
        "object": "house", 
        "cooling_system_type": "ELECTRIC", 
        "longitude": 276.67116431669666, 
        "heating_setpoint": "heating4*1", 
        "cooling_setpoint": "cooling7*1", 
        "air_temperature": "70", 
        "thermal_integrity_level": "5", 
        "heating_COP": "2.4", 
        "latitude": 441.3730674413469, 
        "mass_temperature": "70", 
        "heating_system_type": "HEAT_PUMP"
    }, 
    // node3Line1EndChild1Child1
    "172263": {
        "parent": "house172262", 
        "schedule_skew": "1100", 
        "name": "ZIPload172263", 
        "power_fraction": "0.400000", 
        "object": "ZIPload", 
        "current_fraction": "0.300000", 
        "longitude": 274.72737127069854, 
        "base_power": "LIGHTS*1.33", 
        "latitude": 399.5815169523868, 
        "current_pf": "1.000", 
        "power_pf": "1.000", 
        "heatgain_fraction": "0.9", 
        "impedance_fraction": "0.300000", 
        "impedance_pf": "1.000"
    }, 
    // node3Line1EndChild1Child2
    "172295": {
        "schedule_skew": "998", 
        "heating_element_capacity": "5.2", 
        "parent": "house172262", 
        "tank_volume": "50", 
        "object": "waterheater", 
        "longitude": 237.79530339673374, 
        "thermostat_deadband": "4.6", 
        "location": "INSIDE", 
        "demand": "water16*1", 
        "latitude": 479.2770614982388, 
        "temperature": "135", 
        "tank_setpoint": "132", 
        "tank_UA": "2.6", 
        "name": "waterheater172295"
    }, 
    // node3Line1EndChild2 (house with single child)
    "172260": {
        "schedule_skew": "-2400", 
        "name": "house172260", 
        "parent": "node62474182499T62474182459", 
        "floor_area": "1400", 
        "cooling_COP": "2.9", 
        "object": "house", 
        "cooling_system_type": "NONE", 
        "longitude": 359.2823687716179, 
        "heating_setpoint": "heating5*1", 
        "cooling_setpoint": "cooling8*1", 
        "air_temperature": "70", 
        "thermal_integrity_level": "6", 
        "heating_COP": "3.3", 
        "latitude": 523.0124050331971, 
        "mass_temperature": "70", 
        "heating_system_type": "RESISTANCE"
    }, 
    // node3Line1EndChild2Child1
    "172261": {
        "parent": "house172260", 
        "schedule_skew": "3510", 
        "name": "ZIPload172261", 
        "power_fraction": "0.400000", 
        "object": "ZIPload", 
        "current_fraction": "0.300000", 
        "longitude": 319.4346113286559, 
        "base_power": "LIGHTS*1.33", 
        "latitude": 557.0287833381647, 
        "current_pf": "1.000", 
        "power_pf": "1.000", 
        "heatgain_fraction": "0.9", 
        "impedance_fraction": "0.300000", 
        "impedance_pf": "1.000"
    }, 
    // node3Line1EndChild3 (house with no children)
    "172264": {
        "schedule_skew": "-1600", 
        "name": "house172264", 
        "parent": "node62474182499T62474182459", 
        "floor_area": "1500", 
        "cooling_COP": "2.6", 
        "object": "house", 
        "cooling_system_type": "NONE", 
        "longitude": 442.86546974953814, 
        "heating_setpoint": "heating4*1", 
        "cooling_setpoint": "cooling3*1", 
        "air_temperature": "70", 
        "thermal_integrity_level": "4", 
        "heating_COP": "2.8", 
        "latitude": 549.2536111541721,
        "mass_temperature": "70", 
        "heating_system_type": "RESISTANCE"
    }, 
    // orphanNode1: has a 'parent' node, but that node does not exist.
    "172265": {
        "parent": "madeUpHouse", 
        "schedule_skew": "-3120", 
        "name": "ZIPload172265", 
        "power_fraction": "0.400000", 
        "object": "ZIPload", 
        "current_fraction": "0.300000", 
        "longitude": 409.82098796756964, 
        "base_power": "LIGHTS*1.33", 
        "latitude": 588.129472074135, 
        "current_pf": "1.000", 
        "power_pf": "1.000", 
        "heatgain_fraction": "0.9", 
        "impedance_fraction": "0.300000", 
        "impedance_pf": "1.000"
    }, 
    // orphanLine1: has valid "from" and "to" values, but those nodes don't exist
    "33420": {
        "phases": "ACBN", 
        "from": "nodeDoesntExist1", 
        "name": "17783", 
        "object": "overhead_line", 
        "longitude": 405.7790593997488, 
        "to": "nodeDoesntExist2", 
        "length": "338.245", 
        "latitude": 614.664711377176, 
        "configuration": "16564line_configuration32701"
    },
    // funkyLine1: a line is never found between two houses like this
    "121212": {
        "phases": "CS", 
        "from": "house172262", 
        "name": "Decepticon", 
        "object": "transformer", 
        "to": "house172260", 
        "configuration": "1807--T325_C-CONFIG"
    }, 
    "343434": {// funkyLine2: a line is never found between two houses like this
        "phases": "CS", 
        "from": "house172260", 
        "name": "AutoBot", 
        "object": "transformer", 
        "to": "house172264", 
        "configuration": "1807--T325_C-CONFIG"
    }, 
    "00900": {// childOfLine (node2Line1)
        object: "waterheater",
        name: "waterheater00900",
        parent: "T62474182459",
        longitude: 408.17398807424905,
        latitude: 403.9973646798732
    },
    "113118": {// lineToLoad
        object: "regulator",
        name: "regulator88",
        from: "node7055970558",
        to: "S1707-03-015_A",
        phases: "A"
    }
};
let rawTreeCopy = deepCopy(rawTree);
let testTree = createTree(rawTreeCopy);
// Load the test data into the document before performing tests
const loadTestData = (async function() {
    // Interface initialization is asynchronous and happens automatically. In order to run these tests, initializeInterface() should be temporarily
    // commented-out in distNetViz.html
    await initializeInterface();
    createSvgData(Object.keys(gTree.tree)).remove(gViewport);
    insertCoordinates(Object.values(testTree.tree), 128, 590, 5);
    const svg = createSvgData(Object.keys(testTree.tree), testTree);
    svg.quickDraw(gViewport);
    // Hack
    gTree = testTree;
})()

/* 
TODO: If key === 0, longitude === 0, latitude === 0 (or some other property === 0), the code could 
break in funny ways. I need to check for undefined explicitly instead of using !<property>
TODO: build a tree that is more representative of the actual data

Tree does NOT contain any cycles

Some latitudes and longitudes are strings while others are numbers in the .omd files. Is this a problem?

Hardcoding test data like this is bad because if the original data ever changes structure, the methods will fail but
these unit tests will still pass. However, it is necessary because the alternative would be to use the real rawTreeCopy from a .omd
file and then these unit tests would be dependent on a particular .omd file which is even worse.

39 keys for 37 objects.
The rawTreeCopy is fairly well-formed, aside from the orphan line and orphan node. It should stay well-formed. If I want to test for really malformed data, I should do it in a unit test.

I should only be testing public functions and methods! 

do not test error handling. It's always changing. But error handling is what matters and is tricky! But I move too slow if I test every error condition. Unit tests need to be as few and as simple as possible or there's too many and it's overwhelming and more harmful than helpful. Also, remember that I'm never testing what DOESN'T happen, unless it's for a very specific tricky case. If I encouter and fix a bug, I can add a test to prevent regressions. Unit tests are BASIC!!!!!
*/
describe("Unit tests", function() {

    const weirdNode1 = "0";
    const weirdNode2 = "1";
    const node1 = "245000";
    const node1Line1 = "368700";
    const node1Line1End = "285800";
    const node1Line1EndChild1 = "326000";
    const node1Line2 = "368500";
    const node1Line2End = "285600";
    const node1Line2EndChild1 = "325800";
    const node1Line3 = "368600";
    const node1Line3End = "285700";
    const node1Line3EndChild1 = "325900";
    const node1Line4 = "116900";
    const node1Line4End = "244900";
    const node2 = node1Line4End;
    const node2Line1 = "117200";
    const node2Line1End  = "136420";
    const node2Line2 = "116800";
    const node2Line2End = "140120";
    const node2Line2EndChild1 = "60720";
    const node2Line3 = "117600";
    const node2Line3End = "140220";
    const node2Line3EndLine = "52220";
    const node2Line3EndLineEnd = "140320";
    const node3 = node2Line1End;
    const node3Line1 = "46420";
    const node3Line1End = "136520";
    const node3Line1EndChild1 = "172262";
    const node3Line1EndChild1Child1 = "172263";
    const node3Line1EndChild1Child2 = "172295";
    const node3Line1EndChild2 = "172260";
    const node3Line1EndChild2Child1 = "172261";
    const node3Line1EndChild3 = "172264";
    const orphanNode1 = "172265";
    const orphanLine1 = "33420";
    const funkyLine1 = "121212";
    const funkyLine2 = "343434";
    const childOfLine = "00900";
    const lineToLoad = "113118";

    const allKeys = [weirdNode1, weirdNode2, node1, node1Line1, node1Line1End, node1Line1EndChild1, node1Line2,
        node1Line2End, node1Line2EndChild1, node1Line3, node1Line3End, node1Line3EndChild1, node1Line4, node1Line4End,
        node2Line1, node2Line1End , node2Line2, node2Line2End, node2Line2EndChild1, node2Line3, node2Line3End,
        node2Line3EndLine, node2Line3EndLineEnd, node3Line1, node3Line1End, node3Line1EndChild1,
        node3Line1EndChild1Child1, node3Line1EndChild1Child2, node3Line1EndChild2, node3Line1EndChild2Child1,
        node3Line1EndChild3, orphanNode1, orphanLine1, funkyLine1, funkyLine2, childOfLine, lineToLoad
    ];

    let consoleErrorSpy;

    beforeEach(function() {
        consoleErrorSpy = spyOn(console, "error");
        rawTreeCopy = deepCopy(rawTree);
        testTree = createTree(rawTreeCopy);
    });
    
    describe("Public functions and methods", function() {
        //good
        describe("createTreeMap()", function() {

            describe("if an object's name property has any of the following values: 'null' (in any letter case), 'undefined' (in any letter case), null, or undefined", function() {

                it("should not map the key of that object to its name", function() {
                    const tree = {
                        "0": {
                            name: "null",
                        },
                        "1": {
                            name: null
                        },
                        "2": {
                            name: "undefined"
                        },
                        "3": {
                            name: undefined
                        },
                        "4": {
                            name: "nUlL"
                        },
                        "5": {
                            name: "UnDefInEd"
                        }
                    };
                    const treeMap = createTreeMap(tree);
                    expect(treeMap.names).toEqual({});
                });
            });

            it("should map the key of each object to its 'name' property in an integration test", function() {
                const treeMap = createTreeMap(rawTreeCopy);
                const names = {};
                Object.keys(rawTreeCopy).forEach(key => {
                    if (rawTreeCopy[key].name != null) {
                        names[rawTreeCopy[key].name] = key;
                    }
                });
                expect(treeMap.names).toEqual(names);
            });


            describe("if a tree object has any of the following values for its 'name' property: null, 'null' (in any letter case), undefined, or 'undefined'" +
            "(in any letter case), and a child node has any of those values for its 'parent' property", function() {

                it("should not map that child node to that tree object", function() {
                    const tree = {
                        "0": {
                            name: "null",
                        },
                        "1": {
                            name: null
                        },
                        "2": {
                            name: "undefined"
                        },
                        "3": {
                            name: undefined
                        },
                        "4": {
                            name: "nUlL"
                        },
                        "5": {
                            name: "UnDefInEd"
                        },
                        "6": {
                            parent: "null"
                        },
                        "7": {
                            parent: null
                        },
                        "8": {
                            parent: "undefined"
                        }, 
                        "9": {
                            parent: undefined
                        },
                        "10": {
                            parent: "nUlL"
                        },
                        "11": {
                            parent: "UnDefInEd"
                        }
                    };
                    const treeMap = createTreeMap(tree);
                    Object.keys(tree).forEach(key => {
                        expect(treeMap.children[key]).toBeUndefined();
                    });
                });
            });

            it("should map the key of each object to an array of its child keys in an integration test", function() {
                const treeMap = createTreeMap(rawTreeCopy);
                Object.keys(rawTreeCopy).forEach(parentKey => {
                    if (rawTreeCopy[parentKey].name != null) {
                        const children = [];
                        Object.keys(rawTreeCopy).forEach(childKey => {
                            if (rawTreeCopy[childKey].parent === rawTreeCopy[parentKey].name) {
                                children.push(childKey);
                            }
                        });
                        if (children.length > 0) {
                            expect(treeMap.children[parentKey]).toEqual(children);
                        } else {
                            expect(treeMap.children[parentKey]).toBeUndefined();
                        }
                    }
                });
            });

            describe("if a tree object has any of the following values for its 'name' property: null, 'null' (in any letter case), undefined, or 'undefined' (in any letter case), and a line has any of those values for its 'to' or 'from' properties", function() {

                it("should not map that line to that tree object", function() {
                    const tree = {
                        "0": {
                            name: "null",
                        },
                        "1": {
                            name: null
                        },
                        "2": {
                            name: "undefined"
                        },
                        "3": {
                            name: undefined
                        },
                        "4": {
                            name: "nUlL"
                        },
                        "5": {
                            name: "UnDefInEd"
                        },
                        "6": {
                            to: "null",
                            from: "null"
                        },
                        "7": {
                            to: null,
                            from: null
                        },
                        "8": {
                            to: "undefined",
                            from: "undefined"
                        }, 
                        "9": {
                            to: undefined,
                            from: undefined
                        },
                        "10": {
                            to: "nUlL",
                            from: "nUlL"
                        },
                        "11": {
                            to: "UnDefInEd",
                            from: "UnDefInEd"
                        }
                    };
                    const treeMap = createTreeMap(tree);
                    Object.keys(tree).forEach(key => {
                        expect(treeMap.lines[key]).toBeUndefined();
                    });
                });
            });

            it("should pass an integration test that maps the key of each object to an array of its connected line keys", function() {
                const treeMap = createTreeMap(rawTreeCopy);
                Object.keys(rawTreeCopy).forEach(nodeKey => {
                    if (rawTreeCopy[nodeKey].name != null) {
                        const nodeName = rawTreeCopy[nodeKey].name;
                        const lines = [];
                        Object.keys(rawTreeCopy).forEach(lineKey => {
                            if (rawTreeCopy[lineKey].to === nodeName || rawTreeCopy[lineKey].from === nodeName) {
                                lines.push(lineKey);
                            }
                        });
                        if (lines.length > 0) {
                            expect(treeMap.lines[nodeKey]).toEqual(lines);
                        } else {
                            expect(treeMap.lines[nodeKey]).toBeUndefined();
                        }
                    }
                });
            });
        });
        //good
        describe("treeMapPrototype", function() {

            describe("children mapping function", function() {

                let treeMap;

                beforeEach(function() {
                    const tree = {
                        "0": {
                            object: "node",
                            name: "node0"
                        },
                        "1": {
                            object: "childNode",
                            parent: "node0"
                        },
                        "2": {
                            object: "childNode",
                            parent: "node0"
                        }
                    };
                    treeMap = createTreeMap(tree);
                });
                //good
                describe("mapChild()", function() {

                    describe("if the parent hasn't had any children added to its array yet", function() {

                        it("should store an array containing the child key at the parent key", function() {
                            treeMap.children = {};
                            expect(treeMap.children["0"]).toBeUndefined();
                            treeMap.mapChild("1");
                            expect(treeMap.children["0"]).toEqual(["1"]);
                        });
                    });

                    describe("if the parent already has had children added to its array", function() {

                        describe("if child key already exists in the parent's array", function() {

                            it("should not push the key of the child onto the parent's array", function() {
                                treeMap.children = {};
                                expect(treeMap.children["0"]).toBeUndefined();
                                treeMap.mapChild("1");
                                expect(treeMap.children["0"]).toEqual(["1"]); 
                                treeMap.mapChild("1");
                                expect(treeMap.children["0"]).toEqual(["1"]); 
                            });
                        });
                    });

                    describe("if the child key does not exist in the parent's array", function() {

                        it("should push the child key onto the parent's array", function() {
                            treeMap.children = {};
                            expect(treeMap.children["0"]).toBeUndefined();
                            treeMap.mapChild("1");
                            expect(treeMap.children["0"]).toEqual(["1"]);
                            treeMap.mapChild("2");
                            expect(treeMap.children["0"]).toEqual(["1", "2"]);
                        });
                    });

                    it("should pass an integration test that maps children to parents", function() {
                        const treeMap = createTreeMap(rawTreeCopy);
                        treeMap.children = {};
                        Object.keys(rawTreeCopy).forEach(key => {
                            treeMap.mapChild(key);
                        });
                        expect(testTree.treeMap.children).toEqual(treeMap.children);
                    });
                });
                //good
                describe("unmapChild()", function() {

                    describe("if the child key exists in the parent's array", function() {

                        it("should remove the child key from the parent's array", function() {
                            expect(treeMap.children["0"]).toEqual(["1", "2"]);
                            treeMap.unmapChild("2");
                            expect(treeMap.children["0"]).toEqual(["1"]);
                            treeMap.unmapChild("1");
                            expect(treeMap.children["0"]).toBeUndefined();
                        });
                    });

                    describe("if the object is not a child of any node or line", function() {

                        it("should call console.error()", function() {
                            treeMap.unmapChild("0");
                            expect(treeMap.children).toEqual({"0": ["1", "2"]});
                            expect(consoleErrorSpy).toHaveBeenCalled();
                        });
                    });

                    it("should pass an integration test that unmaps all children from parents", function() {
                        expect(testTree.treeMap.children).not.toEqual({});
                        Object.keys(rawTreeCopy).forEach(key => {
                            testTree.treeMap.unmapChild(key);
                        });
                        expect(testTree.treeMap.children).toEqual({}); 
                    });
                });
            });

            describe("line mapping functions", function() {

                let treeMap;

                beforeEach(function() {
                    const tree = {
                        "0": {
                            object: "node",
                            name: "node0"
                        },
                        "1": {
                            object: "node",
                            name: "node1"
                        },
                        "2": {
                            object: "line",
                            name: "line2",
                            from: "node0",
                            to: "node1"
                        },
                        "3": {
                            object: "line",
                            name: "line3",
                            from: "node1",
                            to: "node0"
                        }
                    };
                    treeMap = createTreeMap(tree);
                });
                //good
                describe("mapLine()", function() {

                    describe("if the node hasn't had any line keys mapped to it yet", function() {

                        it("should set this TreeMap.lines[nodeKey] to an array containing the lineKey", function() {
                            treeMap.lines = {};
                            expect(treeMap.lines["0"]).toBeUndefined();
                            expect(treeMap.lines["1"]).toBeUndefined();
                            treeMap.mapLine("2");
                            expect(treeMap.lines["0"]).toEqual(["2"]);
                            expect(treeMap.lines["1"]).toEqual(["2"]);
                        });
                    });

                    describe("if the node has not been mapped to a particular line key", function() {

                        it("should push the line key onto the lines array of the node", function() {
                            treeMap.lines = {};
                            expect(treeMap.lines["0"]).toBeUndefined();
                            expect(treeMap.lines["1"]).toBeUndefined();
                            treeMap.mapLine("2");
                            expect(treeMap.lines["0"]).toEqual(["2"]);
                            expect(treeMap.lines["1"]).toEqual(["2"]);
                            treeMap.mapLine("3");
                            expect(treeMap.lines["0"]).toEqual(["2", "3"]);
                            expect(treeMap.lines["1"]).toEqual(["2", "3"]);
                        });
                    });

                    describe("if the node has already been mapped to a particular line key", function() {

                        it("should not push the line key onto the lines array of the node", function() {
                            treeMap.lines = {};
                            expect(treeMap.lines["0"]).toBeUndefined();
                            expect(treeMap.lines["1"]).toBeUndefined();
                            treeMap.mapLine("2");
                            expect(treeMap.lines["0"]).toEqual(["2"]);
                            expect(treeMap.lines["1"]).toEqual(["2"]);
                            treeMap.mapLine("2");
                            expect(treeMap.lines["0"]).toEqual(["2"]);
                            expect(treeMap.lines["1"]).toEqual(["2"]);
                        });
                    });

                    it("should pass an integration test that maps lines to their nodes", function() {
                        const treeMap = createTreeMap(rawTreeCopy);
                        treeMap.lines = {};
                        Object.keys(rawTreeCopy).forEach(key => {
                            treeMap.mapLine(key);
                        });
                        expect(testTree.treeMap.lines).toEqual(treeMap.lines);
                    });
                });
                //good
                describe("unmapLine()", function() {

                    describe("if the line key exists in the node's array", function() {

                        it("should remove the line key from the array", function() {
                            expect(treeMap.lines["0"]).toEqual(["2", "3"]);
                            treeMap.unmapLine("3");
                            expect(treeMap.lines["0"]).toEqual(["2"]);
                        });
                    });

                    describe("if the object is not connected to any node", function() {

                        it("should call console.error", function() {
                            expect(treeMap.lines["0"]).toEqual(["2", "3"]);
                            treeMap.unmapLine("0");
                            expect(treeMap.lines["0"]).toEqual(["2", "3"]);
                            expect(consoleErrorSpy).toHaveBeenCalled();
                        });
                    });

                    it("should pass an integration test that unmaps every line from its nodes", function() {
                        const treeMap = createTreeMap(rawTreeCopy);
                        expect(treeMap.lines).not.toEqual({});
                        Object.keys(rawTreeCopy).forEach(key => {
                            treeMap.unmapLine(key);
                        });
                        expect(treeMap.lines).toEqual({});
                    });
                });
            });
        });
        //good
        describe("createTree()", function() {

            it("should format all 'longitude' and 'latitude' property values into numbers if they are strings", function() {
                let tree = {
                    "0": {
                        object: "house",
                        longitude: "50",
                        latitude: "50"
                    },
                };
                tree = createTree(tree);
                expect(tree.tree["0"].longitude).toEqual(50);
                expect(tree.tree["0"].latitude).toEqual(50);
            });

            it("should pass an integration test that converts all 'longitude' and 'latitude' property values into numbers", function() {
                Object.keys(rawTreeCopy).forEach(key => {
                    ["longitude", "latitude"].forEach(prop => {
                        if (rawTreeCopy[key][prop] != null) {
                            expect(parseFloat(rawTreeCopy[key][prop])).toEqual(testTree.tree[key][prop]);
                        }
                    });
                });
            });
        });
        // good
        describe("treePrototype", function() {
            
            describe("replaceNode()", function() {

                describe("if the key is not a number string", function() {

                    it("should throw an Error", function() {
                        const tree = createTree({
                            0: {
                                object: "node",
                                name: "node0"
                            }
                        });
                        expect(function() {
                            tree.replaceNode(0, {});
                        }).toThrowError("The key was not a string with a number value.");                      
                    });
                });

                describe("if the key does not exist in the tree", function() {

                    it("should throw an Error", function() {
                        const tree = createTree();
                        expect(function() {
                            tree.replaceNode("999", {});
                        }).toThrowError("The object with the key \"999\" does not exist in the tree.");
                    });
                });

                describe("if the object being replaced is not a node", function() {

                    it("should throw an Error", function() {
                        const tree = createTree({
                            0: {
                                to: "somewhere",
                                from: "nowhere"
                            }
                        });
                        const component = {object: "node"}
                        expect(function() {
                            tree.replaceNode("0", component);
                        }).toThrowError("The object with the key \"0\" is not a node.");
                    });
                });

                describe("if the replacement component is not a node", function() {

                    it("should throw an Error", function() {
                        const tree = createTree({
                            0: {
                                object: "node"
                            }
                        });
                        const component = {
                            to: "somewhere",
                            from: "everywhere"
                        };
                        expect(function() {
                            tree.replaceNode("0", component);
                        }).toThrowError("The replacement component is not a node.");
                    });
                });

                describe("if the replacement component is a configuration node", function() {

                    describe("if the object being replaced is not a configuration node", function() {

                        it("should throw an error", function() {
                            const tree = createTree({
                                0: {
                                    object: "node"
                                }
                            });
                            const component = {
                                module: "omf"
                            };
                            expect(function() {
                                tree.replaceNode("0", component);
                            }).toThrowError("Configuration nodes cannot be used to replace non-configuration nodes.");
                        });
                    });
                });

                describe("if the replacement component has a 'parent' attribute", function() {

                    describe("if the object being replaced has a 'parent' attribute", function() {

                        it("should set the 'parent' attribute of the replacement component to be the same as the 'parent' attribute of the object being replaced", function() {
                            const tree = createTree({
                                0: {
                                    object: "triplex_load",
                                    name: "triplex_load0",
                                    parent: "node1",
                                    latitude: 99,
                                    longitude: 101
                                },
                                1: {
                                    object: "node",
                                    name: "node1"
                                }
                            });
                            const component = {
                                object: "house",
                                parent: null,
                            };
                            tree.replaceNode("0", component);
                            expect(tree.tree[0]).toEqual({
                                object: "house",
                                name: "house0",
                                parent: "node1",
                                latitude: 99,
                                longitude: 101
                            });
                        });
                    });

                    describe("if the object being replaced does not have a 'parent' attribute", function() {

                        it("should remove the 'parent' attribute from the replacement component", function() {
                            const tree = createTree({
                                0: {
                                    object: "node",
                                    name: "node0",
                                    latitude: "55",
                                    longitude: "0"
                                }
                            });
                            const component = {
                                object: "house",
                                parent: "NULL"
                            };
                            tree.replaceNode("0", component);
                            expect(tree.tree[0]).toEqual({
                                object: "house",
                                name: "house0",
                                latitude: 55,
                                longitude: 0
                            });
                        });
                    });
                });

                describe("if the object being replaced has a 'parent' attribute", function() {

                    describe("if the replacement component does not have a 'parent' attribute", function() {
                        
                        it("should add and update the 'parent' attribute on the replacement component", function() {
                            const tree = createTree({
                                0: {
                                    object: "ZIPload",
                                    name: "ZIPload0",
                                    parent: "node1",
                                    latitude: "7",
                                    longitude: "9.001"
                                },
                                1: {
                                    object: "node",
                                    name: "node1"
                                }
                            });
                            const component = {
                                object: "triplex_node"
                            };
                            tree.replaceNode("0", component);
                            expect(tree.tree[0]).toEqual({
                                object: "triplex_node",
                                name: "triplex_node0",
                                parent: "node1",
                                latitude: 7,
                                longitude: 9.001
                            });
                        });
                    });
                });

                it("should update the 'to' and 'from' properties of all lines that connect to the object being replaced", function() {
                    const tree = createTree({
                        0: {
                            object: "triplex_node",
                            name: "triplex_node0"
                        },
                        1: {
                            object: "overhead_line",
                            name: "overhead_line1",
                            to: "triplex_node0",
                            from: "triplex_node2"
                        },
                        2: {
                            object: "triplex_node",
                            name: "triplex_node2",
                        },
                        3: {
                            object: "overhead_line",
                            name: "overhead_line3",
                            to: "triplex_node2",
                            from: "triplex_node0"
                        }
                    });
                    const component = {
                        object: "house"
                    };
                    tree.replaceNode("0", component);
                    expect(tree.tree[1]).toEqual({
                        object: "overhead_line",
                        name: "overhead_line1",
                        to: "house0",
                        from: "triplex_node2"
                    });
                    expect(tree.tree[3]).toEqual({
                        object: "overhead_line",
                        name: "overhead_line3",
                        to: "triplex_node2",
                        from: "house0"
                    });
                });

                it("should update the 'parent' attribute of all children of the object being replaced", function() {
                    const tree = createTree({
                        0: {
                            object: "triplex_node",
                            name: "triplex_node0"
                        },
                        1: {
                            object: "ZIPload",
                            name: "ZIPload1",
                            parent: "triplex_node0"
                        }
                    });
                    const component = {
                        object: "house"
                    }
                    tree.replaceNode("0", component);
                    expect(tree.tree[1]).toEqual({
                        object: "ZIPload",
                        name: "ZIPload1",
                        parent: "house0"
                    });
                });

                it("should call TreeMap.remove() and TreeMap.add()", function() {
                    const tree = createTree({
                        0: {
                            object: "node",
                            name: "node0"
                        }
                    });
                    const component = {
                        object: "load"
                    };
                    const spy1 = spyOn(treeMapPrototype, "remove").and.callThrough();
                    const spy2 = spyOn(treeMapPrototype, "add").and.callThrough();
                    tree.replaceNode("0", component);
                    expect(spy1).toHaveBeenCalledWith(["0"]);
                    expect(spy2).toHaveBeenCalledWith("0");
                });

                it("should copy the latitude and longitude of the object being replaced to the replacement component", function() {
                    const tree = createTree({
                        0: {
                            object: "node",
                            name: "node0",
                            latitude: 100,
                            longitude: 100
                        }
                    });
                    const component = {
                        object: "load"
                    };
                    tree.replaceNode("0", component);
                    expect(tree.tree[0]).toEqual({
                        object: "load",
                        name: "load0",
                        latitude: 100,
                        longitude: 100
                    });
                });

                it("should set the name of the replacement component to include the key of the object being replaced", function() {
                    const tree = createTree({
                        1077: {
                            object: "node",
                            name: "node1077",
                            latitude: 0,
                            longitude: 18
                        }
                    });
                    const component = {
                        object: "house"
                    };
                    tree.replaceNode("1077", component);
                    expect(tree.tree[1077]).toEqual({
                        object: "house",
                        name: "house1077",
                        latitude: 0,
                        longitude: 18
                    });
                });

                it("should set the key of the replacement component to be the same as the key of the object being replaced", function() {
                    const tree = createTree({
                        779977: {
                            object: "windmill",
                            name: "windmill779977",
                            latitude: 56,
                            longitude: 10
                        }
                    });
                    const component = {
                        object: "volcano"
                    };
                    tree.replaceNode("779977", component);
                    expect(tree.tree).toEqual({
                        779977: {
                            object: "volcano",
                            name: "volcano779977",
                            latitude: 56,
                            longitude: 10
                        }
                    });
                });

                it("should insert a copy of the replacement component into the tree instead of the original replacement component", function() {
                    const tree = createTree({
                        11: {
                            object: "node",
                            name: "node11"
                        }
                    });
                    const component = {
                        object: "nuclear power plant"
                    };
                    tree.replaceNode("11", component);
                    expect(tree.tree[11]).not.toBe(component);
                });

                describe("if a configuration node is replacing another configuration node", function() {

                    it("should not add the 'name' attribute to the incoming component object", function() {
                        const tree = createTree({
                            0: {
                                omftype: "module",
                                longitude: 4,
                                latitude: .701
                            }
                        })
                        const component = {
                            omftype: "#include"
                        }
                        tree.replaceNode("0", component);
                        expect(tree.tree[0]).toEqual({
                            omftype: "#include",
                            longitude: 4,
                            latitude: .701
                        });
                    });
                });
            });
            
            describe("getObject()", function() {

                it("should throw an exception if the key doesn't exist in the tree", function() {
                    const tree = createTree();
                    expect(function() {
                        tree.getObject("100");
                    }).toThrowError(`The object with the key "100" does not exist in the tree.`)
                });

                it("should return an object in the tree", function() {
                    let tree = {
                        "0": {}
                    };
                    tree = createTree(tree);
                    expect(tree.getObject("0")).toBe(tree.tree["0"]);
                });
            });
            
            describe("insert()", function() {

                describe("if the TreeObject does not match a corresponding tree object in the tree", function() {

                    it(`should add the data of the TreeObject argument to this Tree`, function() {
                        const map = {
                            "parent": "house172645", 
                            "name": "waterheater444555666", 
                            "object": "waterheater", 
                            "longitude": 233.258917459014, 
                            "latitude": 800.489571934734, 
                        }
                        const tree = createTree();
                        const tObj = createTreeObject(map, tree);
                        expect(Object.keys(tree.tree).length).toEqual(0);
                        tree.insert(tObj);
                        expect(Object.keys(tree.tree).length).toEqual(1);
                        expect(tree.tree["0"]).toBe(tObj.data);
                    });
                });
    
                describe(`if a tree object with an identical key to the TreeObject already exists in this TreeWrapper`, function() {

                    it(`should overwrite the tree object data with data from the TreeObject`, function() {
                        let tree = {
                            "0": {
                                object: "node",
                                name: "node0"
                            }
                        };
                        tree = createTree(tree);
                        const tObject = createTreeObject("0", tree);
                        const map = {
                            object: "house",
                            name: "house57" 
                        };
                        tObject.data = map;
                        tree.insert(tObject);
                        expect(tree.tree["0"]).toBe(tObject.data);
                    });
                });
            });
            
            describe("isRemovable()", function() {

                let tree;

                beforeEach(function() {
                    tree = {
                        "0": {//parent
                            object: "node",
                            name: "node0"
                        },
                        "1": {//child
                            object: "house",
                            name: "house1",
                            parent: "node0"
                        },
                        "2": {//independent node
                            object: "node",
                            name: "node2"
                        },
                        "3": {//independent node
                            object: "node",
                            name: "node3"
                        },
                        "4": {//line
                            object: "line",
                            name: "line4",
                            from: "node2",
                            to: "node3"
                        },
                        "5": {//child
                            object: "recorder",
                            name: "recorder5",
                            parent: "line4"
                        },
                        "6": {//line
                            object: "line",
                            name: "line6",
                            from: "node3",
                            to: "node2"
                        }
                    };
                    tree = createTree(tree);
                });

                it("should return false if the tree object has children", function() {
                    expect(tree.isRemovable("0")).toBe(false);
                    expect(tree.isRemovable("4")).toBe(false);
                });

                it("should return false if the tree object has connected lines", function() {
                    expect(tree.isRemovable("2")).toBe(false);
                    expect(tree.isRemovable("3")).toBe(false);
                });

                it("should return true if the tree object has neither connected lines nor children", function() {
                    expect(tree.isRemovable("1")).toBe(true);
                    expect(tree.isRemovable("6")).toBe(true);
                });
            });
            
            describe("getSubtreeToRemove()", function() {

                describe("if the tree object has connected lines and/or children", function() {

                    it("it should return the keys of 1) lines that connect to this object 2) children of this object 3) children of children and any lines that connect to any children", function() { 
                        const keysToDelete = [
                            node3Line1EndChild1,
                            node3Line1EndChild2,
                            node3Line1EndChild3,
                            node3Line1,
                            funkyLine1,
                            funkyLine2,
                            node3Line1EndChild1Child1,
                            node3Line1EndChild1Child2,
                            node3Line1EndChild2Child1,
                            childOfLine,
                        ];
                        const keys = testTree.getSubtreeToRemove(node3Line1End).sort();
                        expect(keys).toEqual(keysToDelete.sort());
                    });

                    it(`should not recurse infinitely if a cycle exists in the graph`, function() {
                        let tree = {
                            "1": {
                                "parent": "node226",
                                "name": "node134", 
                                "object": "triplex_meter", 
                                "longitude": 110.54543561193137, 
                                "latitude": 650.800448635241
                            }, 
                            "2": {
                                "parent": "node134", 
                                "name": "node226", 
                                "object": "ZIPload", 
                                "longitude": 93.65197702537034, 
                                "latitude": 1011.8227442648296, 
                            },
                            "3": {
                                "name": "whatever"
                            }
                        };
                        tree = createTree(tree);
                        expect(tree.getSubtreeToRemove("1")).toEqual(["2", "1"]);
                    });
                });
            });
        });
        //good
        describe("createTreeObject()", function() {

            describe("if invoked with (key, tree) arguments", function() {

                it("should return a TreeObject with the passed key", function() {
                    let tree = {
                        1010: {
                            prop: "custom value"
                        }
                    };
                    tree = createTree(tree); 
                    const tObj = createTreeObject("1010", tree);
                    expect(tObj.key).toEqual("1010");
                });

                it("should return a TreeObject with data that is equivalent to the tree object, but not the same object", function() {
                    let tree = {
                        1010: {
                            prop: "custom value",
                            longitude: 50.1,
                            latitude: .77
                        }
                    };
                    tree = createTree(tree);
                    const tObj = createTreeObject("1010", tree);
                    expect(tObj.data).not.toBe(tree.tree[tObj.key]);
                    expect(tObj.data).toEqual(tree.tree[tObj.key]);
                });

                it("should throw an error if the key argument doesn't exist in the treeWrapper argument", function() {
                    expect(function() {
                        createTreeObject("10", createTree());
                    }).toThrowError(`The object with the key "10" does not exist in the tree.`);
                });

                it("should throw an error if the key argument is not a string", function() {
                    expect(function() {
                        createTreeObject(10, createTree());
                    }).toThrowError("TreeObject creation failed. The 'input' argument must be a string or an object."); 
                });

                it("should throw an error if the tree object has a string value stored at its 'longitude' or 'latitude' property",
                function() {
                    const tree = createTree();
                    tree.tree["0"] = {
                        object: "node",
                        longitude: "50",
                        latitude: "50"
                    }
                    expect(function() {
                        createTreeObject("0", tree);
                    }).toThrowError(`TreeObject creation failed. The tree object with key: "0" has a string value for its "longitude" property.`);
                });
            });

            describe("if invoked with (map, tree) arguments", function() {

                describe("if the map has 'longitude' and 'latitude' properties", function() {

                    it("should set the 'longitude' and 'latitude' to be numbers if they are strings", function() {
                        const map = {
                            object: "node",
                            longitude: "50",
                            latitude: "50",
                            name: "Charlie"
                        };
                        const tObject = createTreeObject(map, createTree());
                        expect(tObject.data.longitude).toEqual(50);
                        expect(tObject.data.latitude).toEqual(50);
                    });
                });

                it("should return a TreeObject with data that is equivalent to the map (except for the name), but not the same object", function() {
                    const map = {
                        object: "thing",
                        name: "Jefferson"
                    }
                    const tObj = createTreeObject(map, createTree());
                    expect(tObj.data).not.toBe(map);
                    expect(tObj.data).toEqual({
                        object: "thing",
                        name: "Jefferson_0"
                    });
                });

                it("should return a TreeObject with a key that does not exist in the treeWrapper.tree", function() {
                    let tree = {
                        0: {}
                    };
                    tree = createTree(tree);
                    const component = {
                        object: "object",
                        name: "name"
                    }
                    const tObj = createTreeObject(component, tree);
                    expect(tObj.key).toEqual("1");
                });

                it("should call getNewTreeKey()", function() {
                    const spy = spyOn(window, "getNewTreeKey").and.callThrough();
                    const tree = createTree();
                    expect(spy).not.toHaveBeenCalled();
                    const component = {
                        object: "object",
                        name: "name"
                    }
                    createTreeObject(component, tree);
                    expect(spy).toHaveBeenCalled();
                });

                /* This assumes all components have a name property, which they do */
                it(`should set the 'name' property to be a concatenation of the components's 'name' property and the id (<name>_<id>)`, function() {
                    const tree = createTree();
                    let component = {
                        object: "load",
                        name: "x346R"
                    };
                    let tObject = createTreeObject(component, tree);
                    tree.insert(tObject);
                    expect(tObject.data.name).toEqual("x346R_0");
                    component = {
                        object: "meter",
                        name: "meter"
                    };
                    tObject = createTreeObject(component, tree);
                    expect(tObject.data.name).toEqual("meter_1");
                });
            });
        });
        // good
        describe("svgDataPrototype", function() {

            describe("setSubtreetoRedraw()", function() {

                describe("if the an object in the primaryKeySet has children", function() {

                    it("should update the subtreeKeySet to include keys of children of nodes", function() {
                        const keys = [
                            node3Line1EndChild1,//parent
                            node3Line1EndChild1Child1,//child
                            node3Line1EndChild1Child2,//child
                            node3Line1End,//grandparent
                            node3Line1EndChild2,//sibling
                            funkyLine1//line between parent and sibling
                        ];
                        const svg = createSvgData([node3Line1EndChild1], testTree);
                        expect(Array.from(svg.primaryKeySet)).toEqual([node3Line1EndChild1]);
                        expect(Array.from(svg.subtreeKeySet)).toEqual([node3Line1EndChild1]);
                        svg.setSubtreeToRedraw();
                        expect(Array.from(svg.primaryKeySet)).toEqual([node3Line1EndChild1]);
                        const subtreeKeys = Array.from(svg.subtreeKeySet).sort();
                        expect(subtreeKeys).toEqual(keys.sort());
                    });

                    it("should update the subtreeKeySet to include keys of children of lines", function() {
                        const keys = [
                            node3Line1,//line
                            node3,//source
                            node3Line1End,//target
                            childOfLine//childOfLine
                        ];
                        const svg = createSvgData([node3Line1], testTree);
                        expect(Array.from(svg.primaryKeySet)).toEqual([node3Line1]);
                        expect(Array.from(svg.subtreeKeySet)).toEqual([node3Line1]);
                        svg.setSubtreeToRedraw();
                        expect(Array.from(svg.primaryKeySet)).toEqual([node3Line1]);
                        const subtreeKeys = Array.from(svg.subtreeKeySet).sort();
                        expect(subtreeKeys).toEqual(keys.sort());
                    });
                });

                describe("if an object in the primaryKeySet has a parent", function() {

                    it("should update the subtreeKeySet to include the key of the parent node", function() {
                        const keys = [
                            node2Line2EndChild1,//child
                            node2Line2End//parent
                        ];
                        const svg = createSvgData([node2Line2EndChild1], testTree);
                        expect(Array.from(svg.primaryKeySet)).toEqual([node2Line2EndChild1]);
                        expect(Array.from(svg.subtreeKeySet)).toEqual([node2Line2EndChild1]);
                        svg.setSubtreeToRedraw();
                        expect(Array.from(svg.primaryKeySet)).toEqual([node2Line2EndChild1]);
                        const subtreeKeys = Array.from(svg.subtreeKeySet).sort();
                        expect(subtreeKeys).toEqual(keys.sort());
                    });

                    it("should update the subtreeKeySet to include the key of a parent line, and nodes on either end of that line", function() {
                        const keys = [
                            childOfLine,//childOfLine
                            node3Line1,//line
                            node3,//source
                            node3Line1End,//target
                        ];
                        const svg = createSvgData([childOfLine], testTree);
                        expect(Array.from(svg.primaryKeySet)).toEqual([childOfLine]);
                        expect(Array.from(svg.subtreeKeySet)).toEqual([childOfLine]);
                        svg.setSubtreeToRedraw();
                        expect(Array.from(svg.primaryKeySet)).toEqual([childOfLine]);
                        const subtreeKeys = Array.from(svg.subtreeKeySet).sort();
                        expect(subtreeKeys).toEqual(keys.sort());
                    });
                });

                describe("if an object in the primaryKeySet is a line", function() {

                    it("should update the subtreeKeySet to include the nodes on either end of the line", function() {
                        const keys = [
                            lineToLoad,//line
                            node1Line2EndChild1,//source
                            node2Line2End//target
                        ];
                        const svg = createSvgData([lineToLoad], testTree);
                        expect(Array.from(svg.primaryKeySet)).toEqual([lineToLoad]);
                        expect(Array.from(svg.subtreeKeySet)).toEqual([lineToLoad]);
                        svg.setSubtreeToRedraw();
                        expect(Array.from(svg.primaryKeySet)).toEqual([lineToLoad]);
                        const subtreeKeys = Array.from(svg.subtreeKeySet).sort();
                        expect(subtreeKeys).toEqual(keys.sort());
                    });
                });

                describe("if an object in the primaryKeySet has connected lines", function() {

                    it("should update the subtreeKeySet to include those lines, the nodes on the other ends of those lines, and children of those lines", function() {
                        const keys = [
                            node3Line1End,//need to include the own object, because it is included in the subtreeKeySet
                            node3,
                            node3Line1,
                            childOfLine,
                            node3Line1EndChild1, 
                            node3Line1EndChild2, 
                            node3Line1EndChild3 
                        ];
                        const svg = createSvgData([node3Line1End], testTree);
                        expect(Array.from(svg.primaryKeySet)).toEqual([node3Line1End]);
                        expect(Array.from(svg.subtreeKeySet)).toEqual([node3Line1End]);
                        svg.setSubtreeToRedraw();
                        expect(Array.from(svg.primaryKeySet)).toEqual([node3Line1End]);
                        const subtreeKeys = Array.from(svg.subtreeKeySet).sort();
                        expect(subtreeKeys).toEqual(keys.sort());
                    });
                });
            });
            
            describe("createData()", function() {

                it("should only create parent-child lines for childNodes whose parent is in the subtreeKeySet", function() {
                    // This will solve the problem of updating the parent-child lines of to/from ends of primaryKeySet lines objects, which I don't want
                    const svg = createSvgData([lineToLoad], testTree);
                    svg.setSubtreeToRedraw();
                    svg.createData();
                    const circleIds = svg.circles.map(circle => circle.id).sort();
                    const lineIds = svg.lines.map(line => line.id).sort();
                    const parentChildIds = svg.parentChildLines.map(line => line.id).sort();
                    expect(circleIds).toEqual([node1Line2EndChild1, node2Line2End].sort());
                    expect(lineIds).toEqual([lineToLoad]);
                    expect(parentChildIds).toEqual([]);
                });

                it("should only create parent-child lines for childNodes whose parent is in the subtreeKeySet", function() {
                    // This will solve the problem of updating the parent-child lines of parents of primaryKeySet node objects, which I don't want
                    const svg = createSvgData([node3Line1EndChild2Child1], testTree);
                    svg.setSubtreeToRedraw();
                    svg.createData();
                    const circleIds = svg.circles.map(circle => circle.id).sort();
                    const lineIds = svg.lines.map(line => line.id).sort();
                    const parentChildIds = svg.parentChildLines.map(line => line.id).sort();
                    expect(circleIds).toEqual([node3Line1EndChild2Child1, node3Line1EndChild2].sort());
                    expect(lineIds).toEqual([]);
                    expect(parentChildIds).toEqual([`172260_172261`]); 
                });
            });
        });
        //bad
        describe("componentManagerPrototype", function() {
            //good
            describe("insert()", function() {

                describe("if a component has the 'object' and 'name' properties", function() {

                    describe("if the component has a unique name", function() {

                        it("should insert the component based on its 'object' and 'name' properties", function() {
                            const component = {
                                object: "Geothermal plant",
                                name: "XX9922-114"
                            };
                            const cm = createComponentManager();
                            cm.insert(component);
                            expect(cm.components[component.object][component.name]).toEqual(component);
                            expect(Object.keys(cm.components).length).toEqual(1);
                            expect(Object.keys(cm.components[component.object]).length).toEqual(1);
                        });
                    });

                    describe("if the component has a non-unique name", function() {
                        
                        /* Components themselves need to have unique names. A specific component is retrieved based on its object and name properties. If two components have the same name, which one is returned? Ideally, the .json files are written well enough so that this never becomes an issue. Now that components are guaranteed to have unique names, graph objects ALSO need unique names that are also descriptive. The naming convention for graph objects is "<name>_<tree key>". Two components COULD have the same name, and when added those components would be unique graph objects. However, this wouldn't solve the first problem of retreiving the correct component. Therefore, components themselves must have unique names.
                        */
                        it("should insert the component based on its 'object' property and its new assigned name", function() {
                            const component = {
                                object: "Geothermal plant",
                                name: "XX9922-114"
                            };
                            const components = [];
                            for (let i = 0; i < 5; i++) {
                                let copy = deepCopy(component);
                                components.push(copy);
                            }
                            const cm = createComponentManager();
                            components.forEach(c => cm.insert(c));
                            expect(Object.keys(cm.components).length).toEqual(1);
                            expect(Object.keys(cm.components[component.object]).length).toEqual(5);
                            for (let i = 1; i < 5; i++) {
                                expect(cm.components[component.object][`${component.name}_${i}`]).toBeDefined();
                            }
                        });
                    });
                });

                describe("if a component is missing the 'object' property", function() {

                    it("should alert the user", function() {
                        const spy = spyOn(window, "alert");
                        const component = {name: "Joe"};
                        const cm = createComponentManager();
                        cm.insert(component);
                        expect(spy).toHaveBeenCalled();
                        expect(cm.components).toEqual({});
                    });
                });

                describe("if a component is missing the 'name' property", function() {

                    it("should assign the component a name based on its 'object' property and insert it", function() {
                        const component = {object: "load"};
                        const component2 = {object: "load"};
                        const cm = createComponentManager();
                        cm.insert(component);
                        cm.insert(component2);
                        expect(Object.keys(cm.components).length).toEqual(1)
                        expect(Object.keys(cm.components[component.object]).length).toEqual(2);
                        expect(cm.components["load"]["load"]).toBe(component);
                        expect(component.name).toEqual("load");
                        expect(cm.components["load"]["load_1"]).toBe(component2);
                        expect(component2.name).toEqual("load_1");
                    });
                })
            });
        });
        //good
        describe("insertCoordinates()", function() {

            describe("if an object does not contain 'longitude' and/or 'latitude' properties", function() {

                describe(`if an object has a type of "line"`, function() {

                    it("should not add coordinates", function() {
                        const line = {
                            from: "someNode",
                            to: "otherNode"
                        };
                        insertCoordinates([line], 0, 0, 5);
                        expect(line.longitude).toBeUndefined();
                        expect(line.latitude).toBeUndefined();
                    });
                });

                it("it should pass an integration test that adds coordinates to objects", function() {
                    const tree = {
                        "0": {},
                        "1": {},
                        "2": {},
                        "3": {},
                        "4": {},
                        "5": {},
                        "6": {}
                    };
                    const distance = 101, initX = 52, initY = 53;
                    insertCoordinates(Object.values(tree), initX, initY, distance);
                    expect(tree[0].longitude).toEqual(initX);
                    expect(tree[0].latitude).toEqual(initY);
                    expect(tree[1].longitude).toEqual(initX);
                    expect(tree[1].latitude).toEqual(initY + distance);
                    expect(tree[2].longitude).toEqual(initX + distance);
                    expect(tree[2].latitude).toEqual(initY + distance);
                    expect(tree[3].longitude).toEqual(initX + distance);
                    expect(tree[3].latitude).toEqual(initY);
                    expect(tree[4].longitude).toEqual(initX);
                    expect(tree[4].latitude).toEqual(initY + (2 * distance));
                    expect(tree[5].longitude).toEqual(initX + distance);
                    expect(tree[5].latitude).toEqual(initY + (2 * distance));
                    expect(tree[6].longitude).toEqual(initX + (2 * distance));
                    expect(tree[6].latitude).toEqual(initY + (2 * distance));
                });
            });
        });
        //good
        describe("move()", function() {

            describe("if handling an object that is a line", function() {

                it("should not add 'longitude' or 'latitude' properties to the line", function() {
                    const line = {
                        from: "someNode",
                        to:"otherNode"
                    };
                    move([line], 100, 100);
                    expect(line.longitude).toBeUndefined();
                    expect(line.latitude).toBeUndefined();
                });

                it("should not modify existing 'longitude' or 'latitude' properties on the line", function() {
                    const line = {
                        from: "someNode",
                        to: "otherNode",
                        latitude: 0,
                        longitude: 0
                    };
                    move([line], 200, 200);
                    expect(line.longitude).toEqual(0);
                    expect(line.latitude).toEqual(0);
                });
            });

            describe("if handling an object that is a node", function() {

                it(`should translate each node`, function() {
                    const offsetX = -101.8876,
                        offsetY = -2.00033,
                        x = 117.8,
                        y = -27.01,
                        scaleFactor = .065,
                        avgLon = 2.5,
                        avgLat = 2.5,
                        tree = {
                            "0": {
                                longitude: 0,
                                latitude: 0
                            },
                            "1": {
                                longitude: 5,
                                latitude: 0
                            },
                            "2": {
                                longitude: 0,
                                latitude: 5
                            },
                            "3": {
                                longitude: 5,
                                latitude: 5
                            },
                            "4": {
                                from: "someNode",
                                to: "otherNode",
                                longitude: 1000.333,
                                latitude: NaN
                            }
                        };
                    /*
                    Average longitude of all 4 nodes: (0 + 5 + 0 + 5)/4 = 2.5
                    Average latitude of all 4 nodes: (0 + 0 + 5 + 5)/4 = 2.5
                    etc.
                    */
                    move(Object.values(tree), {x: x, y: y}, {offsetX: offsetX, offsetY: offsetY, scaleFactor: scaleFactor});
                    expect(tree[0].longitude).toEqual(x/scaleFactor - avgLon + offsetX);
                    expect(tree[0].latitude).toEqual(offsetY - avgLat - y/scaleFactor);
                    expect(tree[1].longitude).toEqual(5 + x/scaleFactor - avgLon + offsetX);
                    expect(tree[1].latitude).toEqual(offsetY - avgLat - y/scaleFactor);
                    expect(tree[2].longitude).toEqual(x/scaleFactor - avgLon + offsetX);
                    expect(tree[2].latitude).toEqual(5 - avgLat + offsetY - y/scaleFactor);
                    expect(tree[3].longitude).toEqual(5 + x/scaleFactor - avgLon + offsetX);
                    expect(tree[3].latitude).toEqual(5 - avgLat + offsetY - y/scaleFactor);
                    expect(tree[4].longitude).toEqual(1000.333);
                    expect(tree[4].latitude).toEqual(NaN);
                });
            });
        });
        
        describe("selectionPrototype", function() {
            //good
            describe("remove()", function() {

                describe("if there are 0 HTMLElements in this selection that 1) are equal in identify to the HTMLElement argument or 2) have the same id as the HTMLElement argument", function() {

                    it("should throw an error", function() {
                        const selection = createSelection();
                        const table = document.createElement("table");
                        expect(function() {
                            selection.remove(table)
                        }).toThrowError(`Remove operation failed. The element "TABLE" does not exist in this selection.`);
                    });
                });

                describe("if there are 1 or more HTMLElements in this selection that 1) are equal in identify to the HTMLElement argument or 2) have the same id as the HTMLElement argument", function() {

                    it("should delete all matching HTMLElements from this selection", function() {
                        const selection = createSelection();
                        const table = document.createElement("table");
                        table.id = "item";
                        selection.add(table);
                        const div = document.createElement("div");
                        div.id = "item";
                        selection.add(div);
                        expect(selection.selectedElements.includes(table)).toBe(true);
                        expect(selection.selectedElements.includes(div)).toBe(true);
                        selection.remove(table);
                        expect(selection.selectedElements.length).toEqual(0);
                    });
                });
            });
        });

        describe("Public utility methods", function() {
            //good
            describe("isNumberString()", function() {

                describe("if the 'str' argument is a string that can be parsed to a valid decimal or floating point number",
                function() {

                    it("should return true", function() {
                        const valid = [
                            "1",
                            "1.001",
                            "0.12"
                        ];
                        valid.forEach(num => {
                            expect(isNumberString(num)).toBe(true);
                        });
                    });
                });

                describe("if the 'str' argument is not a string", function() {

                    it("should return false", function() {
                        const invalid = [
                            false,
                            true,
                            null,
                            undefined,
                            Infinity,
                            NaN,
                            0,
                            1
                        ];
                        invalid.forEach(num => {
                            expect(isNumberString(num)).toBe(false);
                        });
                    });
                });

                describe("if the 'str' argument contains whitespace", function() {

                    it("should return false", function() {
                        const invalid = [
                            "1  ",
                            "  1",
                            " 1 "
                        ];
                        invalid.forEach(num => {
                            expect(isNumberString(num)).toBe(false);
                        });
                    });
                });

                describe("if the 'str' argument is a string that cannot be parsed to a valid, finite number", function() {

                    it("should return false", function() {
                        const invalid = [
                            "",
                            " ",
                            "true",
                            "1.2.3",
                            "1-2-3"
                        ];
                        invalid.forEach(num => {
                            expect(isNumberString(num)).toBe(false);
                        });
                    });
                });
            });
            //good
            describe("deepCopy()", function() {

                it("should throw an error if the object being copied contains a method", function() {
                    const obj = {
                        prop1: "a",
                        prop2: function() {}
                    };
                    expect(function() {
                        deepCopy(obj);
                    }).toThrowError();
                });
    
                it("should throw an error if the object being copied was created with a constructor function", function() {
                    function myObj() {
                        this.prop = 5;
                    }
                    const obj = new myObj();
                    expect(function() {
                        deepCopy(obj);
                    }).toThrowError();
                });
    
                it("should throw an error if the argument object has an undefined value", function() {
                    const obj = {
                        foo: undefined,
                        bar: 2
                    };
                    expect(function() {
                        deepCopy(obj)
                    }).toThrowError();
                });
    
                it("should produce a deep copy of a basic object", function() {
                    const obj1 = {
                        prop1: "a",
                        prop2: {
                            prop1: 123,
                            prop2: {
                                prop1: true,
                                prop2: ["10", 11, false]
                            }
                        }
                    };
                    const copy = deepCopy(obj1)
                    expect(copy).toEqual(obj1);
                    expect(copy).not.toBe(obj1);
                    expect(copy.prop2.prop2.prop2).toEqual(["10", 11, false]);
                    expect(copy.prop2.prop2.prop2).toEqual(obj1.prop2.prop2.prop2);
                    expect(copy.prop2.prop2.prop2).not.toBe(obj1.prop2.prop2.prop2);
                });
            });
            //good
            describe("getNewTreeKey()", function() {

                it(`should return a string that is a valid number`, function() {
                    const key1 = getNewTreeKey({});
                    expect(isNumberString(key1)).toBe(true);
                });
    
                it("should return a key that doesn't exist in the passed tree argument", function() {
                    const key1 = getNewTreeKey({});
                    expect(key1).toEqual("0");
                    const key2 = getNewTreeKey(testTree.tree);
                    expect(key2).toEqual(Object.keys(testTree.tree).length.toString());
                });
            });
            //good
            describe("getRelationship()", function() {
                // This should basically never happen, but you never know
                describe("if the object argument is a line and a configuration node", function() {
    
                    it("should return 'line'", function() {
                        spyOn(window, "isLine").and.returnValue(true);
                        spyOn(window, "isChildNode").and.returnValue(false);
                        spyOn(window, "isConfigurationNode").and.returnValue(true);
                        expect(getRelationship({})).toEqual("line");
                    });
                });
                // This should also never happen
                describe("if the object argument is a child node and a configuration node", function() {
    
                    it("should return 'configurationNode'", function() {
                        spyOn(window, "isLine").and.returnValue(false);
                        spyOn(window, "isChildNode").and.returnValue(true);
                        spyOn(window, "isConfigurationNode").and.returnValue(true);
                        expect(getRelationship({})).toEqual("configurationNode");
                    });
                });
    
                describe("if the object is not a line, nor a child node, nor a configuration node", function() {

                    it("should return 'independentNode'", function() {
                        spyOn(window, "isLine").and.returnValue(false);
                        spyOn(window, "isChildNode").and.returnValue(false);
                        spyOn(window, "isConfigurationNode").and.returnValue(false);
                        expect(getRelationship({})).toEqual("independentNode");
                    });
                });
            });
            //good
            describe("getMinMax()", function() {

                it("should return the minimum and maximum numeric values of a single object", function() {
                    const obj = {
                        prop0: NaN,
                        prop1: "100",
                        prop2: "44",
                        prop3: "100.0000001",
                        prop4: "43.999999"
                    };
                    const {min, max} = getMinMax({object: obj});
                    expect(min).toEqual(43.999999);
                    expect(max).toEqual(100.0000001);
                });

                it("should return the minimum and maximum nuermic values across all objects inside of an object", function() {
                    const objectContainer = {
                        prop0: {
                            longitude: NaN,
                            latitude: NaN
                        },
                        prop1: {
                            longitude: "100",
                            latitude: "0"
                        },
                        prop2: {
                           longitude: "27",
                           latitude: "101"
                        },
                        prop3: {
                            longitude: "-2",
                            latitude: "500"
                        },
                        prop4: {
                            longitude: "6",
                            latitude: "-100"
                        }
                    };
                    const minMax = getMinMax({objectContainer: objectContainer, properties: ["longitude", "latitude"]});
                    expect(minMax.longitude.min).toEqual(-2);
                    expect(minMax.longitude.max).toEqual(100);
                    expect(minMax.latitude.min).toEqual(-100);
                    expect(minMax.latitude.max).toEqual(500);
                });
            });
        });

        describe("opacityManagerPrototype", function() {
            //good
            describe("setAlpha()", function() {

                let nodeElement;

                beforeEach(function() {
                    nodeElement = document.getElementById(node1);
                    nodeElement.removeAttribute("style");
                });

                describe("if the rgb values of the inline circle.style.fill attribute do not match the rgb values of the default CSS circle.style.fill attribute", function() {

                    it("should preserve the inline circle.style.fill rgb values but apply the new alpha value", function() {
                        const opacityManager = createOpacityManager();
                        ["rgb(66, 66, 66)", "rgba(66, 66, 66, 0.055)"].forEach(str => {
                            nodeElement.style.fill = str;
                            expect(nodeElement.style.fill).toEqual(str);
                            opacityManager.setAlpha({className:"node", value:"0.2"});
                            expect(nodeElement.style.fill).toEqual("rgba(66, 66, 66, 0.2)");
                            opacityManager.setAlpha({className:"node", value:"1"});
                            expect(nodeElement.style.fill).toEqual("rgb(66, 66, 66)");
                        });
                    });
                });

                describe("if setting the alpha on a circle element to 1", function() {

                    describe("if the circle lacks the style attribute", function() {

                        it("should not add the style attribute to the circle", function() {
                            const opacityManager = createOpacityManager();
                            expect(nodeElement.style.fill).toEqual("");
                            opacityManager.setAlpha({className:"node", value:"1"});
                            expect(nodeElement.style.fill).toEqual("");
                        });
                    });

                    describe("if the rgb values of the inline circle.style.fill attribute match the rgb values of the default CSS circle.style.fill attribute", function() {

                        it("should remove the style attribute from the circle", function() {
                            const opacityManager = createOpacityManager();
                            ["rgb(128, 128, 128)", "rgba(128, 128, 128, 0.055)"].forEach(str => {
                                nodeElement.style.fill = str;
                                expect(nodeElement.style.fill).toEqual(str);
                                opacityManager.setAlpha({className:"node", value:"1"});
                                expect(nodeElement.style.fill).toEqual("");                            
                            });
                        });
                    });
                });

                describe("if setting the alpha on a circle element to anything other than 1", function() {

                    describe("if the circle lacks the style attribute", function() {

                        it("should set the inline circle.style.fill value to equal the default CSS circle.style.fill value with the alpha", function() {
                            const opacityManager = createOpacityManager();
                            expect(nodeElement.style.fill).toEqual("");
                            opacityManager.setAlpha({className:"node", value:"0.043"});
                            expect(nodeElement.style.fill).toEqual("rgba(128, 128, 128, 0.043)");
                        });
                    });
                });
            });
        });

        describe("colorMapPrototype", function() {
            // good
            describe("color()", function() {

                let nodeElement, nodeName;

                beforeEach(function() {
                    spyOn(window, "alert");
                    nodeElement = document.getElementById(node1);
                    nodeElement.removeAttribute("style");
                    nodeName = "nodeT10263825298";
                });

                describe("if the circle element has an inline style.fill attribute with an alpha value", function() {

                    it("should preserve the alpha value on the new color", function() {
                        const color = "rgba(66, 66, 66, 0.05)"; 
                        nodeElement.style.fill = color;
                        expect(nodeElement.style.fill).toEqual(color);
                        const colorMap = createColorMap("columnTitle", "colorFileTitle");
                        colorMap.colorMap[nodeName] = "rgb(55, 107, 23)";
                        colorMap.color();
                        expect(nodeElement.style.fill).toEqual("rgba(55, 107, 23, 0.05)");
                    });
                });

                describe("if the circle element has an inline style.fill attribute without an alpha value", function() {

                    it("should apply the new color", function() {
                        const color = "rgb(66, 66, 66)";
                        nodeElement.style.fill = color;
                        expect(nodeElement.style.fill).toEqual(color);
                        const colorMap = createColorMap("columnTitle", "colorFileTitle");
                        colorMap.colorMap[nodeName] = "rgb(55, 107, 23)";
                        colorMap.color();
                        expect(nodeElement.style.fill).toEqual("rgb(55, 107, 23)");
                    });
                });

                describe("if the circle element does not have an inline style.fill attribute", function() {

                    it("should apply the new color", function() {
                        expect(nodeElement.style.fill).toEqual("");
                        const colorMap = createColorMap("columnTitle", "colorFileTitle");
                        colorMap.colorMap[nodeName] = "rgb(55, 107, 23)";
                        colorMap.color();
                        expect(nodeElement.style.fill).toEqual("rgb(55, 107, 23)"); 
                    });
                });
            });
        });

        describe("colorManagerPrototype", function() {
            //good
            describe("removeColors()", function() {

                let nodeElement;

                beforeEach(function() {
                    nodeElement = document.getElementById(node1);
                    nodeElement.removeAttribute("style");
                });

                describe("if the circle element has an inline alpha value", function() {

                    it("should apply the default CSS styling while preserving the inline alpha value", function() {
                        const color = "rgba(66, 66, 66, 0.4)";
                        nodeElement.style.fill = color;
                        expect(nodeElement.style.fill).toEqual(color);
                        const colorManager = createColorManager();
                        colorManager.removeColors();
                        expect(nodeElement.style.fill).toEqual("rgba(128, 128, 128, 0.4)");
                    });
                });

                describe("if the circle element does not have an inline alpha value", function() {

                    it("should apply the default CSS styling", function() {
                        const color = "rgb(66, 66, 66)";
                        nodeElement.style.fill = color;
                        expect(nodeElement.style.fill).toEqual(color);
                        const colorManager = createColorManager();
                        colorManager.removeColors();
                        expect(nodeElement.style.fill).toEqual("");
                    });
                });

                describe("if the circle element does not have any inline style.fill value", function() {

                    it("should not set the inline style.fill attribute", function() {
                        expect(nodeElement.style.fill).toEqual("");
                        const colorManager = createColorManager();
                        colorManager.removeColors();
                        expect(nodeElement.style.fill).toEqual("");
                    });
                });
            });
            // good
            describe("desaturateGraph()", function() {

                let nodeElement;

                beforeEach(function() {
                    nodeElement = document.getElementById(node1Line1End);
                    nodeElement.removeAttribute("style");
                });

                describe("if the circle element has an inline style.fill value", function() {

                    describe("if the inline style.fill value includes an alpha value", function() {

                        it("should apply the default CSS circle.style.fill value and preserve the alpha value", function() {
                            const color = "rgba(166, 0, 16, 0.5)";
                            nodeElement.style.fill = color;
                            expect(nodeElement.style.fill).toEqual(color);
                            const colorManager = createColorManager();
                            colorManager.desaturateGraph();
                            expect(nodeElement.style.fill).toEqual("rgba(128, 128, 128, 0.5)");
                        });
                    });

                    describe("if the inline style.fill value does not include an alpha value", function() {

                        it("should apply the default CSS circle.style.fill value", function() {
                            const color = "rgb(166, 0, 16)";
                            nodeElement.style.fill = color;
                            expect(nodeElement.style.fill).toEqual(color);
                            const colorManager = createColorManager();
                            colorManager.desaturateGraph();
                            expect(nodeElement.style.fill).toEqual("rgb(128, 128, 128)");
                        });
                    });
                });

                describe("if the circle element does not have an inline style.fill value", function() {
                        
                    it("should apply the default CSS circle element styling", function() {
                        expect(nodeElement.style.fill).toEqual("");
                        const colorManager = createColorManager();
                        colorManager.desaturateGraph();
                        expect(nodeElement.style.fill).toEqual("rgb(128, 128, 128)");
                    });
                });

                describe("if the circle element is already styled according to the default CSS circle.style.fill attribute", function() {

                    it("should not set the inline style.fill attribute value", function() {
                        nodeElement = document.getElementById(node1);
                        nodeElement.removeAttribute("style");
                        expect(nodeElement.style.fill).toEqual("");
                        const colorManager = createColorManager();
                        colorManager.desaturateGraph();
                        expect(nodeElement.style.fill).toEqual("");
                    });
                });
            });
        });

        describe("find modal functions", function() {

            const tree = {
                111: {
                    name: "Joe",
                    age: 1,
                    longitude: 70,
                    latitude: 700,
                },
                222: {
                    age: 11,
                    longitude: 74,
                    latitude: 700,
                },
                333: {
                    age: 2,
                    count: 333,
                    longitude: 76,
                    latitude: 700,
                }
            };

            for (let key in tree) {
                testTree.tree[key] = tree[key];
            }

            describe("findExactMatchingObjects()", function() {

                describe("if there were no matches", function() {

                    it("should return an empty array", function() {
                        expect(findExactMatchingObjects(testTree.tree, "7qzzz")).toEqual([]);
                    });
                });

                describe("if the search term was an empty string", function() {

                    it("should return an empty array", function() {
                        expect(findExactMatchingObjects(testTree.tree, "")).toEqual([]);
                    });
                });

                describe("if the search term contained only whitespace", function() {

                    it("should return an empty array", function() {
                        expect(findExactMatchingObjects(testTree.tree, "     ")).toEqual([]);
                    });
                });

                describe("if a matching object wasn't drawn in the svg", function() {

                    it("should not return the key of the object", function() {
                        expect(testTree.tree["33420"]).toBeDefined();
                        expect(findExactMatchingObjects(testTree.tree, "33420")).toEqual([]);
                    });
                });

                it("should not return multiple instances of the same key for a matching object", function() {
                    expect(findExactMatchingObjects(tree, "333")).toEqual(["333"])
                });

                describe("if an object's key matches the search term", function() {

                    it("should return the object's key", function() {
                        expect(findExactMatchingObjects(tree, "222")).toEqual(["222"]);
                    });
                });

                describe("if an object's property key matches the search term", function() {

                    it("should return the object's key", function() {
                        expect(findExactMatchingObjects(tree, "age")).toEqual(["111", "222", "333"]);
                    });
                });

                describe("if an object's property value matches the search term", function() {

                    it("should return the object's key", function() {
                        expect(findExactMatchingObjects(tree, "1")).toEqual(["111"]);
                    });
                });
            });

            describe("findSubstringMatchingObjects()", function() {

                describe("if there were no matches", function() {

                    it("should return an empty array", function() {
                        expect(findSubstringMatchingObjects(testTree.tree, "7qzzz")).toEqual([]);
                    });
                });

                describe("if the search term was an empty string", function() {

                    it("should return an empty array", function() {
                        expect(findSubstringMatchingObjects(testTree.tree, "")).toEqual([]);
                    });
                });

                describe("if the search term contained only whitespace", function() {

                    it("should return an empty array", function() {
                        expect(findSubstringMatchingObjects(testTree.tree, "     ")).toEqual([]);
                    });
                });

                describe("if a matching object wasn't drawn in the svg", function() {

                    it("should not return the key of the object", function() {
                        expect(testTree.tree["33420"]).toBeDefined();
                        expect(findSubstringMatchingObjects(testTree.tree, "33420")).toEqual([]);
                    });
                });

                it("should not return multiple instances of the same key for a matching object", function() {
                    expect(findSubstringMatchingObjects(tree, "1", true)).toEqual(["111", "222"]);
                });

                describe("if an object's key contains the search term as a substring", function() {

                    it("should return the object's key", function() {
                        expect(findSubstringMatchingObjects(tree, "3", true)).toEqual(["333"]);
                    });
                });

                describe("if an object's property key contains the search term as a substring", function() {

                    it("should return the object's key", function() {
                        expect(findSubstringMatchingObjects(tree, "o", true)).toEqual(["111", "222", "333"]);
                    });
                });

                describe("if an object's property value contains the search term as a substring", function() {

                    it("should return the object's key", function() {
                        expect(findSubstringMatchingObjects(tree, "Joe", true)).toEqual(["111"]);
                    });
                });
            });
        });

        describe("fillFeederList()", function() {

            it("should not append a <li> element to the <ul> element for this feeder", function() {
                const ul = document.createElement("ul");
                const thisModelName = "this_model";
                const thisFeederName = "this_feeder";
                const feeders = [
                    {
                        model: "some_other_model",
                        name: "some_other_feeder"
                    },
                    {
                        model: thisModelName,
                        name: thisFeederName
                    }
                ];
                fillFeederList(ul, feeders, 'this_owner', thisModelName, thisFeederName);
                expect(ul.children.length).toEqual(1);
                expect(ul.children[0].innerHTML).toEqual('<strong>some_other_feeder</strong> from <br>"some_other_model"');
            });

            describe("If two different models have a feeder with the same name", function() {

                it("should append a <li> element to the <ul> element for each feeder", function() {
                    const ul = document.createElement("ul");
                    const feeders = [
                        {
                            model: "some_other_model",
                            name: "some_other_feeder"
                        },
                        {
                            model: "a_different_model",
                            name: "some_other_feeder"
                        }
                    ];
                    fillFeederList(ul, feeders, 'this_owner', 'this_model', 'this_feeder');
                    expect(ul.children.length).toEqual(2);
                    const sortedChildren = Array.from(ul.children).sort();
                    expect(sortedChildren[0].innerHTML).toEqual('<strong>some_other_feeder</strong> from <br>"some_other_model"');
                    expect(sortedChildren[1].innerHTML).toEqual('<strong>some_other_feeder</strong> from <br>"a_different_model"');
                });
            });

            describe("If a different model has a feeder with the same name as this feeder", function() {

                it("should append a <li> element for that feeder only", function() {
                    const ul = document.createElement("ul");
                    const thisModelName = "this_model";
                    const thisFeederName = "this_feeder";
                    const feeders = [
                        {
                            model: "some_other_model",
                            name: thisFeederName
                        },
                        {
                            model: thisModelName,
                            name: thisFeederName
                        }
                    ];
                    fillFeederList(ul, feeders, 'this_owner', thisModelName, thisFeederName);
                    expect(ul.children.length).toEqual(1);
                    expect(ul.children[0].innerHTML).toEqual('<strong>this_feeder</strong> from <br>"some_other_model"');
                });
            });
        });
    });
    /*
    //I shouldn't be testing these, except in cases where I should
    describe("Private functions and methods", function() {

        xdescribe("Private rowPrototype methods", function() {

            let map;

            beforeEach(function() {
                //table = document.createElement("table");
                map = {
                    "schedule_skew": "349",
                    "fixed value": "permanent"
                };
            });

            xdescribe("validateArguments()", function() {

                it("should throw an error if args.key, args.value, and args.map are all defined", function() {
                    expect(function() {
                        createRow({key: "some key", value: "some value", map: map});
                    }).toThrowError();
                });

                xdescribe("if args.key and args.map are defined", function() {

                    it("should throw an error if args.key doesn't exist in args.map and args.key is not an empty string", function() {
                        expect(function() {
                            createRow({key: " ", map: map});
                        }).toThrowError();
                    });

                    it("should not throw an error if args.key doesn't exist in args.map and args.key is an empty string", function() {
                        expect(function() {
                            createRow({key: "", map: map});
                        }).not.toThrowError();
                    });
                });

                it("should throw an error if args.key is an empty string and args.map is not defined", function() {
                    expect(function() {
                        createRow({key:""});
                    }).toThrowError();
                });
            });

            xdescribe("validateNewKey()", function() {

                it("should return false if the key argument matches an existing key in the map (i.e. no duplicate keys allowed)",
                function() {
                    const newKey = "schedule_skew";
                    const row = createRow({map: map, key: "schedule_skew"});
                    expect(row.validateNewKey(newKey)).toBe(false);
                });

                it("should return false if the key argument is an empty string", function() {
                    const newKey = "";
                    const map = {
                        "schedule_skew": 520,
                    };
                    const row = createRow({map: map, key: "schedule_skew"});
                    expect(row.validateNewKey(newKey)).toBe(false);
                });

                it("should return true if the key argument does NOT already exist in the map", function() {
                    const newKey = "new key";
                    const row = createRow({map: map, key: "schedule_skew"});
                    expect(row.validateNewKey(newKey)).toBe(true);
                });
            });

            xdescribe("validateCurrentKey()", function() {

                it("should return false if the current key is an empty string", function() {
                    const row = createRow({map: map, key: ""});
                    expect(row.validateCurrentKey()).toBe(false);
                });
            });

            xdescribe("updateMapKey()", function() {

                xdescribe("if the value of the input element argument is a valid key for this row", function() {

                    let row;
                    let input;

                    beforeEach(function() {
                        spyOn(rowPrototype, "validateNewKey").and.returnValue(true);
                        row = createRow({map: map, key: "schedule_skew"});
                        input = document.createElement("input");
                        input.value = "new valid key";
                    });

                    it("should remove leading and ending whitespace from the new key", function() {
                        const key = "   key with spaces   ";
                        input.value = key;
                        row.updateMapKey(input);
                        expect(row.key).toEqual("key with spaces");
                    });

                    it("should replace the key of this row with the textContent of the input argument", function() {
                        expect(row.key).toEqual("schedule_skew");
                        row.updateMapKey(input);
                        expect(row.key).toEqual("new valid key");
                    });

                    it("should replace the old key with the new key in the map of this row", function() {
                        expect(row.map["schedule_skew"]).toBeDefined();
                        expect(row.map["new valid key"]).toBeUndefined();
                        row.updateMapKey(input);
                        expect(row.map["schedule_skew"]).toBeUndefined();
                        expect(row.map["new valid key"]).toBeDefined();
                    });
                });

                xdescribe(`if this row previously had a key of "" that didn't exist in the map because it represented an
                attribute that hadn't been added to the map yet`, function() {

                    it(`should set this.map[<new key>] === "", even though technically it should
                    be undefined, since (this.map[""] === undefined && this.map[<new key>] === this.map[""])`, function() {
                        const row = createRow({map: map, key: ""});
                        const input = document.createElement("input");
                        input.value = "new key";
                        row.updateMapKey(input);
                        expect(row.map["new key"]).toEqual("");
                    });
                });

                xdescribe("if the textContent of the input element argument is not a valid key for this row", function() {

                    it("should set the value of the input element argument to be the key of this row", function() {
                        spyOn(window, "alert");
                        spyOn(rowPrototype, "validateNewKey").and.returnValue(false);
                        const row = createRow({map: map, key: "schedule_skew"});
                        const input = document.createElement("input");
                        input.value = "invalid key";
                        row.updateMapKey(input);
                        expect(input.value).toEqual("schedule_skew");
                    });

                    it("should call alert()", function() {
                        spyOn(rowPrototype, "validateNewKey").and.returnValue(false);
                        const spy = spyOn(window, "alert");
                        const row = createRow({map: map, key: "schedule_skew"});
                        const input = document.createElement("input");
                        input.value = "invalid key";
                        row.updateMapKey(input);
                        expect(spy).toHaveBeenCalled();
                    });
                });
            });

            xdescribe("getKeyElement()", function() {

                xdescribe("if the key is not an empty string", function() {

                    it(`should return an HTMLTableCellElement with textContent equal to this row.key`, function() {
                        const row = createRow({map: map, key: "schedule_skew"});
                        const td = row.getKeyElement();
                        expect(td instanceof HTMLTableCellElement).toBe(true);
                        expect(td.textContent).toEqual("schedule_skew");
                    });

                    it("should return an HTMLTableCellElement with 0 children", function() {
                        const row = createRow({map: map, key: "schedule_skew"});
                        const td = row.getKeyElement();
                        expect(td.children.length).toEqual(0);
                    });
                });

                xdescribe("if the key is an empty string", function() {

                    it(`should return an HTMLTableCellElement with 1 child that is an HTMLInputElement
                    which has its 'required' and 'pattern' attributes set `, function() {
                        const row = createRow({map: map, key: ""});
                        const td = row.getKeyElement();
                        const input = td.children[0];
                        expect(td instanceof HTMLTableCellElement).toBe(true);
                        expect(td.children.length).toEqual(1);
                        expect(input instanceof HTMLInputElement).toBe(true);
                        expect(input.required).toBeDefined();
                        expect(input.pattern).toBeDefined();
                    });
                });
            });

            xdescribe("validateNewValue()", function() {

                xdescribe("if the key is either 'longitude' or 'latitude'", function() {

                    it("should return false if the value argument is not a valid number", function() {
                        expect(true).toEqual(false);
                    });
                });
            });

            xdescribe("updateMapValue()", function() {

                it("should remove leading and trailing whitespace from the value", function() {
                    const row = createRow({map: map, key: "schedule_skew"});
                    const input = document.createElement("input");
                    input.value = "   value with whitespace         ";
                    row.updateMapValue(input);
                    expect(row.map["schedule_skew"]).toEqual("value with whitespace");
                });

                xdescribe("if the current key is invalid regardless of the value", function() {

                    let row, input, spy;

                    beforeEach(function() {
                        spyOn(window, "alert");
                        spy = spyOn(rowPrototype, "validateCurrentKey").and.returnValue(false);
                        row = createRow({map: map, key: "schedule_skew"});
                        input = document.createElement("input");
                        input.value = "ok";
                    });

                    it("should not update the map value", function() {
                        row.updateMapValue(input);
                        expect(row.map["key"]).toBeUndefined();
                    });

                    it("should call validateCurrentKey()", function() {
                        row.updateMapValue(input);
                        expect(spy).toHaveBeenCalled();
                    });

                    it("should set the value of the input to be an empty string", function() {
                        row.updateMapValue(input);
                        expect(input.value).toEqual("");
                    });
                });
            });

            xdescribe("getValueElement()", function() {

                const nonModifiableProperties = ["fixed value"];

                xdescribe("if this row has a key and a value but no map", function() {

                    xdescribe("if this row.value is a string", function() {

                        it("should return an HTMLTableCellElement with textContent equal to this row.value", function() {
                            const row = createRow({key: "some key", value: "some value"});
                            const td = row.getValueElement(nonModifiableProperties)
                            expect(td instanceof HTMLTableCellElement).toBe(true);
                            expect(td.textContent).toEqual("some value");
                            expect(td.children.length).toEqual(0);
                        });

                        it("should return an HTMLTableCellElement with 0 children", function() {
                            const row = createRow({key: "some key", value: "some value"});
                            const td = row.getValueElement(nonModifiableProperties)
                            expect(td instanceof HTMLTableCellElement).toBe(true);
                            expect(td.children.length).toEqual(0);
                        });
                    });

                    xdescribe("if this row.value is an HTMLElement", function() {

                        it("should return an HTMLTableCellElement with 1 child that is this row.value", function() {
                            const button = document.createElement("button");
                            const row = createRow({key: "some key", value: button});
                            const td = row.getValueElement(nonModifiableProperties)
                            expect(td instanceof HTMLTableCellElement).toBe(true);
                            expect(td.children.length).toEqual(1);
                            expect(td.children[0]).toBe(button);
                        });
                    });
                });

                xdescribe("if this row has a key and a map but no value", function() {

                    xdescribe("if this row.map[row.key] is not in the nonModifiableProperties array", function() {

                        it(`should return an HTMLTableCellElement with 1 child that is an HTMLInputElement whose
                        value equals this row.map[row.key]`, function() {
                            const row = createRow({key: "schedule_skew", map: map});
                            const td = row.getValueElement(nonModifiableProperties);
                            const input = td.children[0];
                            expect(td instanceof HTMLTableCellElement).toBe(true);
                            expect(td.children.length).toEqual(1);
                            expect(input instanceof HTMLInputElement).toBe(true);
                            expect(input.value).toEqual("349");
                        });
                    });

                    xdescribe("if this row.map[row.key] is in the nonModifiableProperties array", function() {

                        it(`should return an HTMLTableCellElement with textContent equal to this row.map[row.key]`, function() {
                            const row = createRow({key: "fixed value", map: map});
                            const td = row.getValueElement(nonModifiableProperties);
                            expect(td instanceof HTMLTableCellElement).toBe(true);
                            expect(td.textContent).toEqual("permanent");
                        });

                        it("should return an HTMLTableCellElement with 0 children", function() {
                            const row = createRow({key: "fixed value", map: map});
                            const td = row.getValueElement(nonModifiableProperties);
                            expect(td instanceof HTMLTableCellElement).toBe(true);
                            expect(td.children.length).toEqual(0);
                        });
                    });
                });

                xdescribe("if this row has a key, but no value or map", function() {

                    it("should return an HTMLTableCellElement with textContent equal to an empty string", function() {
                        const row = createRow({key: "some key"});
                        const td = row.getValueElement(nonModifiableProperties);
                        expect(td instanceof HTMLTableCellElement).toBe(true);
                        expect(td.textContent).toEqual("");
                    });

                    it("should return an HTMLTableCellElement with no children", function() {
                        const row = createRow({key: "some key"});
                        const td = row.getValueElement(nonModifiableProperties);
                        expect(td instanceof HTMLTableCellElement).toBe(true);
                        expect(td.children.length).toEqual(0);
                    });
                });
            });

            xdescribe("delete()", function() {

                xdescribe("if this row has a map", function() {

                    it("should delete the key of this row from the map", function() {
                        const row = createRow({map: map, key: "schedule_skew"});
                        const table = document.createElement("table");
                        table.append(row.self);
                        expect(row.map[row.key]).toBeDefined();
                        row.delete();
                        expect(row.map[row.key]).toBeUndefined();
                    });

                    it("should remove the self HTMLTableRowElement of the row from its parent", function() {
                        const row = createRow({map: map, key: "schedule_skew"});
                        const table = document.createElement("table");
                        table.append(row.self);
                        expect(table.children.length).toEqual(1);
                        row.delete();
                        expect(table.children.length).toEqual(0);
                    });
                });

                xdescribe("if this row does not have a map", function() {

                    it("should remove the self HTMLTableRowElement of the row from its parent", function() {
                        const row = createRow({key: "key"});
                        const table = document.createElement("table");
                        table.append(row.self);
                        expect(table.children.length).toEqual(1);
                        row.delete();
                        expect(table.children.length).toEqual(0);
                    });
                });
            });
        });

        xdescribe("Private buttonPrototype methods", function() {

            //xdescribe("saveObject", function() {

            //    it("should update the TreeWrapper of this button with the value of the TreeObject of this button", function() {
            //        const tObject = createTreeObject(node3Line1EndChild1Child1, testTreeWrapper);
            //        tObject.data = {foo: "bar"};
            //        const button = createButton({action: "save", tObject: tObject, tWrapper: testTreeWrapper});
            //        expect(button.tWrapper.tree[node3Line1EndChild1Child1]).not.toBe(tObject.data);
            //        button.saveObject();
            //        expect(button.tWrapper.tree[node3Line1EndChild1Child1]).toBe(tObject.data);
            //    });

            //    it("should update the svg", function() {
            //        const spy1 = spyOn(window, "createAddableSvgData").and.callThrough();
            //        const spy2 = spyOn(addableSvgDataPrototype, "redrawTo"); 
            //        const tObject = createTreeObject({}, testTreeWrapper);
            //        const button = createButton({action: "save", tObject: tObject, tWrapper: testTreeWrapper});
            //        button.saveObject();
            //        expect(spy1).toHaveBeenCalled();
            //        expect(spy2).toHaveBeenCalled();
            //    });
            //});

            xdescribe("deleteObject()", function() {

                it("should delete the TreeObject of this button from the TreeWrapper of this button", function() {
                    const tObject = createTreeObject(node3Line1EndChild2Child1, testTreeWrapper);
                    const button = createButton({action: "delete", tObject: tObject, tWrapper: testTreeWrapper, tableBody: {}});
                    expect(testTreeWrapper.tree[node3Line1EndChild2Child1]).toBeDefined();
                    button.deleteObject();
                    expect(testTreeWrapper.tree[node3Line1EndChild2Child1]).toBeUndefined();
                });

                it("should remove the corresponding TreeObject from the svg", function() {
                    const spy1 = spyOn(window, "createDeletableSvgData").and.callThrough();
                    const spy2 = spyOn(deletableSvgDataPrototype, "deleteFrom");
                    const tObject = createTreeObject(node3Line1EndChild2Child1, testTreeWrapper);
                    const button = createButton({action: "delete", tObject: tObject, tWrapper: testTreeWrapper, tableBody: {}});
                    button.deleteObject();
                    expect(spy1).toHaveBeenCalled();
                    expect(spy2).toHaveBeenCalled();
                });
            });
        });
    });
    */
});// Unit tests

/* This is used to display the jasmine reporter.
 */
setTimeout(
    function() {
        const jasmineDiv = document.getElementsByClassName("jasmine_html-reporter")[0];
        jasmineDiv.style.margin = "0px";
        jasmineDiv.style.position = "relative";
        jasmineDiv.style["z-index"] = 1;
        document.body.prepend(jasmineDiv);
        // Replace the real tree with the testing tree
    },
    2000
);
//</script>