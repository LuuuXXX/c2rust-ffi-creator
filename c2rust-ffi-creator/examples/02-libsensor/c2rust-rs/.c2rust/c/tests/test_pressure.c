#include <assert.h>
#include "sensor/pressure.h"

void test_pressure_sensor_init() {
    int ret = pressure_sensor_init(0x77);
    (void)ret;
}

int main(void) {
    test_pressure_sensor_init();
    return 0;
}
