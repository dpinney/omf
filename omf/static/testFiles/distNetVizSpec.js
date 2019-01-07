//<script>
// 35 objects
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
    // orphanNode1
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
    // orphanLine1
    "33420": {
        "phases": "ACBN", 
        "from": "node1778317643", 
        "name": "17783", 
        "object": "overhead_line", 
        "longitude": 405.7790593997488, 
        "to": "node1817717783", 
        "length": "338.245", 
        "latitude": 614.664711377176, 
        "configuration": "16564line_configuration32701"
    },
    // funkyLine1
    "121212": {
        "phases": "CS", 
        "from": "house172262", 
        "name": "Decepticon", 
        "object": "transformer", 
        "to": "house172260", 
        "configuration": "1807--T325_C-CONFIG"
    }, 
    // funkyLine2
    "343434": {
        "phases": "CS", 
        "from": "house172260", 
        "name": "AutoBot", 
        "object": "transformer", 
        "to": "house172264", 
        "configuration": "1807--T325_C-CONFIG"
    }, 
};
let testTree = deepCopy(rawTree);
let testTreeWrapper = createTreeWrapper(testTree);

describe("Unit tests", function() {

    /* TODO: If key === 0, longitude === 0, latitude === 0 (or some other property === 0), the code could 
    break in funny ways. I need to check for undefined explicitly instead of using !<property>
    TODO: build a tree that is more representative of the actual data
    */

    /* Some latitudes and longitudes are strings while others are numbers in the .omd files. Is this a problem?
    */

    /* Hardcoding test data like this is bad because if the original data ever changes structure, the methods will fail but
    these unit tests will still pass. However, it is necessary because the alternative would be to use the real testTree from a .omd
    file and then these unit tests would be dependent on a particular .omd file which is even worse.
    */
    // 37 keys for 35 objects
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

    const allKeys = [weirdNode1, weirdNode2, node1, node1Line1, node1Line1End, node1Line1EndChild1, node1Line2,
        node1Line2End, node1Line2EndChild1, node1Line3, node1Line3End, node1Line3EndChild1, node1Line4, node1Line4End,
        node2Line1, node2Line1End , node2Line2, node2Line2End, node2Line2EndChild1, node2Line3, node2Line3End,
        node2Line3EndLine, node2Line3EndLineEnd, node3Line1, node3Line1End, node3Line1EndChild1,
        node3Line1EndChild1Child1, node3Line1EndChild1Child2, node3Line1EndChild2, node3Line1EndChild2Child1,
        node3Line1EndChild3, orphanNode1, orphanLine1, funkyLine1, funkyLine2  
    ];

    beforeEach(function() {
        // Tree does NOT contain any cycles
        testTree = deepCopy(rawTree);
        testTreeWrapper = createTreeWrapper(testTree);
    });

    describe("Public interface methods", function() {

        describe("createTreeWrapper()", function() {

            it("should return a TreeWrapper with a 'tree' property that is identical to the passed tree argument", function() {
                expect(testTreeWrapper.tree).toBe(testTree);
            });

            it(`should return a TreeWrapper with a 'names' property that was created with buildNames()`, function() {
                const spy = spyOn(treeWrapperPrototype, "buildNames").and.callThrough();
                newTreeWrapper = createTreeWrapper(testTree);
                expect(newTreeWrapper.names).toBeDefined();
                expect(spy).toHaveBeenCalled();
            });
        });

        describe("treeWrapperPrototype", function() {
            
            describe("delete()", function() {

                describe("when the key argument does not exist in this TreeWrapper", function() {

                    it("should call console.log() and return an empty TreeWrapper", function() {
                        const spy = spyOn(console, "log");
                        const emptyWrapper = createTreeWrapper();
                        expect(testTreeWrapper.delete("made up key that doesn't exist!!!")).toEqual(emptyWrapper);
                        expect(spy).toHaveBeenCalled();
                    });
                });

                describe("when the tree object with the passed key argument has NO children or connected lines", function() {

                    it(`should delete the tree object with the passed key from this TreeWrapper`, function() {
                        expect(testTreeWrapper.tree[node3Line1EndChild2Child1]).toBeDefined();
                        testTreeWrapper.delete(node3Line1EndChild2Child1);
                        expect(testTreeWrapper.tree[node3Line1EndChild2Child1]).toBeUndefined();
                    });

                    it("should return a TreeWrapper that contains only the tree object with the passed key argument", function() {
                        const tWrapper = createTreeWrapper();
                        tWrapper.add(node3Line1EndChild2Child1, testTreeWrapper);
                        const subWrapper = testTreeWrapper.delete(node3Line1EndChild2Child1);
                        expect(subWrapper).toEqual(tWrapper);
                    });
                });

                describe("when the tree object with the passed key argument HAS children or connected lines", function() {

                    it("should throw an error", function() {
                        expect(function() {
                            testTreeWrapper.delete(node3Line1EndChild2);
                        }).toThrowError();
                    });
                });
            });

            describe("recursiveDelete()", function() {

                it("should call contains() to verify that the key argument exists in the TreeWrapper", function() {
                    const spy = spyOn(treeWrapperPrototype, "contains");
                    testTreeWrapper.recursiveDelete("");
                    expect(spy).toHaveBeenCalled();
                });

                describe("when the key argument does not exist in the TreeWrapper", function() {

                    it("should call console.log() and return an empty TreeWrapper", function() {
                        const spy = spyOn(console, "log");
                        const emptyWrapper = createTreeWrapper();
                        expect(testTreeWrapper.recursiveDelete("made up key that doesn't exist!!!")).toEqual(emptyWrapper);
                        expect(spy).toHaveBeenCalled();
                    });
                });

                describe("when the tree object with the passed key argument is a node", function() {

                    it(`should delete from this TreeWrapper: 1) the tree object with the passed key 2) its direct children 
                    3) all children of children recursively 4) lines connected to the tree object with the passed key 
                    5) lines that are connected to children of children.`, function() {
                        const keys = [node3Line1EndChild1, node3Line1EndChild2, node3Line1EndChild3, node3Line1,
                            node3Line1EndChild1Child1, node3Line1EndChild1Child2, node3Line1EndChild2Child1, node3Line1End,
                            funkyLine1, funkyLine2]
                        const names = [];
                        for (let key of keys) {
                            expect(testTreeWrapper.tree[key]).toBeDefined();
                            expect(testTreeWrapper.names[testTreeWrapper.tree[key].name]).toBeDefined();
                            names.push(testTreeWrapper.tree[key].name);
                        }
                        testTreeWrapper.recursiveDelete(node3Line1End);
                        for (let key of keys) {
                            expect(testTreeWrapper.tree[key]).toBeUndefined();
                            expect(testTreeWrapper.names[names.pop()]).toBeUndefined();
                        }
                    });

                    it(`should return a TreeWrapper that contains the objects that were deleted.`, function() {
                        const keys = [node3Line1EndChild1, node3Line1EndChild2, node3Line1EndChild3, node3Line1,
                            node3Line1EndChild1Child1, node3Line1EndChild1Child2, node3Line1EndChild2Child1, node3Line1End,
                            funkyLine1, funkyLine2];
                        for (let key of keys) {
                            expect(testTreeWrapper.tree[key]).toBeDefined();
                            expect(testTreeWrapper.names[testTreeWrapper.tree[key].name]).toBeDefined();
                        }
                        const tWrapper = createTreeWrapper();
                        for (let key of keys) {
                            tWrapper.add(key, testTreeWrapper);
                        } 
                        const subWrapper = testTreeWrapper.recursiveDelete(node3Line1End);
                        expect(subWrapper).toEqual(tWrapper);
                    });
                });

                describe("when the tree argument with the passed key argument is a line", function() {

                    it("should delete only the line from this TreeWrapper", function() {
                        expect(testTreeWrapper.tree[node1Line1]).toBeDefined();
                        testTreeWrapper.recursiveDelete(node1Line1);
                        expect(testTreeWrapper.tree[node1Line1]).toBeUndefined();
                    });

                    it(`should return a TreeWrapper that only contains the line`, function() {
                        expect(testTreeWrapper.tree[node1Line1]).toBeDefined();
                        const tWrapper = createTreeWrapper();
                        tWrapper.add(node1Line1, testTreeWrapper);
                        const subWrapper = testTreeWrapper.recursiveDelete(node1Line1);
                        expect(subWrapper).toEqual(tWrapper);
                    });
                });
            });

            describe("insert()", function() {

                describe("when the TreeObject does not exist in the TreeWrapper", function() {

                    it(`should add the data of the TreeObject argument to this TreeWrapper`, function() {
                        const map = {
                            "parent": "house172645", 
                            "name": "waterheater444555666", 
                            "object": "waterheater", 
                            "longitude": 233.258917459014, 
                            "latitude": 800.489571934734, 
                        }
                        const tObj = createTreeObject(map, testTreeWrapper);
                        expect(Object.keys(testTreeWrapper.tree).length).toEqual(35);
                        expect(Object.keys(testTreeWrapper.names).length).toEqual(33);
                        testTreeWrapper.insert(tObj);      
                        expect(Object.keys(testTreeWrapper.tree).length).toEqual(36);
                        expect(Object.keys(testTreeWrapper.names).length).toEqual(34);
                    });
                });

                describe(`when a tree object with an identical key to the TreeObject already exists
                in this TreeWrapper`, function() {

                    it(`should overwrite the tree object data with data from the TreeObject`, function() {
                        const tObj = createTreeObject(node1, testTreeWrapper);
                        tObj.data.object = "blahblahblah";
                        tObj.data.longitude = "-1000";
                        tObj.data.latitude = "-1111";
                        expect(Object.keys(testTreeWrapper.tree).length).toEqual(35);
                        expect(Object.keys(testTreeWrapper.names).length).toEqual(33);
                        testTreeWrapper.insert(tObj);
                        expect(testTreeWrapper.tree[node1]).toBe(tObj.data);
                        expect(testTreeWrapper.names[testTreeWrapper.tree[node1].name]).toEqual(tObj.key);
                        expect(Object.keys(testTreeWrapper.tree).length).toEqual(35);
                        expect(Object.keys(testTreeWrapper.names).length).toEqual(33);
                    });
                });

                describe("when the TreeObject represents a node", function() {

                    it(`should return a TreeWrapper that contains 1) the tree object represented by the TreeObject argument
                    2) the parent of the tree object (if one exists) 3) the direct children of the tree object (if they exist)
                    4) lines that are connected to the tree object (if there are any) 5) nodes on the other ends of lines that
                    are connected to the tree object (if there are connected lines)`, function() {
                        const keys = [node3Line1End, node3Line1EndChild1, node3Line1EndChild2, node3Line1EndChild3, node3Line1, node3];
                        const tObj = createTreeObject(node3Line1End, testTreeWrapper);
                        const subWrapper = testTreeWrapper.insert(tObj);
                        for (let key of keys) {
                            expect(subWrapper.tree[key]).toBe(testTreeWrapper.tree[key]);
                            expect(subWrapper.names[subWrapper.tree[key].name]).toEqual(testTreeWrapper.names[testTreeWrapper.tree[key].name]);
                        }
                        expect(Object.keys(subWrapper.tree).length).toEqual(keys.length);
                        expect(Object.keys(subWrapper.names).length).toEqual(keys.length);
                    });
                });

                describe("when the TreeObject represents a line", function() {

                    it(`should return a TreeWrapper that contains the line and the nodes on either end of
                    the line`, function() {
                        const keys = [node3Line1, node3Line1End, node3]
                        const tObj = createTreeObject(node3Line1, testTreeWrapper);
                        const subWrapper = testTreeWrapper.insert(tObj);
                        for (let key of keys) {
                            expect(subWrapper.tree[key]).toBe(testTreeWrapper.tree[key]);
                            expect(subWrapper.names[subWrapper.tree[key].name]).toEqual(testTreeWrapper.names[testTreeWrapper.tree[key].name]);
                        }
                        expect(Object.keys(subWrapper.tree).length).toEqual(keys.length);
                        expect(Object.keys(subWrapper.names).length).toEqual(keys.length);
                    });
                });
            });
        });

        describe("createTreeObject()", function() {

            describe("when invoked with (key, treeWrapper) arguments", function() {

                it("should return a TreeObject with the passed key", function() {
                    const tree = {
                        1010: {
                            prop: "custom value"
                        },
                        2020: {
                            prop: "different value"
                        }
                    };
                    const treeWrapper = createTreeWrapper(tree);
                    const tObj = createTreeObject("1010", treeWrapper);
                    expect(tObj.key).toEqual("1010");
                });

                it("should return a TreeObject with data that is equivalent to the tree object, but not the same object", function() {
                    const tree = {
                        1010: {
                            prop: "custom value"
                        },
                        2020: {
                            prop: "different value"
                        }
                    };
                    const treeWrapper = createTreeWrapper(tree);
                    const tObj = createTreeObject("1010", treeWrapper);
                    expect(tObj.data).not.toBe(treeWrapper.tree[tObj.key]);
                    expect(tObj.data).toEqual(treeWrapper.tree["1010"]);
                });

                it("should throw an error if the key argument doesn't exist in the treeWrapper argument", function() {
                    expect(function() {
                        createTreeObject("10", createTreeWrapper());
                    }).toThrowError(`The passed key argument: "10" to create the TreeObject does not exist in the treeWrapper.tree.`);
                });

                it("should throw an error if the key argument is not a string", function() {
                    expect(function() {
                        createTreeObject(10, createTreeWrapper());
                    }).toThrowError("Input argument must be a string or an object."); 
                });
            });

            describe("when invoked with (map, treeWrapper) arguments", function() {

                it("should return a TreeObject with data that is equivalent to the map, but not the same object", function() {
                    const map = {
                        prop: "cool value"
                    }
                    const tObj = createTreeObject(map, createTreeWrapper());
                    expect(tObj.data).not.toBe(map);
                    expect(tObj.data).toEqual(map);
                });

                it("should return a TreeObject with a key that does not exist in the treeWrapper.tree", function() {
                    const tree = {
                        0: {}
                    };
                    const treeWrapper = createTreeWrapper(tree);
                    const tObj = createTreeObject({}, treeWrapper);
                    expect(tObj.key).toEqual("1");
                });

                //it("should call update()", function() {
                //    const spy = spyOn(treeObjectPrototype, "update").and.callThrough();
                //    createTreeObject({}, createTreeWrapper());
                //    expect(spy).toHaveBeenCalled();
                //});

                //it("should throw any error thrown by update()", function() {
                //    const error = "Custom Error"
                //    const spy = spyOn(treeObjectPrototype, "update").and.throwError(error);
                //    expect(function() {
                //        createTreeObject({}, createTreeWrapper());
                //    }).toThrowError(error)
                //});

                //it("should call getNewTreeKey()", function() {
                //    const spy = spyOn(window, "getNewTreeKey").and.callThrough();
                //    createTreeObject({}, createTreeWrapper());
                //    expect(spy).toHaveBeenCalled();
                //});
            });
        });

        describe("createRow()", function() {

            it("should throw an error if the key argument does not exist in the map argument and the key is not an empty string",
            function() {
                const table = document.createElement("table");
                const map = {
                    "schedule_skew": 129
                };
                expect(function() {
                    createRow({map: map, key: "doesn't exist"});
                }).toThrowError();
            });

            it("should throw an error if a non-null/undefined key argument is passed with a null/undefined map argument",
            function() {
                expect(function() {
                    createRow({map: null, key: ""});
                }).toThrowError();
            });

            it("should not throw an error if the key argument exists in the map argument", function() {
                const table = document.createElement("table");
                const map = {
                    "schedule_skew": 129
                };
                expect(function() {
                    createRow({map: map, key: "schedule_skew"});
                }).not.toThrowError();
            });

            it("should not throw an error if the key argument equals an empty string", function() {
                const table = document.createElement("table");
                const map = {
                    "schedule_skew": 399
                };
                expect(function() {
                    createRow({map: map, key: ""});
                }).not.toThrowError();
            });
        });

        xdescribe("treeObjectPrototype()", function() {
            //no public methods?
        });

        describe("createAddableSvgData()", function() {

            it("should return an object with an array of lines and an array of circles", function() {
                const treeWrapper = createTreeWrapper();
                const svgData = createAddableSvgData(treeWrapper);
                expect(svgData.circles).toEqual(jasmine.any(Array));
                expect(svgData.lines).toEqual(jasmine.any(Array));
            });

            describe("when the treeWrapper.tree argument is non-empty", function() {

                it("should return an object with the correct number of circles and lines", function() {
                    const svgData = createAddableSvgData(testTreeWrapper);
                    expect(svgData.circles.length).toEqual(23);
                    expect(svgData.lines.length).toEqual(21);
                });
            });
        });

        describe("createDeletableSvgData", function() {

        });

        describe("deletableSvgDataPrototype", function() {

            describe("deleteFrom()", function() {

                describe("When an element id does not exist in the document viewport", function() {
                    
                    it("should not throw an error", function() {
                        const tree = {
                            "crazy made up key": {}
                        };
                        const svg = createDeletableSvgData(tree);
                        expect(svg.ids[0]).toEqual("crazy made up key");
                        expect(function() {
                            svg.deleteFrom(gViewport)
                        }).not.toThrowError();
                    });
                });
            });
        });
    });

    describe("Private helper methods", function() {

        describe("treeWrapperPrototype", function() {

            describe("buildNames()", function() {

                it("should return an object that maps the name of every tree object to its key", function() {
                    const names = {};
                    for (let key in testTree) {
                        let name = testTree[key].name;
                        if (name !== undefined && name !== null) {
                            names[name] = key;
                        }
                    }
                    expect(testTreeWrapper.buildNames()).toEqual(names);
                });

                it("should exclude a tree object if it does not have a name property", function() {
                    // 35 objects exist, but only 33 have names because 2 weird nodes are missing 'name'
                    expect(Object.keys(testTreeWrapper.buildNames()).length).toEqual(33);  
                    expect(testTreeWrapper.names[undefined]).not.toBeDefined();
                });
            });

            describe("contains()", function() {

                it("should return true if this TreeWrapper contains a tree object with the 'key' argument.", function() {
                    expect(testTreeWrapper.tree[node1]).toBeDefined();
                    expect(testTreeWrapper.contains(node1)).toEqual(true);
                });

                it("should return false if this TreeWrapper does not contain a tree object with the 'key' argument", function() {
                    expect(testTreeWrapper.tree["foo"]).toBeUndefined();
                    expect(testTreeWrapper.contains("foo")).toEqual(false);
                });
            });

            describe("add()", function() {

                describe("when the 'key' argument does not exist in 'treeWrapper' argument", function() {

                    it("should call console.log(), not modify this TreeWrapper, and return", function() {
                        expect(testTreeWrapper.tree["foo"]).toBeUndefined();
                        const spy = spyOn(console, "log");
                        const emptyWrapper = createTreeWrapper();
                        const tWrapper = createTreeWrapper();
                        tWrapper.add("foo", testTreeWrapper);
                        expect(tWrapper).toEqual(emptyWrapper);
                        expect(spy).toHaveBeenCalled();
                    });
                });

                describe(`when the tree object with the 'key' argument exists in the 'treeWrapper' argument,
                but does not have a 'name' property`, function() {

                    it(`should 1) add the tree object to the 'tree' property of this TreeWrapper, 2) not
                    modify the 'names' property of this TreeWrapper.`, function() {
                        expect(testTreeWrapper.tree[weirdNode1]).toBeDefined();
                        expect(testTreeWrapper.tree[weirdNode1].name).toBeUndefined();
                        const tWrapper = createTreeWrapper();
                        tWrapper.add(weirdNode1, testTreeWrapper);
                        expect(Object.keys(tWrapper.tree).length).toEqual(1);
                        expect(Object.keys(tWrapper.names).length).toEqual(0);
                    });
                });

                describe("when the tree object with the key exists, and has a 'name' property", function() {

                    it(`should add the tree object argument to the 'tree' and 'names' properties of 
                    this treeWrapper`, function() {
                        expect(testTreeWrapper.tree[node1]).toBeDefined();
                        expect(testTreeWrapper.tree[node1].name).toBeDefined();
                        const tWrapper = createTreeWrapper();
                        tWrapper.add(node1, testTreeWrapper);
                        expect(Object.keys(tWrapper.tree).length).toEqual(1);
                        expect(Object.keys(tWrapper.names).length).toEqual(1);
                    });
                });
            });

            describe("getChildrenOf()", function() {

                it("should call contains() to validate the 'key' argument", function() {
                    const spy = spyOn(treeWrapperPrototype, "contains");
                    testTreeWrapper.getChildrenOf("0");
                    expect(spy).toHaveBeenCalled();
                });

                it(`should return a TreeWrapper that excludes tree objects that lack a 'parent' 
                property.` , function() {
                    const t = {
                        "0": {
                            "climate": "humid"
                        }
                    };
                    const emptyWrapper = createTreeWrapper();
                    const children = createTreeWrapper(t).getChildrenOf("0");
                    expect(children).toEqual(emptyWrapper);
                });

                describe("when the tree object with the passed 'key' argument has children", function() {

                    it(`should return a TreeWrapper that only contains its child tree objects`, function() {
                        // Get 2 children
                        const tWrapper = createTreeWrapper();
                        tWrapper.add(node3Line1EndChild1Child2, testTreeWrapper);
                        tWrapper.add(node3Line1EndChild1Child1, testTreeWrapper);
                        const children = testTreeWrapper.getChildrenOf(node3Line1EndChild1);
                        expect(children).toEqual(tWrapper);
                    });

                    it(`should return a TreeWrapper that only contains its child tree objects`, function() {
                        // Get 1 child
                        const tWrapper = createTreeWrapper();
                        tWrapper.add(node2Line2EndChild1, testTreeWrapper);
                        const children = testTreeWrapper.getChildrenOf(node2Line2End)
                        expect(children).toEqual(tWrapper);
                    });
                });

                describe("when the tree object with the passed key argument does not have children", function() {

                    it("should return an empty TreeWrapper", function() {
                        const emptyWrapper = createTreeWrapper();
                        const children = testTreeWrapper.getChildrenOf(node2Line3End);                        
                        expect(children).toEqual(emptyWrapper);
                    });

                    it("should return an empty TreeWrapper", function() {
                        // test for weird nodes
                        const emptyWrapper = createTreeWrapper();
                        const children = testTreeWrapper.getChildrenOf(weirdNode2);
                        expect(children).toEqual(emptyWrapper);
                    });
                });
            });
            
            describe("getConnectedLinesOf()", function() {

                it("should call contains to validate the 'key' argument", function() {
                    const spy = spyOn(treeWrapperPrototype, "contains");
                    testTreeWrapper.getConnectedLinesOf("0");
                    expect(spy).toHaveBeenCalled();
                });

                describe("when the tree object with the passed 'key' argument has connected lines", function() {

                    it(`should return a new TreeWrapper that only contains tree objects that are lines
                    which connect to the tree object argument`, function() {
                        const tWrapper = createTreeWrapper();
                        tWrapper.add(node2Line1, testTreeWrapper);
                        tWrapper.add(node2Line2, testTreeWrapper);
                        tWrapper.add(node2Line3, testTreeWrapper);
                        tWrapper.add(node1Line4, testTreeWrapper);
                        const subWrapper = testTreeWrapper.getConnectedLinesOf(node2);
                        expect(subWrapper).toEqual(tWrapper);
                    });
                });

                describe("when the tree object with the passed 'key' argument does not have connected lines", function() {

                    it("should return an empty TreeWrapper", function() {
                        // Test for nodes without lines
                        const emptyWrapper = createTreeWrapper();
                        const subWrapper = testTreeWrapper.getConnectedLinesOf(node2Line2EndChild1);
                        expect(subWrapper).toEqual(emptyWrapper);
                    });

                    it("should return an empty TreeWrapper", function() {
                        // Test for lines (since lines don't connect to other lines)
                        const emptyWrapper = createTreeWrapper();
                        const subWrapper = testTreeWrapper.getConnectedLinesOf(node1Line4);
                        expect(subWrapper).toEqual(emptyWrapper);
                    });

                    it("should return an empty TreeWrapper", function() {
                        // Test for weird nodes
                        const emptyWrapper = createTreeWrapper();
                        const subWrapper = testTreeWrapper.getConnectedLinesOf(weirdNode1);
                        expect(subWrapper).toEqual(emptyWrapper);
                    });
                });
            });

            describe("merge()", function() {

                describe("when no keys array is passed", function() {

                    it(`should merge the entire TreeWrapper argument into this TreeWrapper`, function() {
                        /* Both TreeWrapper.trees should contain the same objects. Both TreeWrapper.names 
                        should contain the same names
                        */
                        const subWrapper = createTreeWrapper();
                        subWrapper.merge(testTreeWrapper);
                        for (let key of allKeys) {
                            expect(subWrapper.tree[key]).toBe(testTreeWrapper.tree[key]);
                            expect(subWrapper.names[subWrapper.tree[key].name]).toEqual(testTreeWrapper.names[testTreeWrapper.tree[key].name]);
                        }
                        expect(Object.keys(subWrapper.tree).length).toEqual(Object.keys(testTreeWrapper.tree).length);
                        expect(Object.keys(subWrapper.names).length).toEqual(Object.keys(testTreeWrapper.names).length);
                    });
                });

                describe(`when a keys array argument is passed`, function() {
                    
                    it(`should merge only tree objects with the specified keys from the TreeWrapper agument into this
                    TreeWrapper`, function() {
                        const keys = [node2Line3EndLine, node2Line3End];
                        const subWrapper = createTreeWrapper();
                        subWrapper.merge(testTreeWrapper, keys);
                        for (let key of keys) {
                            expect(subWrapper.tree[key]).toBe(testTreeWrapper.tree[key]);
                            expect(subWrapper.names[subWrapper.tree[key].name]).toEqual(testTreeWrapper.names[testTreeWrapper.tree[key].name]);
                        }
                        expect(Object.keys(subWrapper.tree).length).toEqual(keys.length);
                        expect(Object.keys(subWrapper.names).length).toEqual(keys.length);
                    });
                });
            });

            describe(`getSubtreeToDelete()`, function() {

                describe("when the tree object with the passed key argument is a node", function() {

                    it(`should return a TreeWrapper that contains children of children (etc.) and all lines that connect to 
                    any of those children`, function() { 
                        const tWrapper = createTreeWrapper();
                        tWrapper.add(node3Line1EndChild1, testTreeWrapper);
                        tWrapper.add(node3Line1EndChild2, testTreeWrapper);
                        tWrapper.add(node3Line1EndChild3, testTreeWrapper);
                        tWrapper.add(node3Line1, testTreeWrapper);
                        tWrapper.add(funkyLine1, testTreeWrapper);
                        tWrapper.add(funkyLine2, testTreeWrapper);
                        tWrapper.add(node3Line1EndChild1Child1, testTreeWrapper);
                        tWrapper.add(node3Line1EndChild1Child2, testTreeWrapper);
                        tWrapper.add(node3Line1EndChild2Child1, testTreeWrapper);
                        const subWrapper = testTreeWrapper.getSubtreeToDelete(node3Line1End, []);
                        expect(subWrapper).toEqual(tWrapper);
                    });

                    it(`should not recurse infinitely if a cycle exists in the graph`, function() {
                        tree = {
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
                        const smallWrapper = createTreeWrapper(tree);
                        const tWrapper = createTreeWrapper();
                        tWrapper.add("1", smallWrapper);
                        tWrapper.add("2", smallWrapper);
                        const subWrapper = tWrapper.getSubtreeToDelete("1", []);
                        expect(subWrapper).toEqual(tWrapper);
                    });
                });
                
                describe("when the tree object with the passed key argument is a line", function() {

                    it(`should return an empty TreeWrapper`, function() {
                        const emptyWrapper = createTreeWrapper();
                        const subWrapper = testTreeWrapper.getSubtreeToDelete(funkyLine1, []);
                        expect(subWrapper).toEqual(emptyWrapper);
                    });
                });
            });
            
            describe("getParentOf()", function() {

                it("should call contains() to validate the 'key' argument", function() {
                    const spy = spyOn(treeWrapperPrototype, "contains");
                    testTreeWrapper.getParentOf("0");
                    expect(spy).toHaveBeenCalled();
                });

                describe(`when the tree object with the 'key' argument has a parent that exists in 
                the TreeWrapper`, function() {

                    it(`should return a new TreeWrapper that contains only the parent of the tree object.`, function() {
                        const tWrapper = createTreeWrapper();
                        tWrapper.add(node2Line2End, testTreeWrapper);
                        const subWrapper = testTreeWrapper.getParentOf(node2Line2EndChild1);
                        expect(subWrapper).toEqual(tWrapper);
                    });
                });

                describe(`when the tree object with the 'key' argument has a parent, but that parent does not exist
                in the TreeWrapper`, function() {

                    xit("should call console.log()", function() {
                        /* When the graph is first built, the log messages are helpful for finding bad data. Once I'm moving
                        stuff around in the interface, the same error messages appear even when the code is behaving as intended.
                        That's why this is disabled.
                        */
                        const spy = spyOn(console, "log");
                        const subWrapper = testTreeWrapper.getParentOf(orphanNode1);
                        expect(spy).toHaveBeenCalled();
                    });

                    it("should return a new empty TreeWrapper.", function() {
                        const emptyWrapper = createTreeWrapper();
                        const subWrapper = testTreeWrapper.getParentOf(orphanNode1);
                        expect(subWrapper).toEqual(emptyWrapper);
                    });
                });

                describe("when the tree object with the passed key doesn't have a 'parent' property at all", function() {

                    it(`should return an empty TreeWrapper.`, function() {
                        // Test for parentless nodes
                        const emptyWrapper = createTreeWrapper();
                        const subWrapper = testTreeWrapper.getParentOf(node1Line2End);
                        expect(subWrapper).toEqual(emptyWrapper);
                    });

                    it(`should return an empty TreeWrapper`, function() {
                        // Test for lines
                        const emptyWrapper = createTreeWrapper();
                        const subWrapper = testTreeWrapper.getParentOf(node1Line4);
                        expect(subWrapper).toEqual(emptyWrapper);
                    });

                    it("should return an empty TreeWrapper", function() {
                        // Test for weird objects
                        const emptyWrapper = createTreeWrapper();
                        const subWrapper = testTreeWrapper.getParentOf(weirdNode2);
                        expect(subWrapper).toEqual(emptyWrapper);
                    })
                });
            });

            //Problem?!
            describe("getPairedNodesOf()", function() {

                it("should call contains() to validate the 'key' argument", function() {
                    const spy = spyOn(treeWrapperPrototype, "contains");
                    testTreeWrapper.getPairedNodesOf("0");
                    expect(spy).toHaveBeenCalled();
                });

                describe("when the tree object with the passed key has paired nodes", function() {

                    it(`should return a TreeWrapper that contains only those nodes which are on the other ends of lines
                    that are connected to the tree object.`, function() {
                        const tWrapper = createTreeWrapper();
                        tWrapper.add(node2Line1End, testTreeWrapper);
                        tWrapper.add(node2Line2End, testTreeWrapper);
                        tWrapper.add(node2Line3End, testTreeWrapper);
                        tWrapper.add(node1, testTreeWrapper);
                        const paired = testTreeWrapper.getPairedNodesOf(node2);
                        expect(paired).toEqual(tWrapper);
                    });
                });

                describe("when the tree object with the passed key has no paired nodes", function() {

                    it(`should return an empty TreeWrapper`, function() {
                        // Test for node that has no connected lines
                        const emptyWrapper = createTreeWrapper();
                        const subWrapper = testTreeWrapper.getPairedNodesOf(node1Line1EndChild1);
                        expect(subWrapper).toEqual(emptyWrapper);
                    });

                    it(`should return an empty TreeWrapper`, function() {
                        // Test for line (since lines don't have paired nodes)
                        const emptyWrapper = createTreeWrapper();
                        const subWrapper = testTreeWrapper.getPairedNodesOf(node3Line1);
                        expect(subWrapper).toEqual(emptyWrapper);
                    });

                    it(`should return an empty TreeWrapper`, function() {
                        // Test for weird node
                        const emptyWrapper = createTreeWrapper();
                        const subWrapper = testTreeWrapper.getPairedNodesOf(weirdNode2);
                        expect(subWrapper).toEqual(emptyWrapper);
                    });
                });
            });

            describe("getNodeEndsOf()", function() {

                it("should call contains() to validate the 'key' argument", function() {
                    const spy = spyOn(treeWrapperPrototype, "contains");
                    testTreeWrapper.getNodeEndsOf("0");
                    expect(spy).toHaveBeenCalled();
                });

                describe("when the tree object with the passed key argument is a line", function() {

                    it(`should return a TreeWrapper that contains only those nodes which are on either side of the line
                    that is represented by the tree object.`, function() {
                        const tWrapper = createTreeWrapper();
                        tWrapper.add(node2, testTreeWrapper);
                        tWrapper.add(node2Line3End, testTreeWrapper);
                        const subWrapper = testTreeWrapper.getNodeEndsOf(node2Line3);
                        expect(subWrapper).toEqual(tWrapper);
                    });
                });

                describe("when the tree object with the passed key argument is NOT a line", function() {

                    it(`should return an empty TreeWrapper`, function() {
                        const emptyWrapper = createTreeWrapper();
                        const subWrapper = testTreeWrapper.getNodeEndsOf(node2);
                        expect(subWrapper).toEqual(emptyWrapper);
                    });

                    it("should return an empty TreeWrapper", function() {
                        // Test for weird nodes
                        const emptyWrapper = createTreeWrapper();
                        const subWrapper = testTreeWrapper.getNodeEndsOf(weirdNode2);
                        expect(subWrapper).toEqual(emptyWrapper);
                    });
                });
            });

            describe("getSubtreeToRedraw()", function() {

                /* Should NOT call contains(), because the other private helper methods can be used
                in different methods besides just this one, so they should contain their own validation and
                not rely entirely on this method to validate the key.
                */

                describe("when tree object with the passed key argument is a node", function() {

                    it(`should return a TreeWrapper containing: 1) lines that connect to the tree object with the passed key argument
                    2) direct children of the tree object with the passed key argument, 3) the parent of the tree object with the 
                    passed key argument 4) nodes on the other ends of lines that connect to the tree object with the passed key 
                    argument`, function() {
                        const tWrapper = createTreeWrapper();
                        tWrapper.add(node3Line1End, testTreeWrapper);
                        tWrapper.add(node3Line1EndChild2Child1, testTreeWrapper);
                        tWrapper.add(node3Line1EndChild1, testTreeWrapper);
                        tWrapper.add(node3Line1EndChild3, testTreeWrapper);
                        tWrapper.add(funkyLine1, testTreeWrapper);
                        tWrapper.add(funkyLine2, testTreeWrapper);
                        const subWrapper = testTreeWrapper.getSubtreeToRedraw(node3Line1EndChild2);
                        expect(subWrapper).toEqual(tWrapper);
                    });
                });

                describe("when the tree object with the passed key argument is a line", function() {

                    it(`should return a TreeWrapper containing 2 nodes on either end of the line`, function() {
                        const tWrapper = createTreeWrapper();
                        tWrapper.add(node2Line3End, testTreeWrapper);
                        tWrapper.add(node2Line3EndLineEnd, testTreeWrapper);
                        const subWrapper = testTreeWrapper.getSubtreeToRedraw(node2Line3EndLine);
                        expect(subWrapper).toEqual(tWrapper);
                    });
                });
            });
        });

        xdescribe("treeObjectPrototype", function() {
            // no private methods?
        });

        describe("rowPrototype", function() {

            let map;

            beforeEach(function() {
                table = document.createElement("table");
                map = {
                    "schedule_skew": "349" 
                };
            });

            describe("validateNewKey()", function() {

                it("should return false if the key argument matches an existing key in the map (i.e. no duplicate keys allowed)",
                function() {
                    const newKey = "schedule_skew";
                    const row = createRow({map: map, key: "schedule_skew"});
                    expect(row.validateNewKey(newKey)).toBe(false);
                });

                it("should return true if the key argument is an empty string", function() {
                    const newKey = "";
                    const map = {
                        "schedule_skew": 520,
                    };
                    const row = createRow({map: map, key: "schedule_skew"});
                    expect(row.validateNewKey(newKey)).toBe(true);
                });

                it("should return true if the key argument does NOT already exist in the map", function() {
                    const newKey = "new key";
                    const row = createRow({map: map, key: "schedule_skew"});
                    expect(row.validateNewKey(newKey)).toBe(true);
                });
            });

            describe("updateMapKey()", function() {

                describe("when the value of the input element argument is a valid key for this row", function() {

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

                describe(`when this row previously had a key of "" that didn't exist in the map because it represented an
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

                describe("when the textContent of the input element argument is not a valid key for this row", function() {

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

            describe("getKeyElement()", function() {

                it(`should return a <td> HTMLElement with 0 children and textContent equal to the key of this row,
                if the row.key is not null and not an empty string`, function() {
                    const row = createRow({map: map, key: "schedule_skew"});
                    const td = row.getKeyElement();
                    expect(td instanceof HTMLTableCellElement).toBe(true);
                    expect(td.textContent).toEqual("schedule_skew");
                    expect(td.children.length).toEqual(0);
                });

                it(`should return a <td> HTMLElement with 1 <input> child element, if the row.key equals an empty string`, function() {
                    const row = createRow({map: map, key: ""});
                    const td = row.getKeyElement();
                    expect(td instanceof HTMLTableCellElement).toBe(true);
                    expect(td.children[0] instanceof HTMLInputElement).toBe(true);
                    expect(td.children.length).toEqual(1);
                });

                it(`should return a <td> HTMLElement with 0 children and with textContent equal to an empty string,
                when the row.key and row.map are null`, function() {
                    const row = createRow();
                    const td = row.getKeyElement();
                    expect(td instanceof HTMLTableCellElement).toBe(true);
                    expect(td.textContent).toEqual("");
                    expect(td.children.length).toEqual(0);
                });
            });

            describe("validateNewValue()", function() {

                describe("when the key is either 'longitude' or 'latitude'", function() {

                    it("should return false if the value argument is not a valid number", function() {
                        expect(true).toEqual(false);
                    });
                });
            });

            describe("updateMapValue", function() {

                it("should remove leading and trailing whitespace from the value", function() {
                    const row = createRow({map: map, key: "schedule_skew"});
                    const input = document.createElement("input");
                    input.value = "   value with whitespace         ";
                    row.updateMapValue(input);
                    expect(row.map["schedule_skew"]).toEqual("value with whitespace");
                });
            });

            describe("getValueElement()", function() {

                it(`should return a <td> HTMLElement with 0 children and textContent equal to an empty string,
                if the value argument is null/undefined`, function() {
                    const row = createRow();
                    const td = row.getValueElement()
                    expect(td instanceof HTMLTableCellElement).toBe(true);
                    expect(td.children.length).toEqual(0);
                    expect(td.textContent).toEqual("");
                });

                it(`should return a <td> HTMLElement with 0 children and textContent equal to the value argument,
                if the value argument is not null/undefined and the corresponding key is contained within the
                nonModifiableProperties array`, function() {
                    const nonModifiableProperties = ["schedule_skew"];
                    const row = createRow({key: "schedule_skew", map: map});
                    const td = row.getValueElement(row.map[row.key], nonModifiableProperties);
                    expect(td instanceof HTMLTableCellElement).toBe(true);
                    expect(td.children.length).toEqual(0);
                    expect(td.textContent).toEqual("349");
                });

                it(`should return a <td> HTMLElement with 1 <input> child element whose value equals the value argument,
                if the value argument is not null/undefined and is not contained with the nonModifiableProperties array`,
                function() {
                    const nonModifiableProperties = ["schedule_skew"];
                    const row = createRow();
                    const td = row.getValueElement("", nonModifiableProperties);
                    expect(td instanceof HTMLTableCellElement).toBe(true);
                    expect(td.children.length).toEqual(1);
                    expect(td.children[0].value).toEqual(""); 
                });
            });

            describe("delete()", function() {

                it("should delete the key of this row from the the map", function() {
                    const row = createRow({map: map, key: "schedule_skew"});
                    const table = document.createElement("table");
                    table.append(row.self);
                    expect(row.map[row.key]).toBeDefined();
                    row.delete();
                    expect(row.map[row.key]).toBeUndefined();

                });

                it("should remove the self <tr> HTMLElement of the row from its parent", function() {
                    const row = createRow({map: map, key: "schedule_skew"});
                    const table = document.createElement("table");
                    table.append(row.self);
                    expect(table.children.length).toEqual(1);
                    row.delete();
                    expect(table.children.length).toEqual(0);
                });
            });
        });

        describe("buttonPrototype", function() {

            //describe("saveObject", function() {

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

            describe("deleteObject", function() {

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

    describe("Utility methods", function() {

        describe("getNewTreeKey()", function() {

            it(`should return a string that is a valid number`, function() {
                const key1 = getNewTreeKey({});
                expect(key1).toEqual(jasmine.any(String));
                expect(parseInt(key1, 10)).not.toBeNaN();
                const key2 = getNewTreeKey(testTreeWrapper.tree);
                expect(key2).toEqual(jasmine.any(String));
                expect(parseInt(key2, 10)).not.toBeNaN();
            });

            it("should return a key that doesn't exist in the passed tree argument", function() {
                const key1 = getNewTreeKey({});
                expect(key1).toEqual("0");
                const key2 = getNewTreeKey(testTreeWrapper.tree);
                expect(key2).toEqual(Object.keys(testTreeWrapper.tree).length.toString());
            });
        });

        describe("isParentlessNode()", function() {

            it("should return true if the object is a node without a parent", function() {
                const obj = {
                    latitude: "4",
                    longitude: "5",
                }
                expect(isParentlessNode(obj)).toBe(true);
            });

            it("should return false if the object is a line", function() {
                const obj = {
                    latitude: "4",
                    longitude: "5",
                    from: "node1",
                    to: "node2"
                }
                expect(isParentlessNode(obj)).toBe(false);
            });
        });
    });

        /*
        describe("Ajax constructor function prototype", function() {

            it("should throw an error when http method is POST and there is no instance of FormData", function() {
                expect(function() {
                    new Ajax(null, "POST", null);
                }).toThrowError();
            });

            describe("send()", function() {

                it ("should not send an instance of FormData when the http method is not POST", function() {
                    const spy = spyOn(XMLHttpRequest.prototype, "send");
                    const ajax = new Ajax(null, "GET", new FormData());
                    ajax.send();
                    expect(spy).toHaveBeenCalled();
                    expect(spy.calls.first().args).toEqual([]);
                });

                it("should return a promise", function() {
                    const request = new Ajax("#");
                    expect(request.send()).toEqual(jasmine.any(Promise));
                });

                it("should send an instance of FormData when the http method is POST", function() {
                    const spy = spyOn(XMLHttpRequest.prototype, "send");
                    const ajax = new Ajax(null, "POST", new FormData());
                    ajax.send();
                    expect(spy).toHaveBeenCalled();
                    expect(spy.calls.first().args[0]).toEqual(jasmine.any(FormData));
                });

                it("should resolve to an instance of XMLHttpRequest", function() {
                    const request = new Ajax("#");
                    return expectAsync(request.send()).toBeResolvedTo(jasmine.any(XMLHttpRequest));
                });

                it("should reject with an instance of XMLHttpRequest", function() {
                    const request = new Ajax("invalid/url");
                    return expectAsync(request.send()).toBeRejectedWith(jasmine.any(XMLHttpRequest));
                })
            });
        });

        describe("FileOperation constructor function prototype,", function() {

            it("should not throw an error when no ProgressModal is provided as an argument", function() {
                expect(function() {
                    new FileOperation(new Ajax("#"), (xhr, resolve, reject) => { resolve(); });
                }).not.toThrowError();
            });

            describe("start(),", function() {
                
                it("should return a promise.", function() {
                    const fileOp = new FileOperation(new Ajax("#"), (xhr, resolve, reject) => {resolve();});
                    expect(fileOp.start()).toEqual(jasmine.any(Promise));
                });

                it(`should call its own success callback when its cancelled flag is false and the underlying 
                Ajax request resolved successfully`, async function() {
                    spyOn(Ajax.prototype, 'send').and.returnValue(Promise.resolve());
                    const success = (xhr, resolve, reject) => { resolve(); }
                    const op = new FileOperation(new Ajax("#"), success);
                    const spy = spyOn(op, "success").and.callThrough();
                    await op.start();
                    expect(spy).toHaveBeenCalled();
                });
            });
        });
        */

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
                expect(deepCopy(obj1)).toEqual(obj1);
                expect(deepCopy(obj1)).not.toBe(obj1);
            });
        });
    });

//Run each test inside this block one at a time, i.e. uncomment one it() function at a time and only run one describe block at a time
xdescribe("Integration tests that require the environment to be prepared correctly and that should be run one at a time", function() {

        let originalTimeout;
        beforeEach(function() {
            originalTimeout = jasmine.DEFAULT_TIMEOUT_INTERVAL;
            jasmine.DEFAULT_TIMEOUT_INTERVAL = 20000;
        });
    
        afterEach(function() {
            jasmine.DEFAULT_TIMEOUT_INTERVAL = originalTimeout;
        });

//    describe("loadFeeder()", function() {
//
//        xit("should have its underlying XMLHttpRequest be opened properly before sending", async function() {
//            const spy = spyOn(XMLHttpRequest.prototype, "send").and.callThrough();
//            const spy2 = spyOn(Ajax.prototype, "send").and.callThrough();
//            await loadFeeder("ABEC Columbia", "publicFeeders", "public");
//
//            console.log("Ajax send was called: " + spy2.calls.count());
//            console.log("xmlhttprequest send was called: " + spy.calls.count());
//            console.log(spy.calls.all());
//        });
//
//        xit("should have its checkFileExists FileOperation resolve successfully", async function() {
//            const spy = spyOn(Promise.prototype, "then").and.callThrough();
//            await loadFeeder("ABEC Columbia", "publicFeeders", "public");
//
//            console.log(spy.calls.all());
//            //console.log("count was: " + spy.calls.count());
//            //expect()
//        });
//
//        xit("should show a sensible error message to the user in case an unrecoverable error occurs", function() {
//
//        });
//
//        xit("should call saveFeeder if something goes wrong")
//    });

    describe("saveFeeder()", function() {

        describe("when not cancelled", function() {

            xit("should send 1 XMLHttpRequest that receives a successful server response", async function() {
                spyOn(window, "reloadWrapper");
                const spy = spyOn(Promise.prototype, "then").and.callThrough();
                await saveFeeder();
                spy.calls.first().object.then(function(xhr) {
                    console.log(xhr);
                    expect(xhr.readyState).toEqual(4);
                    expect(xhr.status >= 200 && xhr.status < 400).toBeTruthy();
                    expect(xhr.responseURL).not.toEqual("");
                });
            });

            xit("should refresh the browser", async function() {
                const spy = spyOn(window, "reloadWrapper");
                await saveFeeder();
                expect(spy).toHaveBeenCalled();
            });

            /** Send the writeFeeder because we overwrite the server's .omd file with the new writes that the user has made.
             */
            xit("should send writeFeeder to the server in the first ajax request", async function() {
                spyOn(window, "reloadWrapper");
                const spy = spyOn(XMLHttpRequest.prototype, "send").and.callThrough();
                /** Modify the writeFeeder, but not the readFeeder. */
                writeFeeder["TestingKey"] = { prop: "testing object"};
                await saveFeeder();
                const feeder = JSON.parse(spy.calls.first().args[0].get("feederObjectJson"));
                expect(feeder).toEqual(writeFeeder);
                expect(feeder).not.toEqual(readFeeder);
            });
        });
    });

    describe("submitForm()", function() {

        describe("when submitting the blankFeeder form", function() {

            describe("when not canceled", function() {

                //it("should send 2 XMLHttpRequests that receive successful responses from the server", async function() {
                //    spyOn(window, "reloadWrapper");
                //    const spy = spyOn(Promise.prototype, "then").and.callThrough();
                //    document.getElementById("blankFeederInput").value = "Test file name";
                //    await submitForm("blankFeederInput", "blankFeederForm");

                //    //console.log(spy.calls.all());
                //    //expect(spy.calls.count()).toEqual(3);

                //    let requests = 0;
                //    for (let i = 0; i <= 2; i++) {
                //        const promise = spy.calls.all()[i].object;
                //        console.log(promise);
                //        promise.then(function(xhr) {
                //            //console.log(xhr);
                //            if (xhr instanceof XMLHttpRequest) {
                //                requests++;
                //            }
                //        });
                //    }
                //    return expect(requests).toEqual(2);

                //    /*for (let i = 0; i <= 2; i++) {
                //        if (i == 0 || i == 2) {
                //            spy.calls.all()[i].object.then(function(xhr) {
                //                console.log(xhr);
                //                expect(xhr.readyState).toEqual(4);
                //                expect(xhr.status >= 200 && xhr.status < 400).toBeTruthy();
                //                expect(xhr.responseURL).not.toEqual("");
                //            });
                //        } 
                //    }*/
                //});

                xit("should refresh the browser", async function() {
                    const spy = spyOn(window, "reloadWrapper");
                    document.getElementById("blankFeederInput").value = "Test file name";
                    await submitForm("blankFeederInput", "blankFeederForm");
                    expect(spy).toHaveBeenCalled();
                });
            });
        });

        describe("when submitting milsoft form", function() {

            describe ("when not canceled", function() {

            });
        });

        describe("when submitting gridlab form", function() {

            describe("when not canceled", function() {

            });
        });

        describe("when submitting cyme form", function() {

            describe("when not canceled", function() {

            });
        });
    });
});
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
        let svg = createDeletableSvgData(gTreeWrapper.tree);
        svg.deleteFrom(gViewport);
        svg = createAddableSvgData(createTreeWrapper(deepCopy(rawTree)));
        svg.addTo(gViewport);
        // Hack
        gTreeWrapper = testTreeWrapper;
    },
    2000
);
//</script>