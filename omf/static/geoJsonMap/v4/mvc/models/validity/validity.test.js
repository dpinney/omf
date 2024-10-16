import { describe, expect, it, vi } from 'vitest';
import { Validity } from './validity.js';

/**
 * - Remember
 *  - If a function has no control logic (e.g. getter functions), then I shouldn't test that function
 */

describe('Validity', () => {

    describe('given an isValid argument that is not a boolean', () => {

        it('throws an exception', () => {
            expect(() => new Validity('foobar')).toThrow(/must be typeof "boolean"/);
        });
    });

    describe('given an isValid argument that is true', () => {

        it('sets this.isValid to true', () => {
            const validity = new Validity(true);
            expect(validity.isValid).toBe(true);
        });
    });

    describe('given an isValid argument that is false', () => {

        it('sets this.isValid to false', () => {
            const validity = new Validity(false);
            expect(validity.isValid).toBe(false);
        });
    });


    describe('given a reason argument that is not a string', () => {

        it('throws an exception', () => {
            expect(() => new Validity(true, 5)).toThrow(/must be typeof "string"/);
        });
    });

    describe('given a reason argument that is a string', () => {

        it('sets this.reason to equal the string', () => {
            const validity = new Validity(false, 'Number out of range.');
            expect(validity.reason).toEqual('Number out of range.');
        });
    });


    describe('set isValid', () => {

        describe('given a true boolean argument', () => {

            it('sets this.#isValid to true', () => {
                const validity = new Validity(false);
                validity.isValid = true;
                expect(validity.isValid).toBe(true);
            });
        });

        describe('given a false boolean argument', () => {

            it('sets this.#isValid to be false', () => {
                const validity = new Validity(true);
                validity.isValid = false;
                expect(validity.isValid).toBe(false);
            });
        });
    });

    describe('set reason', () => {

        describe('given a reason argument that is not a string', () => {

            it('throws an exception', () => {
                const validity = new Validity(true);
                expect(() => validity.reason = 5).toThrow(/must be typeof "string"/);
            });
        });

        describe('given a reason argument that is a string', () => {

            it('sets this.reason to be the string', () => {
                const validity = new Validity(false);
                validity.reason = 'Number out of range.';
                expect(validity.reason).toEqual('Number out of range.');
            });
        });
    });
});