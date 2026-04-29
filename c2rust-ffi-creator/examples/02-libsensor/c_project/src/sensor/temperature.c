#include <string.h>
#include "sensor/temperature.h"
#include "platform/linux/i2c.h"

static int g_fd = -1;

int temp_sensor_init(uint8_t addr) {
    (void)addr;
    g_fd = i2c_open("/dev/i2c-1");
    return g_fd >= 0 ? 0 : -1;
}

int temp_sensor_read(uint8_t addr, temp_reading_t *out) {
    uint8_t raw[2];
    if (i2c_read(g_fd, addr, raw, 2) != 0) return -1;
    out->millidegrees = ((int32_t)(raw[0] << 8 | raw[1])) * 1000 / 256;
    out->sensor_id = addr;
    out->valid = 1;
    return 0;
}

void temp_sensor_shutdown(uint8_t addr) {
    (void)addr;
    i2c_close(g_fd);
    g_fd = -1;
}
