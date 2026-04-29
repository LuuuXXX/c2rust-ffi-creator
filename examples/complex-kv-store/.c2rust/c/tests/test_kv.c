#include <stdio.h>
#include <assert.h>
#include <string.h>
#include "kv.h"

static int passed = 0, failed = 0;

#define CHECK(expr, name) do { \
    if (expr) { printf("  [PASS] %s\n", name); passed++; } \
    else { printf("  [FAIL] %s  (line %d)\n", name, __LINE__); failed++; } \
} while (0)

static void test_new_and_destroy(void) {
    kv_store_t *kv = kv_new(0);
    CHECK(kv != NULL,          "kv_new returns non-NULL");
    CHECK(kv_count(kv) == 0,   "new store has count 0");
    kv_destroy(kv);
    kv_destroy(NULL);           /* must not crash */
    CHECK(1,                   "kv_destroy(NULL) is safe");
}

static void test_set_and_get(void) {
    kv_store_t *kv = kv_new(4);
    CHECK(kv_set(kv, "foo",   "bar")   == KV_OK, "set foo=bar");
    CHECK(kv_set(kv, "hello", "world") == KV_OK, "set hello=world");
    CHECK(kv_count(kv) == 2,                     "count == 2");
    CHECK(strcmp(kv_get(kv, "foo"),   "bar")   == 0, "get foo");
    CHECK(strcmp(kv_get(kv, "hello"), "world") == 0, "get hello");
    CHECK(kv_get(kv, "missing") == NULL,             "get missing => NULL");
    kv_destroy(kv);
}

static void test_update(void) {
    kv_store_t *kv = kv_new(0);
    kv_set(kv, "key", "v1");
    kv_set(kv, "key", "v2");
    CHECK(kv_count(kv) == 1,                       "update keeps count at 1");
    CHECK(strcmp(kv_get(kv, "key"), "v2") == 0,    "updated value returned");
    kv_destroy(kv);
}

static void test_delete(void) {
    kv_store_t *kv = kv_new(0);
    kv_set(kv, "a", "1");
    kv_set(kv, "b", "2");
    kv_set(kv, "c", "3");
    CHECK(kv_delete(kv, "b")   == KV_OK,          "delete b => OK");
    CHECK(kv_count(kv) == 2,                       "count == 2 after delete");
    CHECK(kv_get(kv, "b") == NULL,                 "b no longer found");
    CHECK(strcmp(kv_get(kv, "a"), "1") == 0,       "a still accessible");
    CHECK(strcmp(kv_get(kv, "c"), "3") == 0,       "c still accessible");
    CHECK(kv_delete(kv, "missing") == KV_ERR_NOT_FOUND, "delete missing => NOT_FOUND");
    kv_destroy(kv);
}

static void test_null_safety(void) {
    kv_store_t *kv = kv_new(0);
    CHECK(kv_set(NULL, "k", "v")  == KV_ERR_INVALID, "set to NULL store");
    CHECK(kv_set(kv, NULL,  "v")  == KV_ERR_INVALID, "set NULL key");
    CHECK(kv_set(kv, "k",  NULL)  == KV_ERR_INVALID, "set NULL value");
    CHECK(kv_get(NULL, "k") == NULL,                  "get from NULL store");
    CHECK(kv_count(NULL) == 0,                        "count of NULL store");
    kv_destroy(kv);
}

static void test_growth(void) {
    kv_store_t *kv = kv_new(2);
    char key[16], val[16];
    int ok = 1;
    for (int i = 0; i < 20; i++) {
        snprintf(key, sizeof(key), "key%d", i);
        snprintf(val, sizeof(val), "val%d", i);
        if (kv_set(kv, key, val) != KV_OK) { ok = 0; break; }
    }
    CHECK(ok, "20 inserts succeed (triggers realloc)");
    CHECK(kv_count(kv) == 20, "count == 20 after growth");
    /* Spot-check a few values */
    CHECK(strcmp(kv_get(kv, "key0"),  "val0")  == 0, "key0  correct");
    CHECK(strcmp(kv_get(kv, "key19"), "val19") == 0, "key19 correct");
    kv_destroy(kv);
}

int main(void) {
    printf("kv_store C test suite\n");
    printf("=====================\n");
    test_new_and_destroy();
    test_set_and_get();
    test_update();
    test_delete();
    test_null_safety();
    test_growth();
    printf("=====================\n");
    if (failed == 0) {
        printf("All %d tests passed!\n", passed);
        return 0;
    } else {
        printf("%d passed, %d FAILED\n", passed, failed);
        return 1;
    }
}
