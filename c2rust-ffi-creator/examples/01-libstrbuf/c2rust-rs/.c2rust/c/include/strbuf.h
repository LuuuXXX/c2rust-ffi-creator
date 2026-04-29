#ifndef STRBUF_H
#define STRBUF_H

#include <stddef.h>

/**
 * A growable string buffer.
 */
typedef struct {
    char   *data;   /**< null-terminated character data */
    size_t  len;    /**< current length (bytes, excluding NUL) */
    size_t  cap;    /**< allocated capacity (bytes) */
} strbuf_t;

/** Initialize a strbuf with initial capacity. Returns 0 on success, -1 on OOM. */
int strbuf_init(strbuf_t *buf, size_t initial_cap);

/** Append a NUL-terminated string. Returns 0 on success, -1 on OOM. */
int strbuf_append(strbuf_t *buf, const char *str);

/** Append exactly len bytes from data. Returns 0 on success, -1 on OOM. */
int strbuf_append_len(strbuf_t *buf, const char *data, size_t len);

/** Reset the buffer length to zero without freeing memory. */
void strbuf_reset(strbuf_t *buf);

/** Free allocated memory and zero-out the struct. */
void strbuf_free(strbuf_t *buf);

#endif /* STRBUF_H */
