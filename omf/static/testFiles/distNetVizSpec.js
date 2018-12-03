//<script>
describe("Unit tests", function() {

    /* Hardcoding test data like this is bad because if the original data ever changes structure, the methods will fail but
    these unit tests will still pass. However, it is necessary because the alternative would be to use the real testTree from a .omd
    file and then these unit tests would be dependent on a particular .omd file which is even worse.
    */
    let testTree;
    let testTreeWrapper;
    const parentKey = "172645";
    const childKey = "172646";

    beforeEach(function() {
        testTree = {
            //Parent node
            "172645": {
                "name": "house172645", 
                "parent": "node62474181379T62474181443", 
                "object": "house", 
                "longitude": 92.46050261745904, 
                "latitude": 1012.0545354006846, 
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
            //Parent node of parent node
            "136920": {
                "name": "node62474181379T62474181443", 
                "object": "triplex_meter", 
                "longitude": 110.54543561193137, 
                "latitude": 650.800448635241
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
                        "ZIPload172646": "172646",
                        "15631": "57720",
                        "nodeT6246210126716194": "144420",
                        "node62474181379T62474181443": "136920"
                    }
                );
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

            describe("deleteFrom()", function() {

                describe("when this TreeObject has no children or connected lines", function() {

                    it("should remove this TreeObject from the TreeWrapper.tree", function() {
                        const tObj = createTreeObject(childKey, testTreeWrapper);
                        expect(testTreeWrapper.tree[childKey]).toBeDefined();
                        expect(testTreeWrapper.tree[childKey]).toEqual(tObj.data);
                        tObj.deleteFrom(testTreeWrapper);
                        expect(testTreeWrapper.tree[childKey]).toBeUndefined();
                    });
                });

                it(`should throw an exception when this TreeObject has existing children in the TreeWrapper.tree, 
                and not remove this TreeObject`, function() {

                });

                it(`should throw an exception when this TreeObject has a line connected to it in the TreeWrapper.tree,
                and not remove this TreeObject`, function() {

                });

                it(`should throw an exception if this TreeObject does not exist in the TreeWrapper.tree, and
                not remove this TreeObject`, function() {

                });
            });
        });

        describe("createAddableSvgData()", function() {

            it("should return an object with an array of lines and an array of circles", function() {
                const treeWrapper = createTreeWrapper({});
                const svgData = createAddableSvgData(treeWrapper);
                expect(svgData.circles).toEqual(jasmine.any(Array));
                expect(svgData.lines).toEqual(jasmine.any(Array));
            });

            describe("when the treeWrapper.tree argument is non-empty", function() {

                it("should return an object with a non-empty array of circles and/or a non-empty array of lines", function() {
                    // This isn't a great test, but SOMETHING should be rendered if a non-empty tree is passed in
                    const svgData = createAddableSvgData(testTreeWrapper);
                    expect(svgData.circles.length).toBeGreaterThan(0);
                    expect(svgData.lines.length).toBeGreaterThan(0);
                });
            });
        });
    });

    describe("Private helper methods", function() {

        describe("treeObjectPrototype", function() {

            describe("getSubtreeToDelete()", function() {

                it(`should return a subtreeWrapper that contains a reference to the identical object in 
                the TreeWrapper.tree that is equivalent to this TreeObject`, function() {
                    const obj = createTreeObject(childKey, testTreeWrapper);
                    const subtreeWrapper = obj.getSubtreeToDelete(testTreeWrapper);
                    expect(subtreeWrapper.tree[obj.key]).toBe(testTreeWrapper.tree[obj.key]);
                });

                it(`should return a subtreeWrapper that contains children of this TreeObject`, function() {
                    const obj = createTreeObject(parentKey, testTreeWrapper);
                    const subtreeWrapper = obj.getSubtreeToDelete(testTreeWrapper);
                    expect(subtreeWrapper.tree[childKey]).toBe(testTreeWrapper.tree[childKey]);
                });

                it("should return a subtreeWrapper that contains lines which connect to this TreeObject", function() {

                });

                it("should return a subtreeWrapper that does not contain the parent of this TreeObject", function() {

                });

                it(`should return a subtreeWrapper that does not contain tree objects 
                which are connected to lines that connect to this TreeObject`, function() {

                });

                it(`should throw an error if this TreeObject does not exist in the TreeWrapper.tree`, function() {
                    const obj = createTreeObject({}, testTreeWrapper);
                    //Just checking to make sure I understand how the key of the created TreeObject is being set
                    expect(obj.key).toEqual(Object.keys(testTree).length.toString()); // should equal 5
                    expect(function() {
                        obj.getSubtreeToDelete(testTreeWrapper);
                    }).toThrowError();
                });
            });

            describe("getChildren()", function() {

                it(`should return a subtreeWrapper that contains only references to tree objects that represent
                direct children of the tree object that is represented by this TreeObject`, function() {
                    const obj = createTreeObject(parentKey, testTreeWrapper);
                    const subtreeWrapper = obj.getChildren(testTreeWrapper);
                    expect(subtreeWrapper.tree[childKey.toString()]).toBe(testTreeWrapper.tree[childKey.toString()]);
                    expect(Object.keys(subtreeWrapper.tree).length).toEqual(1);
                });

                it(`should not throw an error if the tree object represented by this TreeObject does not have any children`, function() {
                    const obj = createTreeObject(childKey, testTreeWrapper);
                    let subtreeWrapper;
                    expect(function() {
                        subtreeWrapper = obj.getChildren(testTreeWrapper)
                    }).not.toThrowError();
                    expect(Object.keys(subtreeWrapper.tree).length).toEqual(0);
                });
            });

            describe("getConnectedLines()", function() {

                it(`should return a subtree that contains only references to testTree objects that represent
                lines that connect to the tree object that is represented by this TreeObject`, function() {
                    const obj = createTreeObject(parentKey, testTreeWrapper);
                    const subtreeWrapper = obj.getConnectedLines(testTreeWrapper);
                    expect(subtreeWrapper.tree["57720"]).toBe(testTreeWrapper.tree["57720"]);
                    expect(Object.keys(subtreeWrapper.tree).length).toEqual(1);
                });

                it(`should not throw an error if the tree object represented by this TreeObject does not 
                have any connected lines`, function() {
                    const obj = createTreeObject(childKey, testTreeWrapper);
                    let subtreeWrapper;
                    expect(function() {
                        subtreeWrapper = obj.getConnectedLines(testTreeWrapper);
                    }).not.toThrowError();
                    expect(Object.keys(subtreeWrapper.tree).length).toEqual(0);
                });
            });
        });

        describe("getParentObject()", function() {

            it("should return a tree object that is the parent of the testTreeWrapper.tree[childKey] object", function() {
                const parent = getParentObject(childKey, testTreeWrapper);
                expect(parent).toBe(testTreeWrapper.tree[parentKey.toString()]);
            });
        });

        describe("getLineEnds()", function() {

            it(`should return an object that contains references to the 'to' and 'from' 
            nodes that are on either end of the testTreeWrapper.tree[lineKey] object`, function() {
                const nodes = getLineEnds("57720", testTreeWrapper);
                expect(nodes.sourceNode).toBe(testTreeWrapper.tree["144420"]);
                expect(nodes.targetNode).toBe(testTreeWrapper.tree["172645"]);
            });
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