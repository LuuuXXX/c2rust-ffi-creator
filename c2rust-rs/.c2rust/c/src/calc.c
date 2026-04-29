/**
 * calc.c - Simple calculator library implementation
 */

#include "calc.h"
#include <stddef.h>
#include <stdint.h>
#include <math.h>

const char *calc_version(void)
{
    return "1.0.0";
}

int calc_add(int32_t a, int32_t b, int32_t *result)
{
    if (result == NULL) {
        return CALC_ERR_INVALID;
    }

    /* Check for overflow: a + b > INT32_MAX or a + b < INT32_MIN */
    if ((b > 0 && a > INT32_MAX - b) ||
        (b < 0 && a < INT32_MIN - b)) {
        return CALC_ERR_OVERFLOW;
    }

    *result = a + b;
    return CALC_OK;
}

int calc_sub(int32_t a, int32_t b, int32_t *result)
{
    if (result == NULL) {
        return CALC_ERR_INVALID;
    }

    /* Check for overflow: a - b may overflow when b == INT32_MIN */
    if ((b < 0 && a > INT32_MAX + b) ||
        (b > 0 && a < INT32_MIN + b)) {
        return CALC_ERR_OVERFLOW;
    }

    *result = a - b;
    return CALC_OK;
}

int calc_mul(int32_t a, int32_t b, int32_t *result)
{
    if (result == NULL) {
        return CALC_ERR_INVALID;
    }

    /* Overflow check using 64-bit arithmetic */
    int64_t tmp = (int64_t)a * (int64_t)b;
    if (tmp > INT32_MAX || tmp < INT32_MIN) {
        return CALC_ERR_OVERFLOW;
    }

    *result = (int32_t)tmp;
    return CALC_OK;
}

int calc_div(int32_t a, int32_t b, int32_t *result)
{
    if (result == NULL) {
        return CALC_ERR_INVALID;
    }

    if (b == 0) {
        return CALC_ERR_DIV_ZERO;
    }

    *result = a / b;
    return CALC_OK;
}

int calc_abs(int32_t a, int32_t *result)
{
    if (result == NULL) {
        return CALC_ERR_INVALID;
    }

    /* INT32_MIN has no positive representation in int32_t */
    if (a == INT32_MIN) {
        return CALC_ERR_OVERFLOW;
    }

    *result = (a < 0) ? -a : a;
    return CALC_OK;
}

int calc_sqrt(double x, double *result)
{
    if (result == NULL || x < 0.0) {
        return CALC_ERR_INVALID;
    }

    *result = sqrt(x);
    return CALC_OK;
}
