/**
 * calc.h - Simple calculator library public API
 * 
 * This is a demo C library used by r2rust-ffi-creator to demonstrate
 * the C-to-Rust FFI migration workflow.
 *
 * All exported functions follow these conventions:
 * - Return 0 on success, negative error code on failure
 * - Error codes defined in calc_error enum
 * - All output parameters are last in the parameter list
 * - NULL output pointers return CALC_ERR_INVALID
 */

#ifndef CALC_H
#define CALC_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ----------------------------------------------------------------
 * Error codes
 * ---------------------------------------------------------------- */

typedef enum {
    CALC_OK           =  0,  /**< Success */
    CALC_ERR_INVALID  = -1,  /**< Invalid argument (NULL pointer, bad range) */
    CALC_ERR_OVERFLOW = -2,  /**< Integer overflow */
    CALC_ERR_DIV_ZERO = -3,  /**< Division by zero */
} calc_error_t;

/* ----------------------------------------------------------------
 * Version information
 * ---------------------------------------------------------------- */

#define CALC_VERSION_MAJOR 1
#define CALC_VERSION_MINOR 0
#define CALC_VERSION_PATCH 0

/**
 * Get the library version string.
 *
 * @return Static string "major.minor.patch", never NULL.
 *         Caller must NOT free this string.
 */
const char *calc_version(void);

/* ----------------------------------------------------------------
 * Arithmetic operations
 *
 * Thread safety: All functions are thread-safe (no global state).
 * Memory: No heap allocation; all operations on stack variables.
 * ---------------------------------------------------------------- */

/**
 * Add two integers.
 *
 * @param a      First operand.
 * @param b      Second operand.
 * @param result Output: a + b. Must not be NULL.
 * @return CALC_OK on success.
 *         CALC_ERR_INVALID if result is NULL.
 *         CALC_ERR_OVERFLOW if the result would overflow int32_t.
 */
int calc_add(int32_t a, int32_t b, int32_t *result);

/**
 * Subtract two integers.
 *
 * @param a      Minuend.
 * @param b      Subtrahend.
 * @param result Output: a - b. Must not be NULL.
 * @return CALC_OK on success.
 *         CALC_ERR_INVALID if result is NULL.
 *         CALC_ERR_OVERFLOW if the result would overflow int32_t.
 */
int calc_sub(int32_t a, int32_t b, int32_t *result);

/**
 * Multiply two integers.
 *
 * @param a      First operand.
 * @param b      Second operand.
 * @param result Output: a * b. Must not be NULL.
 * @return CALC_OK on success.
 *         CALC_ERR_INVALID if result is NULL.
 *         CALC_ERR_OVERFLOW if the result would overflow int32_t.
 */
int calc_mul(int32_t a, int32_t b, int32_t *result);

/**
 * Divide two integers (integer division, truncation toward zero).
 *
 * @param a      Dividend.
 * @param b      Divisor. Must not be 0.
 * @param result Output: a / b (truncated). Must not be NULL.
 * @return CALC_OK on success.
 *         CALC_ERR_INVALID if result is NULL.
 *         CALC_ERR_DIV_ZERO if b == 0.
 */
int calc_div(int32_t a, int32_t b, int32_t *result);

/**
 * Compute the absolute value of an integer.
 *
 * @param a      Input value.
 * @param result Output: |a|. Must not be NULL.
 * @return CALC_OK on success.
 *         CALC_ERR_INVALID if result is NULL.
 *         CALC_ERR_OVERFLOW if a == INT32_MIN (no positive representation).
 */
int calc_abs(int32_t a, int32_t *result);

/* ----------------------------------------------------------------
 * Floating-point operations
 * ---------------------------------------------------------------- */

/**
 * Compute the square root of a double.
 *
 * @param x      Input value. Must be >= 0.
 * @param result Output: sqrt(x). Must not be NULL.
 * @return CALC_OK on success.
 *         CALC_ERR_INVALID if result is NULL or x < 0.
 */
int calc_sqrt(double x, double *result);

#ifdef __cplusplus
}
#endif

#endif /* CALC_H */
