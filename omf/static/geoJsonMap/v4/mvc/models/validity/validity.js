export { Validity };

/**
 * - Create a custom Boolean object that has a boolean state and a reason for why that state is true or false. This class is an attempt to stop
 *   creating methods that return an object while also having the ability to throw a custom exception. Exceptions and try-catch blocks should be used
 *   for exceptional circumstances. Regular validation logic is not an exceptional circumstance. Using this class allows me to chain together various
 *   if-statements inside of a function and understand which of the if-statements failed the validation
 * - v3 code has many functions that retrieve a value while also having the ability to throw a custom exception and I would like to get rid of those
 *   functions eventually
 */
class Validity {

    #isValid;
    #reason;

    constructor(isValid, reason='') {
        if (typeof isValid !== 'boolean') {
            throw TypeError('The "isValid" argument must be typeof "boolean".');
        }
        if (typeof reason !== 'string') {
            throw TypeError('The "reason" argument must be typeof "string".');
        }
        this.#isValid = isValid;
        this.#reason = reason;
    }

    get isValid() {
        return this.#isValid;
    }

    set isValid(isValid) {
        if (typeof isValid !== 'boolean') {
            throw TypeError('The "isValid" argument must be typeof "boolean".');
        }
        this.#isValid = isValid;
    }

    get reason() {
        return this.#reason;
    }

    set reason(reason) {
        if (typeof reason !== 'string') {
            throw TypeError('The "reason" argument must be typeof "string".');
        }
        this.#reason = reason;
    }
}