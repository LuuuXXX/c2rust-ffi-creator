CC      = gcc
CFLAGS  = -Wall -Wextra -Iinclude
SRCDIR  = src
TESTDIR = tests

all: libstrbuf.a

libstrbuf.a: $(SRCDIR)/strbuf.o
	ar rcs $@ $^

$(SRCDIR)/%.o: $(SRCDIR)/%.c
	$(CC) $(CFLAGS) -c $< -o $@

test: tests/test_strbuf
	./tests/test_strbuf

tests/test_strbuf: $(TESTDIR)/test_strbuf.c $(SRCDIR)/strbuf.o
	$(CC) $(CFLAGS) $^ -o $@

clean:
	rm -f $(SRCDIR)/*.o libstrbuf.a tests/test_strbuf
