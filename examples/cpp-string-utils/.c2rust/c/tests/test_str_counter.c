#include <stdio.h>
#include <assert.h>
#include "str_counter.h"

static int passed = 0, failed = 0;

#define CHECK(expr, name) do { \
    if (expr) { printf("  [PASS] %s\n", name); passed++; } \
    else { printf("  [FAIL] %s  (line %d)\n", name, __LINE__); failed++; } \
} while (0)

static void test_new_and_free(void) {
    str_counter_t *c = str_counter_new();
    CHECK(c != NULL,                  "new returns non-NULL");
    CHECK(str_counter_total(c) == 0,  "new counter has total 0");
    str_counter_free(c);
    str_counter_free(NULL);   /* must not crash */
    CHECK(1,                          "free(NULL) is safe");
}

static void test_add_and_get(void) {
    str_counter_t *c = str_counter_new();
    CHECK(str_counter_add(c, "hello") == 0,     "add hello");
    CHECK(str_counter_add(c, "world") == 0,     "add world");
    CHECK(str_counter_add(c, "hello") == 0,     "add hello again");
    CHECK(str_counter_get(c, "hello") == 2,     "hello count == 2");
    CHECK(str_counter_get(c, "world") == 1,     "world count == 1");
    CHECK(str_counter_get(c, "missing") == 0,   "missing count == 0");
    CHECK(str_counter_total(c) == 3,            "total == 3");
    str_counter_free(c);
}

static void test_growth(void) {
    str_counter_t *c = str_counter_new();
    char word[16];
    int ok = 1;
    for (int i = 0; i < 20; i++) {
        snprintf(word, sizeof(word), "word%d", i);
        if (str_counter_add(c, word) != 0) { ok = 0; break; }
    }
    CHECK(ok,                            "20 unique words added");
    CHECK(str_counter_total(c) == 20,    "total == 20");
    CHECK(str_counter_get(c, "word0")  == 1, "word0 count == 1");
    CHECK(str_counter_get(c, "word19") == 1, "word19 count == 1");
    str_counter_free(c);
}

static void test_null_safety(void) {
    CHECK(str_counter_add(NULL, "x") == -1,     "add to NULL counter");
    CHECK(str_counter_add((str_counter_t*)1, NULL) == -1, "add NULL word");
    CHECK(str_counter_get(NULL, "x") == 0,      "get from NULL counter");
    CHECK(str_counter_total(NULL) == 0,          "total of NULL counter");
}

int main(void) {
    printf("str_counter C test suite\n");
    printf("========================\n");
    test_new_and_free();
    test_add_and_get();
    test_growth();
    test_null_safety();
    printf("========================\n");
    if (failed == 0) {
        printf("All %d tests passed!\n", passed);
        return 0;
    } else {
        printf("%d passed, %d FAILED\n", passed, failed);
        return 1;
    }
}
