<script>
xdescribe("Unit tests", function() {

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
describe("Integration tests that require the environment to be prepared correctly and that should be run one at a time", function() {

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
</script>