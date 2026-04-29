#ifndef SENSOR_PRESSURE_H
#define SENSOR_PRESSURE_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/** Pressure reading in Pascal. */
typedef struct {
    uint32_t pascal;
    uint8_t  sensor_id;
    uint8_t  valid;
} pressure_reading_t;

/** Initialize the pressure sensor at I2C address `addr`. Returns 0 on success. */
int pressure_sensor_init(uint8_t addr);

/** Read current pressure. Returns 0 on success, fills *out. */
int pressure_sensor_read(uint8_t addr, pressure_reading_t *out);

/** Shut down the sensor. */
void pressure_sensor_shutdown(uint8_t addr);

#ifdef __cplusplus
} /* extern "C" */
#endif

#endif /* SENSOR_PRESSURE_H */
