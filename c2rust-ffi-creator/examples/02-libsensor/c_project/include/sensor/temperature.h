#ifndef SENSOR_TEMPERATURE_H
#define SENSOR_TEMPERATURE_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/** Temperature reading in millidegrees Celsius. */
typedef struct {
    int32_t  millidegrees;  /**< e.g. 25000 = 25.000 °C */
    uint8_t  sensor_id;
    uint8_t  valid;
} temp_reading_t;

/** Initialize the temperature sensor at I2C address `addr`. Returns 0 on success. */
int temp_sensor_init(uint8_t addr);

/** Read current temperature. Returns 0 on success, fills *out. */
int temp_sensor_read(uint8_t addr, temp_reading_t *out);

/** Shut down the sensor. */
void temp_sensor_shutdown(uint8_t addr);

#ifdef __cplusplus
} /* extern "C" */
#endif

#endif /* SENSOR_TEMPERATURE_H */
