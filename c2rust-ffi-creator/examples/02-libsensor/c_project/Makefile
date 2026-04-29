CC      = gcc
CFLAGS  = -Wall -Wextra -Iinclude
SRCDIR  = src
TESTDIR = tests

SRCS    = $(SRCDIR)/sensor/temperature.c \
          $(SRCDIR)/sensor/pressure.c \
          $(SRCDIR)/platform/linux/i2c.c
OBJS    = $(SRCS:.c=.o)

all: libsensor.a

libsensor.a: $(OBJS)
	ar rcs $@ $^

$(SRCDIR)/%.o: $(SRCDIR)/%.c
	$(CC) $(CFLAGS) -c $< -o $@

test: tests/test_temperature tests/test_pressure
	./tests/test_temperature
	./tests/test_pressure

tests/test_temperature: $(TESTDIR)/test_temperature.c $(SRCDIR)/sensor/temperature.o $(SRCDIR)/platform/linux/i2c.o
	$(CC) $(CFLAGS) $^ -o $@

tests/test_pressure: $(TESTDIR)/test_pressure.c $(SRCDIR)/sensor/pressure.o $(SRCDIR)/platform/linux/i2c.o
	$(CC) $(CFLAGS) $^ -o $@

clean:
	find src -name '*.o' -delete
	rm -f libsensor.a tests/test_temperature tests/test_pressure
