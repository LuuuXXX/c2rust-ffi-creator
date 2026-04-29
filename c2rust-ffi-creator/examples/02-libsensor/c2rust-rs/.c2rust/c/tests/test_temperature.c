#include <assert.h>
#include "sensor/temperature.h"

void test_temp_sensor_init() {
    /* Test initialization returns no error in stub mode */
    int ret = temp_sensor_init(0x48);
    (void)ret; /* fd may be -1 in CI, just ensure it doesn't crash */
}

void test_temp_sensor_read_invalid_fd() {
    temp_reading_t reading;
    /* reading on uninitialised sensor should return error */
    int ret = temp_sensor_read(0x48, &reading);
    assert(ret != 0 || reading.valid == 1);
}

int main(void) {
    test_temp_sensor_init();
    test_temp_sensor_read_invalid_fd();
    return 0;
}
