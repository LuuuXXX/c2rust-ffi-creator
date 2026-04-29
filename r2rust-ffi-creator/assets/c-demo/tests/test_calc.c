/**
 * test_calc.c - Tests for the calculator library
 */

#include <stdio.h>
#include <assert.h>
#include <stdint.h>
#include "calc.h"

#define TEST(name) static void test_##name(void)
#define RUN_TEST(name) do { printf("  [TEST] %s ... ", #name); test_##name(); printf("PASS\n"); } while(0)

/* ---------------------------------------------------------------- */
TEST(version)
{
    const char *v = calc_version();
    assert(v != NULL);
    assert(v[0] != '\0');
}

TEST(add_basic)
{
    int32_t result;
    assert(calc_add(2, 3, &result) == CALC_OK);
    assert(result == 5);
}

TEST(add_negative)
{
    int32_t result;
    assert(calc_add(-10, 4, &result) == CALC_OK);
    assert(result == -6);
}

TEST(add_overflow)
{
    int32_t result;
    assert(calc_add(INT32_MAX, 1, &result) == CALC_ERR_OVERFLOW);
}

TEST(add_null)
{
    assert(calc_add(1, 2, NULL) == CALC_ERR_INVALID);
}

TEST(sub_basic)
{
    int32_t result;
    assert(calc_sub(10, 3, &result) == CALC_OK);
    assert(result == 7);
}

TEST(sub_overflow)
{
    int32_t result;
    assert(calc_sub(INT32_MIN, 1, &result) == CALC_ERR_OVERFLOW);
}

TEST(mul_basic)
{
    int32_t result;
    assert(calc_mul(6, 7, &result) == CALC_OK);
    assert(result == 42);
}

TEST(mul_overflow)
{
    int32_t result;
    assert(calc_mul(INT32_MAX, 2, &result) == CALC_ERR_OVERFLOW);
}

TEST(div_basic)
{
    int32_t result;
    assert(calc_div(10, 3, &result) == CALC_OK);
    assert(result == 3);  /* integer division, truncation toward zero */
}

TEST(div_by_zero)
{
    int32_t result;
    assert(calc_div(5, 0, &result) == CALC_ERR_DIV_ZERO);
}

TEST(abs_positive)
{
    int32_t result;
    assert(calc_abs(42, &result) == CALC_OK);
    assert(result == 42);
}

TEST(abs_negative)
{
    int32_t result;
    assert(calc_abs(-42, &result) == CALC_OK);
    assert(result == 42);
}

TEST(abs_zero)
{
    int32_t result;
    assert(calc_abs(0, &result) == CALC_OK);
    assert(result == 0);
}

TEST(abs_overflow)
{
    int32_t result;
    assert(calc_abs(INT32_MIN, &result) == CALC_ERR_OVERFLOW);
}

TEST(sqrt_basic)
{
    double result;
    assert(calc_sqrt(9.0, &result) == CALC_OK);
    assert(result >= 2.999 && result <= 3.001);
}

TEST(sqrt_zero)
{
    double result;
    assert(calc_sqrt(0.0, &result) == CALC_OK);
    assert(result == 0.0);
}

TEST(sqrt_negative)
{
    double result;
    assert(calc_sqrt(-1.0, &result) == CALC_ERR_INVALID);
}

TEST(sqrt_null)
{
    assert(calc_sqrt(4.0, NULL) == CALC_ERR_INVALID);
}

/* ---------------------------------------------------------------- */

int main(void)
{
    printf("calc library test suite\n");
    printf("========================\n");

    RUN_TEST(version);
    RUN_TEST(add_basic);
    RUN_TEST(add_negative);
    RUN_TEST(add_overflow);
    RUN_TEST(add_null);
    RUN_TEST(sub_basic);
    RUN_TEST(sub_overflow);
    RUN_TEST(mul_basic);
    RUN_TEST(mul_overflow);
    RUN_TEST(div_basic);
    RUN_TEST(div_by_zero);
    RUN_TEST(abs_positive);
    RUN_TEST(abs_negative);
    RUN_TEST(abs_zero);
    RUN_TEST(abs_overflow);
    RUN_TEST(sqrt_basic);
    RUN_TEST(sqrt_zero);
    RUN_TEST(sqrt_negative);
    RUN_TEST(sqrt_null);

    printf("========================\n");
    printf("All tests passed!\n");
    return 0;
}
