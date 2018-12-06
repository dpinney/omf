//<script>
describe("Unit tests", function() {

    /* TODO: If key === 0, longitude === 0, latitude === 0 (or some other property === 0), the code could 
    break in funny ways. I need to check for undefined explicitly instead of using !<property>
    TODO: build a tree that is more representative of the actual data
    */

    /* Hardcoding test data like this is bad because if the original data ever changes structure, the methods will fail but
    these unit tests will still pass. However, it is necessary because the alternative would be to use the real testTree from a .omd
    file and then these unit tests would be dependent on a particular .omd file which is even worse.
    */
    let testTree;
    let testTreeWrapper;
    const parentKey = "172645";
    const childKey = "172646";
    const lineKey = "57720";
    const lineNodeKey = "144420"
    const grandParentKey = "136920";
    const childLineKey = "0";
    const childLineNodeKey = "-1";

    beforeEach(function() {
        // Tree does NOT contain any cycles
        testTree = {
            //Parent node
            "172645": {
                "name": "house172645", 
                "parent": "node62474181379T62474181443", 
                "object": "house", 
                "longitude": 92.46050261745904, 
                "latitude": 1012.0545354006846, 
            }, 
            //Parent node of parent node (grandparent node)
            "136920": {
                "name": "node62474181379T62474181443", 
                "object": "triplex_meter", 
                "longitude": 110.54543561193137, 
                "latitude": 650.800448635241
            }, 
            //Child of parent node
            "172646": {
                "parent": "house172645", 
                "name": "ZIPload172646", 
                "object": "ZIPload", 
                "longitude": 93.65197702537034, 
                "latitude": 1011.8227442648296, 
            }, 
            //Line connected to parent node
            "57720": {
                "from": "nodeT6246210126716194", 
                "name": "15631", 
                "object": "overhead_line", 
                "longitude": 452.44826409302914, 
                "to": "house172645", 
                "latitude": 324.0822385660431, 
                "configuration": "16194line_configuration57101",
                "phases": "CN"
            }, 
            //Node on the other end of a line connected to the parent node
            "144420": {
                "name": "nodeT6246210126716194", 
                "object": "node", 
                "longitude": 469.95529889121826, 
                "latitude": 328.98233583846013
            }, 
            //Line connected to child node
            "0": {
                "from": "ZIPload172646", 
                "name": "338044", 
                "object": "overhead_line", 
                "longitude": 552.44826409302914, 
                "to": "nodeT9000", 
                "latitude": 124.0822385660431, 
                "configuration": "16194line_configuration57101",
                "phases": "CN"
            }, 
            //Node on the other end of a line connected to the child node
            "-1": {
                "name": "nodeT9000", 
                "object": "node", 
                "longitude": 300.552, 
                "latitude": 23480.5588
            }, 
        };
        testTreeWrapper = createTreeWrapper(testTree);
    });

    describe("Public interface methods", function() {

        describe("createTreeWrapper()", function() {

            it("should return a TreeWrapper with an 'tree' property that is identical to the passed tree argument", function() {
                expect(testTreeWrapper.tree).toBe(testTree);
            });

            it(`should return a TreeWrapper with a 'names' property that is a map between every name and key of an object in the 
            tree`, function() {
                expect(testTreeWrapper.names).toEqual(
                    {
                        "house172645": "172645",
                        "node62474181379T62474181443": "136920",
                        "ZIPload172646": "172646",
                        "15631": "57720",
                        "nodeT6246210126716194": "144420",
                        "338044": "0",
                        "nodeT9000": "-1"
                    }
                );
            });
        });

        describe("treeWrapperPrototype", function() {
            
            describe("delete()", function() {

                describe("when the tree object with the passed key argument has NO children or connected lines", function() {

                    it(`should delete the tree object with the passed key from this TreeWrapper`, function() {
                        expect(testTreeWrapper.tree[childLineKey]).toBeDefined();
                        expect(testTreeWrapper.names[testTreeWrapper.tree[childLineKey].name]).toBeDefined(); 
                        expect(Object.keys(testTreeWrapper.tree).length).toEqual(7);
                        expect(Object.keys(testTreeWrapper.names).length).toEqual(7);
                        testTreeWrapper.delete(childLineKey);
                        expect(testTreeWrapper.tree[childLineKey]).toBeUndefined();
                        expect(testTreeWrapper.names[testTreeWrapper.tree[childLineKey]]).toBeUndefined();
                        expect(Object.keys(testTreeWrapper.tree).length).toEqual(6);
                        expect(Object.keys(testTreeWrapper.names).length).toEqual(6);
                    });

                    it("should return a TreeWrapper that contains only the tree object with the passed key argument", function() {
                        const deletedObject = testTreeWrapper.tree[childLineKey]
                        const deletedKey = childLineKey;
                        const subtreeWrapper = testTreeWrapper.delete(childLineKey);
                        expect(subtreeWrapper.tree[childLineKey]).toBe(deletedObject);
                        expect(subtreeWrapper.names[subtreeWrapper.tree[childLineKey].name]).toEqual(deletedKey);
                        expect(Object.keys(subtreeWrapper.tree).length).toEqual(1);
                        expect(Object.keys(subtreeWrapper.names).length).toEqual(1);
                    });
                });

                describe("when the tree object with the passed key argument HAS children or connected lines", function() {

                    it("should throw an error", function() {
                        expect(function() {
                            testTreeWrapper.delete(childLineNodeKey);
                        }).toThrowError();
                    });
                });
            });

            describe("recursiveDelete()", function() {

                describe("when the tree object with the passed key argument is a node", function() {

                    it(`should delete from this TreeWrapper: 1) the tree object with the passed key 2) its direct children 
                    3) all children of children recursively 4) lines connected to the tree object with the passed key 
                    5) lines that are connected to children of children`, function() {
                        const keys = [grandParentKey, parentKey, childKey, lineKey, childLineKey];
                        const names = []
                        for (let key of keys) {
                            expect(testTreeWrapper.tree[key]).toBeDefined();
                            const name = testTreeWrapper.tree[key].name;
                            names.push(name);
                            expect(testTreeWrapper.names[name]).toBeDefined();
                        }
                        expect(Object.keys(testTreeWrapper.tree).length).toEqual(7);
                        expect(Object.keys(testTreeWrapper.names).length).toEqual(7);
                        testTreeWrapper.recursiveDelete(grandParentKey);
                        for (let key of keys) {
                            expect(testTreeWrapper.tree[key]).toBeUndefined();
                            expect(testTreeWrapper.names[names.shift()]).toBeUndefined();
                        }
                        expect(Object.keys(testTreeWrapper.tree).length).toEqual(2);
                        expect(Object.keys(testTreeWrapper.names).length).toEqual(2);
                    });

                    it(`should return a TreeWrapper that contains 1) the tree object with the passed key
                    2) its direct children (if they exist), 3) all children of children 4) lines
                    connected to the tree object with the passed key 5) lines that are connected to children
                    of children`, function() {
                        const keys = [grandParentKey, parentKey, childKey, lineKey, childLineKey];
                        const deletedObjects = []
                        const deletedKeys = [];
                        for (let key of keys) {
                            deletedObjects.push(testTreeWrapper.tree[key]);
                            deletedKeys.push(key);
                        }
                        const subtreeWrapper = testTreeWrapper.recursiveDelete(grandParentKey);
                        for (let key of keys) {
                            expect(subtreeWrapper.tree[key]).toBe(deletedObjects.shift());
                            expect(subtreeWrapper.names[subtreeWrapper.tree[key].name]).toEqual(deletedKeys.shift());
                        }
                        expect(Object.keys(subtreeWrapper.tree).length).toEqual(keys.length); 
                        expect(Object.keys(subtreeWrapper.names).length).toEqual(keys.length); 
                    });
                });

                describe("when the tree argument with the passed key argument is a line", function() {

                    it("should delete only the line from this TreeWrapper", function() {
                        const deletedObject = testTreeWrapper.tree[childLineKey];
                        expect(Object.keys(testTreeWrapper.tree).length).toEqual(7); 
                        expect(Object.keys(testTreeWrapper.names).length).toEqual(7); 
                        testTreeWrapper.recursiveDelete(childLineKey);
                        expect(testTreeWrapper.tree[childLineKey]).toBeUndefined();
                        expect(testTreeWrapper.names[deletedObject.name]).toBeUndefined();
                        expect(Object.keys(testTreeWrapper.tree).length).toEqual(6); 
                        expect(Object.keys(testTreeWrapper.names).length).toEqual(6); 
                    });

                    it(`should return a TreeWrapper that only contains the line`, function() {
                        const deletedObject = testTreeWrapper.tree[childLineKey]
                        const deletedKey = childLineKey;
                        const subtreeWrapper = testTreeWrapper.recursiveDelete(childLineKey);
                        expect(subtreeWrapper.tree[childLineKey]).toBe(deletedObject);
                        expect(subtreeWrapper.names[subtreeWrapper.tree[childLineKey].name]).toEqual(deletedKey);
                        expect(Object.keys(subtreeWrapper.tree).length).toEqual(1);
                        expect(Object.keys(subtreeWrapper.names).length).toEqual(1);
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
                        expect(Object.keys(testTreeWrapper.tree).length).toEqual(7);
                        expect(Object.keys(testTreeWrapper.names).length).toEqual(7);
                        testTreeWrapper.insert(tObj);
                        expect(testTreeWrapper.tree[tObj.key]).toBe(tObj.data);
                        expect(testTreeWrapper.names[tObj.data.name]).toEqual(tObj.key);
                        expect(Object.keys(testTreeWrapper.tree).length).toEqual(8);
                        expect(Object.keys(testTreeWrapper.names).length).toEqual(8);
                    });
                });

                describe(`when a tree object with an identical key to the TreeObject already exists
                in this TreeWrapper`, function() {

                    it(`should overwrite the tree object data with data from the TreeObject`, function() {
                        const tObj = createTreeObject(parentKey, testTreeWrapper);
                        tObj.data.object = "blahblahblah";
                        tObj.data.longitude = "-1000";
                        tObj.data.latitude = "-1111";
                        expect(Object.keys(testTreeWrapper.tree).length).toEqual(7);
                        expect(Object.keys(testTreeWrapper.names).length).toEqual(7);
                        testTreeWrapper.insert(tObj);
                        expect(testTreeWrapper.tree[parentKey]).toBe(tObj.data);
                        expect(testTreeWrapper.names[testTreeWrapper.tree[parentKey].name]).toEqual(tObj.key);
                        expect(Object.keys(testTreeWrapper.tree).length).toEqual(7);
                        expect(Object.keys(testTreeWrapper.names).length).toEqual(7);
                    });
                });

                describe("when the TreeObject represents a node", function() {

                    it(`should return a TreeWrapper that contains 1) the tree object represented by the TreeObject argument
                    2) the parent of the tree object (if one exists) 3) the direct children of the tree object (if they exist)
                    4) lines that are connected to the tree object (if there are any) 5) nodes on the other ends of lines that
                    are connected to the tree object (if there are connected lines)`, function() {
                        const tObj = createTreeObject(parentKey, testTreeWrapper);
                        const keys = [parentKey, grandParentKey, childKey, lineKey, lineNodeKey];
                        const subtreeWrapper = testTreeWrapper.insert(tObj);
                        for (let key of keys) {
                            expect(subtreeWrapper.tree[key]).toBe(testTreeWrapper.tree[key]);
                            expect(subtreeWrapper.names[subtreeWrapper.tree[key].name]).toEqual(testTreeWrapper.names[testTreeWrapper.tree[key].name]);
                        }
                        expect(Object.keys(subtreeWrapper.tree).length).toEqual(keys.length);
                        expect(Object.keys(subtreeWrapper.names).length).toEqual(keys.length);
                    });
                });

                describe("when the TreeObject represents a line", function() {

                    it(`should return a TreeWrapper that contains the line and the nodes on either end of
                    the line`, function() {
                        const keys = [lineKey, parentKey, lineNodeKey];
                        const tObj = createTreeObject(lineKey, testTreeWrapper);
                        const subtreeWrapper = testTreeWrapper.insert(tObj);
                        for (let key of keys) {
                            expect(subtreeWrapper.tree[key]).toBe(testTreeWrapper.tree[key]);
                            expect(subtreeWrapper.names[subtreeWrapper.tree[key].name]).toEqual(testTreeWrapper.names[testTreeWrapper.tree[key].name]);
                        }
                        expect(Object.keys(subtreeWrapper.tree).length).toEqual(keys.length);
                        expect(Object.keys(subtreeWrapper.names).length).toEqual(keys.length);
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

                it("should throw an error when the given key doesn't exist in the tree", function() {
                    expect(function() {
                        createTreeObject(10, createTreeWrapper({}));
                    }).toThrowError();
                });
            });

            describe("when invoked with (map, treeWrapper) arguments", function() {

                it("should return a TreeObject with data that is equivalent to the map, but not the same object", function() {
                    const map = {
                        prop: "cool value"
                    }
                    const tObj = createTreeObject(map, createTreeWrapper({}));
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

                it("should call update()", function() {
                    const spy = spyOn(treeObjectPrototype, "update").and.callThrough();
                    createTreeObject({}, createTreeWrapper({}));
                    expect(spy).toHaveBeenCalled();
                });

                it("should throw any error thrown by update()", function() {
                    const error = "Custom Error"
                    const spy = spyOn(treeObjectPrototype, "update").and.throwError(error);
                    expect(function() {
                        createTreeObject({}, createTreeWrapper({}));
                    }).toThrowError(error)
                });

                it("should call getNewTreeKey()", function() {
                    const spy = spyOn(window, "getNewTreeKey").and.callThrough();
                    createTreeObject({}, createTreeWrapper({}));
                    expect(spy).toHaveBeenCalled();
                });
            });
        });

        describe("treeObjectPrototype", function() {
            //no public methods?
        });

        describe("createAddableSvgData()", function() {

            it("should return an object with an array of lines and an array of circles", function() {
                const treeWrapper = createTreeWrapper({});
                const svgData = createAddableSvgData(treeWrapper);
                expect(svgData.circles).toEqual(jasmine.any(Array));
                expect(svgData.lines).toEqual(jasmine.any(Array));
            });

            describe("when the treeWrapper.tree argument is non-empty", function() {

                it("should return an object with the correct number of circles and lines", function() {
                    const svgData = createAddableSvgData(testTreeWrapper);
                    /* circles: grandparent, parent, child, lineNode, childLineNode
                        lines: line, childLine, 
                        parent-child lines: child-parent, parent-grandparent
                    */
                    expect(svgData.circles.length).toEqual(5);
                    expect(svgData.lines.length).toEqual(4);
                });
            });
        });
    });

    describe("Private helper methods", function() {

        describe("treeWrapperPrototype", function() {

            describe("getChildrenOf()", function() {

                describe("when the tree object with the passed key argument has children", function() {

                    it(`should return a TreeWrapper that only contains references to child tree objects of
                    the tree object with the passed key argument`, function() {
                        const subtreeWrapper = testTreeWrapper.getChildrenOf(parentKey);
                        expect(subtreeWrapper.tree[childKey]).toBe(testTreeWrapper.tree[childKey]);
                        expect(Object.keys(subtreeWrapper.tree).length).toEqual(1);
                        expect(subtreeWrapper.names[subtreeWrapper.tree[childKey].name]).toEqual(testTreeWrapper.names[testTreeWrapper.tree[childKey].name]);
                        expect(Object.keys(subtreeWrapper.names).length).toEqual(1);
                    });
                });

                describe("when the tree object with the passed key argument does not have children", function() {

                    it("should return an empty TreeWrapper", function() {
                        const subtreeWrapper = testTreeWrapper.getChildrenOf(lineKey);
                        expect(Object.keys(subtreeWrapper.tree).length).toEqual(0);
                        expect(Object.keys(subtreeWrapper.names).length).toEqual(0);
                    });
                });
            });
            
            describe("getConnectedLinesOf()", function() {

                describe("when the tree object with the passed key argument has connected lines", function() {

                    it(`should return a TreeWrapper that only contains references to tree objects that are lines
                    which connect to the tree object with passed key argument`, function() {
                        const subtreeWrapper = testTreeWrapper.getConnectedLinesOf(childKey);
                        expect(subtreeWrapper.tree[childLineKey]).toBe(testTreeWrapper.tree[childLineKey]);
                        expect(Object.keys(subtreeWrapper.tree).length).toEqual(1);
                        expect(subtreeWrapper.names[subtreeWrapper.tree[childLineKey].name]).toEqual(testTreeWrapper.names[testTreeWrapper.tree[childLineKey].name]);
                        expect(Object.keys(subtreeWrapper.names).length).toEqual(1);
                    });
                });

                describe("when the tree object with the passed key argument has no connected lines", function() {

                    it("should return an empty TreeWrapper", function() {
                        const subtreeWrapper = testTreeWrapper.getConnectedLinesOf(lineKey);
                        expect(Object.keys(subtreeWrapper.tree).length).toEqual(0);
                        expect(Object.keys(subtreeWrapper.names).length).toEqual(0);
                    });
                });
            });

            describe("merge()", function() {

                describe("when no keys array is passed", function() {

                    it(`should merge the entire TreeWrapper argument into this TreeWrapper`, function() {
                        /* Both TreeWrapper.trees should contain the same objects. Both TreeWrapper.names 
                        should contain the same names
                        */
                        const keys = [grandParentKey, parentKey, childKey, lineKey, lineNodeKey, childLineKey, childLineNodeKey];
                        const subtreeWrapper = createTreeWrapper({});
                        subtreeWrapper.merge(testTreeWrapper);
                        for (let key of keys) {
                            expect(subtreeWrapper.tree[key]).toBe(testTreeWrapper.tree[key]);
                            expect(subtreeWrapper.names[subtreeWrapper.tree[key].name]).toEqual(testTreeWrapper.names[testTreeWrapper.tree[key].name]);
                        }
                        expect(Object.keys(subtreeWrapper.tree).length).toEqual(Object.keys(testTreeWrapper.tree).length);
                        expect(Object.keys(subtreeWrapper.names).length).toEqual(Object.keys(testTreeWrapper.tree).length);
                    });
                });

                describe(`when a keys array argument is passed`, function() {
                    
                    it(`should merge only tree objects with the specified keys from the TreeWrapper agument into this
                    TreeWrapper`, function() {
                        const keys = [grandParentKey, lineNodeKey];
                        const subtreeWrapper = createTreeWrapper({});
                        subtreeWrapper.merge(testTreeWrapper, keys);
                        for (let key of keys) {
                            expect(subtreeWrapper.tree[key]).toBe(testTreeWrapper.tree[key]);
                            expect(subtreeWrapper.names[subtreeWrapper.tree[key].name]).toEqual(testTreeWrapper.names[testTreeWrapper.tree[key].name]);
                        }
                        expect(Object.keys(subtreeWrapper.tree).length).toEqual(keys.length);
                        expect(Object.keys(subtreeWrapper.names).length).toEqual(keys.length);
                    });
                });
            });

            describe(`getSubtreeToDelete()`, function() {

                describe("when the tree object with the passed key argument is a node", function() {

                    it(`should return a TreeWrapper that contains direct children and lines that connect to the tree object
                    with the passed key argument`, function() {
                        const keys = [childKey, lineKey];
                        const subtreeWrapper = testTreeWrapper.getSubtreeToDelete(parentKey, []);
                        for (let key of keys) {
                            expect(subtreeWrapper.tree[key]).toBe(testTreeWrapper.tree[key]);
                            expect(subtreeWrapper.names[subtreeWrapper.tree[key].name]).toEqual(testTreeWrapper.names[testTreeWrapper.tree[key].name]);
                        }
                        expect(Object.keys(subtreeWrapper.tree).length).toEqual(3); //child, line, and line connected to child
                        expect(Object.keys(subtreeWrapper.names).length).toEqual(3); //child, line, and line connected to child
                    });

                    it(`should return a TreeWrapper that contains children of children (etc.) and all lines that connect to 
                    any of those children`, function() { 
                        const keys = [parentKey, lineKey, childKey, childLineKey];
                        const subtreeWrapper = testTreeWrapper.getSubtreeToDelete(grandParentKey, []);
                        for (let key of keys) {
                            expect(subtreeWrapper.tree[key]).toBe(testTreeWrapper.tree[key]);
                            expect(subtreeWrapper.names[subtreeWrapper.tree[key].name]).toEqual(testTreeWrapper.names[testTreeWrapper.tree[key].name]);
                        }
                        expect(Object.keys(subtreeWrapper.tree).length).toEqual(4); //parent, line connected to parent, child, line connected to child (4)
                        expect(Object.keys(subtreeWrapper.names).length).toEqual(4); //parent, line connected to parent, child, line connected to child (4)
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
                        const treeWrapper = createTreeWrapper(tree);
                        const subtreeWrapper = treeWrapper.getSubtreeToDelete("1", []);
                        expect(subtreeWrapper.tree["1"]).toBe(treeWrapper.tree["1"]);
                        expect(subtreeWrapper.tree["2"]).toBe(treeWrapper.tree["2"]);
                        expect(Object.keys(subtreeWrapper.tree).length).toEqual(2);
                        expect(subtreeWrapper.names["node226"]).toEqual(treeWrapper.names["node226"]);
                        expect(subtreeWrapper.names["node134"]).toEqual(treeWrapper.names["node134"]);
                        expect(Object.keys(subtreeWrapper.names).length).toEqual(2);
                    });
                });
                
                describe("when the tree object with the passed key argument is a line", function() {

                    it(`should return an empty TreeWrapper`, function() {
                        const subtreeWrapper = testTreeWrapper.getSubtreeToDelete(lineKey, []);
                        expect(Object.keys(subtreeWrapper.tree).length).toEqual(0);
                        expect(Object.keys(subtreeWrapper.names).length).toEqual(0);
                    });
                });
            });

            describe("getParentOf()", function() {

                describe("when the tree object with the passed key argument has a parent", function() {

                    it(`should return a TreeWrapper that contains only the parent of the tree object with the passed key
                    argument`, function() {
                        const subtreeWrapper = testTreeWrapper.getParentOf(parentKey);
                        expect(subtreeWrapper.tree[grandParentKey]).toBe(testTreeWrapper.tree[grandParentKey]);
                        expect(subtreeWrapper.names[subtreeWrapper.tree[grandParentKey].name]).toEqual(testTreeWrapper.names[testTreeWrapper.tree[grandParentKey].name]);
                        expect(Object.keys(subtreeWrapper.tree).length).toEqual(1);
                        expect(Object.keys(subtreeWrapper.names).length).toEqual(1);
                    });
                });

                describe("when the tree object with the passed key doesn't have a parent", function() {

                    it(`should return an empty TreeWrapper`, function() {
                        const subtreeWrapper = testTreeWrapper.getParentOf(lineKey);
                        expect(Object.keys(subtreeWrapper.tree).length).toEqual(0);
                        expect(Object.keys(subtreeWrapper.names).length).toEqual(0);
                    });
                });
            });

            describe("getPairedNodesOf()", function() {

                describe("when the tree object with the passed key has paired nodes", function() {

                    it(`should return a TreeWrapper that contains only those nodes which are on the other ends of lines
                    that are connected to the tree object with the passed key argument`, function() {
                        // Test for when the searched key is the "from" node and the paired node is the "to" node
                        const subtreeWrapper = testTreeWrapper.getPairedNodesOf(childKey);
                        expect(subtreeWrapper.tree[childLineNodeKey]).toBe(testTreeWrapper.tree[childLineNodeKey]);
                        expect(subtreeWrapper.names[subtreeWrapper.tree[childLineNodeKey].name]).toEqual(testTreeWrapper.names[testTreeWrapper.tree[childLineNodeKey].name]);
                        expect(Object.keys(subtreeWrapper.tree).length).toEqual(1);
                        expect(Object.keys(subtreeWrapper.names).length).toEqual(1);
                    });

                    it(`should return a TreeWrapper that contains only those nodes which are on the other ends of lines
                    that are connected to the tree object with the passed key argument`, function() {
                        // Test for when the searched key is the "to" node and the paired node is the "from" node
                        const subtreeWrapper = testTreeWrapper.getPairedNodesOf(parentKey);
                        expect(subtreeWrapper.tree[lineNodeKey]).toBe(testTreeWrapper.tree[lineNodeKey]);
                        expect(subtreeWrapper.names[subtreeWrapper.tree[lineNodeKey].name]).toEqual(testTreeWrapper.names[testTreeWrapper.tree[lineNodeKey].name]);
                        expect(Object.keys(subtreeWrapper.tree).length).toEqual(1);
                        expect(Object.keys(subtreeWrapper.names).length).toEqual(1);
                    });
                });

                describe("when the tree object with the passed key has no paired nodes", function() {

                    it(`should return an empty TreeWrapper`, function() {
                        const subtreeWrapper = testTreeWrapper.getPairedNodesOf(lineKey);
                        expect(Object.keys(subtreeWrapper.tree).length).toEqual(0);
                        expect(Object.keys(subtreeWrapper.names).length).toEqual(0);
                    });
                });
            });

            describe("getNodeEndsOf()", function() {

                describe("when the tree object with the passed key argument is a line", function() {

                    it(`should return a TreeWrapper that contains only those nodes which are on either side of the line
                    that is represented by the tree object with the passed key argument.`, function() {
                        const keys = [parentKey, lineNodeKey];
                        const subtreeWrapper = testTreeWrapper.getNodeEndsOf(lineKey);
                        for (let key of keys) {
                            expect(subtreeWrapper.tree[key]).toBe(testTreeWrapper.tree[key]);
                            expect(subtreeWrapper.names[subtreeWrapper.tree[key].name]).toEqual(testTreeWrapper.names[testTreeWrapper.tree[key].name]);
                        }
                        expect(Object.keys(subtreeWrapper.tree).length).toEqual(keys.length);
                        expect(Object.keys(subtreeWrapper.names).length).toEqual(keys.length);
                    });
                });

                describe("when the tree object with the passed key argument is NOT a line", function() {

                    it(`should return an empty TreeWrapper`, function() {
                        const subtreeWrapper = testTreeWrapper.getNodeEndsOf(childKey);
                        expect(Object.keys(subtreeWrapper.tree).length).toEqual(0);
                        expect(Object.keys(subtreeWrapper.names).length).toEqual(0);
                    });
                });
            });

            describe("getSubtreeToRedraw()", function() {

                describe("when tree object with the passed key argument is a node", function() {

                    it(`should return a TreeWrapper containing: 1) lines that connect to the tree object with the passed key argument
                    2) direct children of the tree object with the passed key argument, 3) the parent of the tree object with the 
                    passed key argument 4) nodes on the other ends of lines that connect to the tree object with the passed key 
                    argument`, function() {
                        const keys = [grandParentKey, childKey, lineKey, lineNodeKey];
                        const subtreeWrapper = testTreeWrapper.getSubtreeToRedraw(parentKey);
                        for (let key of keys) {
                            expect(subtreeWrapper.tree[key]).toBe(testTreeWrapper.tree[key]);
                            expect(subtreeWrapper.names[subtreeWrapper.tree[key].name]).toEqual(testTreeWrapper.names[testTreeWrapper.tree[key].name]);
                        }
                        expect(Object.keys(subtreeWrapper.tree).length).toEqual(4);
                        expect(Object.keys(subtreeWrapper.names).length).toEqual(4);
                    });
                });

                describe("when the tree object with the passed key argument is a line", function() {

                    it(`should return a TreeWrapper containing 2 nodes on either end of the line`, function() {
                        const keys = [parentKey, lineNodeKey];
                        const subtreeWrapper = testTreeWrapper.getSubtreeToRedraw(lineKey);
                        for (let key of keys) {
                            expect(subtreeWrapper.tree[key]).toBe(testTreeWrapper.tree[key]);
                            expect(subtreeWrapper.names[subtreeWrapper.tree[key].name]).toEqual(testTreeWrapper.names[testTreeWrapper.tree[key].name]);
                        }
                        expect(Object.keys(subtreeWrapper.tree).length).toEqual(keys.length);
                        expect(Object.keys(subtreeWrapper.names).length).toEqual(keys.length);
                    });
                });
            });
        });

        describe("treeObjectPrototype", function() {
            // no private methods?
        });

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
    });

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
                const obj2 = {
                    prop1: "a",
                    prop2: {
                        prop1: 123,
                        prop2: {
                            prop1: true,
                            prop2: ["10", 11, false]
                        }
                    }
                };
                const obj3 = {
                    prop1: "a",
                    prop2: {
                        prop1: 123,
                        prop2: {
                            prop1: true,
                            prop2: ["10", 11, true]
                        }
                    }
                };
                expect(deepCopy(obj1)).toEqual(obj2);
                expect(deepCopy(obj1)).not.toEqual(obj3);
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

    xdescribe("saveFeeder()", function() {

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

        xdescribe("when submitting milsoft form", function() {

            describe ("when not canceled", function() {

            });
        });

        xdescribe("when submitting gridlab form", function() {

            describe("when not canceled", function() {

            });
        });

        xdescribe("when submitting cyme form", function() {

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
    },
    1000
);
//</script>