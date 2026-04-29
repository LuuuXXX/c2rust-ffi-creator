#include <stdlib.h>
#include <string.h>
#include "kv.h"

#define DEFAULT_CAPACITY 16

/* ── Internal types ─────────────────────────────────────────────────────── */

typedef struct kv_entry {
    char *key;
    char *value;
} kv_entry_t;

struct kv_store {
    kv_entry_t *entries;
    size_t      count;
    size_t      capacity;
};

/* ── Lifecycle ──────────────────────────────────────────────────────────── */

kv_store_t *kv_new(size_t initial_capacity) {
    if (initial_capacity == 0) initial_capacity = DEFAULT_CAPACITY;

    kv_store_t *store = (kv_store_t *)malloc(sizeof(kv_store_t));
    if (!store) return NULL;

    store->entries = (kv_entry_t *)calloc(initial_capacity, sizeof(kv_entry_t));
    if (!store->entries) { free(store); return NULL; }

    store->count    = 0;
    store->capacity = initial_capacity;
    return store;
}

void kv_destroy(kv_store_t *store) {
    if (!store) return;
    for (size_t i = 0; i < store->count; i++) {
        free(store->entries[i].key);
        free(store->entries[i].value);
    }
    free(store->entries);
    free(store);
}

/* ── Operations ─────────────────────────────────────────────────────────── */

kv_status_t kv_set(kv_store_t *store, const char *key, const char *value) {
    if (!store || !key || !value) return KV_ERR_INVALID;

    /* Update existing key */
    for (size_t i = 0; i < store->count; i++) {
        if (strcmp(store->entries[i].key, key) == 0) {
            char *new_val = strdup(value);
            if (!new_val) return KV_ERR_NO_MEMORY;
            free(store->entries[i].value);
            store->entries[i].value = new_val;
            return KV_OK;
        }
    }

    /* Grow backing array if needed */
    if (store->count >= store->capacity) {
        size_t new_cap = store->capacity * 2;
        kv_entry_t *new_entries =
            (kv_entry_t *)realloc(store->entries, new_cap * sizeof(kv_entry_t));
        if (!new_entries) return KV_ERR_NO_MEMORY;
        store->entries  = new_entries;
        store->capacity = new_cap;
    }

    /* Insert new entry */
    store->entries[store->count].key = strdup(key);
    if (!store->entries[store->count].key) return KV_ERR_NO_MEMORY;

    store->entries[store->count].value = strdup(value);
    if (!store->entries[store->count].value) {
        free(store->entries[store->count].key);
        return KV_ERR_NO_MEMORY;
    }

    store->count++;
    return KV_OK;
}

const char *kv_get(const kv_store_t *store, const char *key) {
    if (!store || !key) return NULL;
    for (size_t i = 0; i < store->count; i++) {
        if (strcmp(store->entries[i].key, key) == 0)
            return store->entries[i].value;
    }
    return NULL;
}

kv_status_t kv_delete(kv_store_t *store, const char *key) {
    if (!store || !key) return KV_ERR_INVALID;
    for (size_t i = 0; i < store->count; i++) {
        if (strcmp(store->entries[i].key, key) == 0) {
            free(store->entries[i].key);
            free(store->entries[i].value);
            memmove(&store->entries[i], &store->entries[i + 1],
                    (store->count - i - 1) * sizeof(kv_entry_t));
            store->count--;
            return KV_OK;
        }
    }
    return KV_ERR_NOT_FOUND;
}

size_t kv_count(const kv_store_t *store) {
    if (!store) return 0;
    return store->count;
}
