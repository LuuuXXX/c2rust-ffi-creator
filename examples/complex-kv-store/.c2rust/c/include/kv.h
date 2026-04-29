#pragma once
#include <stddef.h>
#include <stdint.h>

/**
 * Status codes returned by KV store operations.
 */
typedef enum kv_status {
    KV_OK             =  0,  /**< Success */
    KV_ERR_NOT_FOUND  = -1,  /**< Key does not exist */
    KV_ERR_NO_MEMORY  = -2,  /**< malloc/realloc/strdup failed */
    KV_ERR_INVALID    = -3,  /**< NULL store, key, or value pointer */
} kv_status_t;

/**
 * Opaque handle to an in-memory key-value store.
 * Callers must treat this as an opaque pointer; the internal layout is an
 * implementation detail of kv.c.
 */
typedef struct kv_store kv_store_t;

/**
 * kv_new — allocate a new, empty KV store.
 *
 * @param initial_capacity  Hint for pre-allocation; pass 0 for the default (16).
 * @return  Pointer to a new store, or NULL on allocation failure.
 */
kv_store_t *kv_new(size_t initial_capacity);

/**
 * kv_destroy — free all memory owned by the store.
 *
 * @param store  May be NULL (no-op).
 */
void kv_destroy(kv_store_t *store);

/**
 * kv_set — insert or update a key-value pair.
 *
 * The store copies both @key and @value; the caller may free them afterwards.
 *
 * @return KV_OK, KV_ERR_NO_MEMORY, or KV_ERR_INVALID.
 */
kv_status_t kv_set(kv_store_t *store, const char *key, const char *value);

/**
 * kv_get — retrieve the value associated with @key.
 *
 * The returned pointer is owned by the store and is valid until the key is
 * updated, deleted, or the store is destroyed.
 *
 * @return Pointer to the value string, or NULL if the key is not present.
 */
const char *kv_get(const kv_store_t *store, const char *key);

/**
 * kv_delete — remove a key-value pair from the store.
 *
 * @return KV_OK, KV_ERR_NOT_FOUND, or KV_ERR_INVALID.
 */
kv_status_t kv_delete(kv_store_t *store, const char *key);

/**
 * kv_count — number of entries currently in the store.
 *
 * @param store  May be NULL (returns 0).
 */
size_t kv_count(const kv_store_t *store);
