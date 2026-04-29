#include <fcntl.h>
#include <unistd.h>
#include "platform/linux/i2c.h"

int i2c_open(const char *bus_path) {
    return open(bus_path, O_RDWR);
}

void i2c_close(int fd) {
    if (fd >= 0) close(fd);
}

int i2c_write(int fd, uint8_t addr, const uint8_t *data, size_t len) {
    (void)fd; (void)addr; (void)data; (void)len;
    return 0; /* stub */
}

int i2c_read(int fd, uint8_t addr, uint8_t *buf, size_t len) {
    (void)fd; (void)addr; (void)buf; (void)len;
    return 0; /* stub */
}
