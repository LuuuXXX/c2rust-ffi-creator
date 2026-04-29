#include <stdio.h>
#include <stdint.h>
#include "calc.h"

static int passed = 0, failed = 0;

#define CHECK(expr, name) do { \
    if (expr) { printf("  [PASS] %s\n", name); passed++; } \
    else { printf("  [FAIL] %s  (line %d)\n", name, __LINE__); failed++; } \
} while (0)

static void test_add(void) {
    CHECK(calc_add(1, 2)             ==        3, "add basic:         1 + 2 == 3");
    CHECK(calc_add(1000000, 2000000) ==  3000000, "add large:         1M + 2M == 3M");
    CHECK(calc_add(-5, 3)            ==       -2, "add with negative: -5 + 3 == -2");
    CHECK(calc_add(-5, -3)           ==       -8, "add both negative: -5 + -3 == -8");
    CHECK(calc_add(0, 0)             ==        0, "add zeros:         0 + 0 == 0");
}

static void test_sub(void) {
    CHECK(calc_sub(10, 3)  ==  7, "sub basic:           10 - 3 == 7");
    CHECK(calc_sub(3, 10)  == -7, "sub negative result:  3 - 10 == -7");
    CHECK(calc_sub(0, 0)   ==  0, "sub zeros:            0 - 0 == 0");
    CHECK(calc_sub(-1, -1) ==  0, "sub equal negatives: -1 - -1 == 0");
}

static void test_mul(void) {
    CHECK(calc_mul(4, 5)    ==  20, "mul basic:         4 * 5 == 20");
    CHECK(calc_mul(999, 0)  ==   0, "mul by zero:       999 * 0 == 0");
    CHECK(calc_mul(-3, 4)   == -12, "mul negative:      -3 * 4 == -12");
    CHECK(calc_mul(-3, -4)  ==  12, "mul both negative: -3 * -4 == 12");
}

int main(void) {
    printf("simple-calc C test suite\n");
    printf("========================\n");
    test_add();
    test_sub();
    test_mul();
    printf("========================\n");
    if (failed == 0) {
        printf("All %d tests passed!\n", passed);
        return 0;
    } else {
        printf("%d passed, %d FAILED\n", passed, failed);
        return 1;
    }
}
