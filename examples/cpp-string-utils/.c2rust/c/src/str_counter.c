/* str_counter.c — C implementation of the string counter. */

#include "str_counter.h"
#include <stdlib.h>
#include <string.h>

#define INITIAL_BUCKETS 8

typedef struct entry {
    char   *word;
    size_t  count;
} entry_t;

struct str_counter {
    entry_t *entries;
    size_t   len;
    size_t   cap;
    size_t   total;
};

str_counter_t *str_counter_new(void) {
    str_counter_t *c = calloc(1, sizeof(str_counter_t));
    if (!c) return NULL;
    c->entries = calloc(INITIAL_BUCKETS, sizeof(entry_t));
    if (!c->entries) { free(c); return NULL; }
    c->cap = INITIAL_BUCKETS;
    return c;
}

void str_counter_free(str_counter_t *c) {
    if (!c) return;
    for (size_t i = 0; i < c->len; i++) free(c->entries[i].word);
    free(c->entries);
    free(c);
}

int str_counter_add(str_counter_t *c, const char *word) {
    if (!c || !word) return -1;
    /* Check for existing entry */
    for (size_t i = 0; i < c->len; i++) {
        if (strcmp(c->entries[i].word, word) == 0) {
            c->entries[i].count++;
            c->total++;
            return 0;
        }
    }
    /* Grow if needed */
    if (c->len == c->cap) {
        size_t new_cap = c->cap * 2;
        entry_t *tmp = realloc(c->entries, new_cap * sizeof(entry_t));
        if (!tmp) return -1;
        c->entries = tmp;
        c->cap = new_cap;
    }
    char *copy = strdup(word);
    if (!copy) return -1;
    c->entries[c->len].word  = copy;
    c->entries[c->len].count = 1;
    c->len++;
    c->total++;
    return 0;
}

size_t str_counter_get(const str_counter_t *c, const char *word) {
    if (!c || !word) return 0;
    for (size_t i = 0; i < c->len; i++)
        if (strcmp(c->entries[i].word, word) == 0)
            return c->entries[i].count;
    return 0;
}

size_t str_counter_total(const str_counter_t *c) {
    return c ? c->total : 0;
}
