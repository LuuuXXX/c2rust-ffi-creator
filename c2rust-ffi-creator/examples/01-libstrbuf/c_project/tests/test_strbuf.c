#include <assert.h>
#include <string.h>
#include "strbuf.h"

void test_strbuf_init_success() {
    strbuf_t buf;
    assert(strbuf_init(&buf, 16) == 0);
    assert(buf.len == 0);
    assert(buf.cap == 16);
    strbuf_free(&buf);
}

void test_strbuf_append() {
    strbuf_t buf;
    strbuf_init(&buf, 8);
    assert(strbuf_append(&buf, "hello") == 0);
    assert(buf.len == 5);
    assert(strcmp(buf.data, "hello") == 0);
    strbuf_free(&buf);
}

void test_strbuf_append_grows() {
    strbuf_t buf;
    strbuf_init(&buf, 4);
    assert(strbuf_append(&buf, "hello world") == 0);
    assert(buf.len == 11);
    strbuf_free(&buf);
}

void test_strbuf_reset() {
    strbuf_t buf;
    strbuf_init(&buf, 16);
    strbuf_append(&buf, "hi");
    strbuf_reset(&buf);
    assert(buf.len == 0);
    assert(buf.data[0] == '\0');
    strbuf_free(&buf);
}

int main(void) {
    test_strbuf_init_success();
    test_strbuf_append();
    test_strbuf_append_grows();
    test_strbuf_reset();
    return 0;
}
