#pragma once
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Opaque handle to a string counter.
 * Tracks the count of times each word has been added.
 */
typedef struct str_counter str_counter_t;

/**
 * str_counter_new — allocate a new, empty string counter.
 * Returns NULL on allocation failure.
 */
str_counter_t *str_counter_new(void);

/**
 * str_counter_free — release all memory owned by the counter.
 * May be called with NULL (no-op).
 */
void str_counter_free(str_counter_t *counter);

/**
 * str_counter_add — increment the count for the given word.
 * Returns 0 on success, -1 on allocation failure or NULL input.
 */
int str_counter_add(str_counter_t *counter, const char *word);

/**
 * str_counter_get — return the count for a word (0 if not present).
 */
size_t str_counter_get(const str_counter_t *counter, const char *word);

/**
 * str_counter_total — return the total number of words added (with repetition).
 */
size_t str_counter_total(const str_counter_t *counter);

#ifdef __cplusplus
}
#endif
