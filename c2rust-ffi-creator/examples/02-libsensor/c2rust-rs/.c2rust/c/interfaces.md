# 接口清单：c2rust-rs

生成时间：2026-04-29T07:39:17Z
来源：.c2rust/c/spec.json

## 模块：i2c

- **头文件**：`include/platform/linux/i2c.h`
- **源文件**：`src/platform/linux/i2c.c`

### 北向接口（对外 API）

| 函数 | 签名 | 返回值 |
|------|------|--------|
| `i2c_open` | `int i2c_open(const char *bus_path)` | `int` |
| `i2c_close` | `void i2c_close(int fd)` | `void` |
| `i2c_write` | `int i2c_write(int fd, uint8_t addr, const uint8_t *data, size_t len)` | `int` |
| `i2c_read` | `int i2c_read(int fd, uint8_t addr, uint8_t *buf, size_t len)` | `int` |

### 南向依赖

| 依赖 | 类型 |
|------|------|
| `platform` | external |

### 数据契约


### C 测试覆盖

（无测试或测试文件未检测到）

## 模块：pressure

- **头文件**：`include/sensor/pressure.h`
- **源文件**：`src/sensor/pressure.c`

### 北向接口（对外 API）

| 函数 | 签名 | 返回值 |
|------|------|--------|
| `pressure_sensor_init` | `int pressure_sensor_init(uint8_t addr)` | `int` |
| `pressure_sensor_read` | `int pressure_sensor_read(uint8_t addr, pressure_reading_t *out)` | `int` |
| `pressure_sensor_shutdown` | `void pressure_sensor_shutdown(uint8_t addr)` | `void` |

### 南向依赖

| 依赖 | 类型 |
|------|------|
| `i2c` | internal |
| `sensor` | external |

### 数据契约

```c
typedef struct {
    uint32_t pascal;
    uint8_t  sensor_id;
    uint8_t  valid;
} pressure_reading_t;
```

### C 测试覆盖

- `test_pressure_sensor_init`

## 模块：temperature

- **头文件**：`include/sensor/temperature.h`
- **源文件**：`src/sensor/temperature.c`

### 北向接口（对外 API）

| 函数 | 签名 | 返回值 |
|------|------|--------|
| `temp_sensor_init` | `int temp_sensor_init(uint8_t addr)` | `int` |
| `temp_sensor_read` | `int temp_sensor_read(uint8_t addr, temp_reading_t *out)` | `int` |
| `temp_sensor_shutdown` | `void temp_sensor_shutdown(uint8_t addr)` | `void` |

### 南向依赖

| 依赖 | 类型 |
|------|------|
| `i2c` | internal |
| `sensor` | external |

### 数据契约

```c
typedef struct {
    int32_t  millidegrees;  /**< e.g. 25000 = 25.000 °C */
    uint8_t  sensor_id;
    uint8_t  valid;
} temp_reading_t;
```

### C 测试覆盖

- `test_temp_sensor_init`
- `test_temp_sensor_read_invalid_fd`
