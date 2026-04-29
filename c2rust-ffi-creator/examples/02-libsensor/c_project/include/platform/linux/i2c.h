#ifndef PLATFORM_LINUX_I2C_H
#define PLATFORM_LINUX_I2C_H

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/** Open the I2C bus at `bus_path` (e.g. "/dev/i2c-1"). Returns fd or -1. */
int i2c_open(const char *bus_path);

/** Close an I2C file descriptor. */
void i2c_close(int fd);

/** Write `len` bytes to device at `addr`. Returns 0 on success. */
int i2c_write(int fd, uint8_t addr, const uint8_t *data, size_t len);

/** Read `len` bytes from device at `addr`. Returns 0 on success. */
int i2c_read(int fd, uint8_t addr, uint8_t *buf, size_t len);

#ifdef __cplusplus
} /* extern "C" */
#endif

#endif /* PLATFORM_LINUX_I2C_H */
