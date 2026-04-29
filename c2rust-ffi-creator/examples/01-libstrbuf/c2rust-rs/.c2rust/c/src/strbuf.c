#include <stdlib.h>
#include <string.h>
#include "strbuf.h"

int strbuf_init(strbuf_t *buf, size_t initial_cap) {
    buf->data = (char *)malloc(initial_cap + 1);
    if (!buf->data) return -1;
    buf->data[0] = '\0';
    buf->len = 0;
    buf->cap = initial_cap;
    return 0;
}

int strbuf_append(strbuf_t *buf, const char *str) {
    return strbuf_append_len(buf, str, strlen(str));
}

int strbuf_append_len(strbuf_t *buf, const char *data, size_t len) {
    if (buf->len + len >= buf->cap) {
        size_t new_cap = (buf->cap + len) * 2;
        char *new_data = (char *)realloc(buf->data, new_cap + 1);
        if (!new_data) return -1;
        buf->data = new_data;
        buf->cap = new_cap;
    }
    memcpy(buf->data + buf->len, data, len);
    buf->len += len;
    buf->data[buf->len] = '\0';
    return 0;
}

void strbuf_reset(strbuf_t *buf) {
    buf->len = 0;
    if (buf->data) buf->data[0] = '\0';
}

void strbuf_free(strbuf_t *buf) {
    free(buf->data);
    buf->data = NULL;
    buf->len = 0;
    buf->cap = 0;
}
