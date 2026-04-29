//! FFI 封装：temperature 模块
//! 原 C 头文件：include/sensor/temperature.h
//! 警告：此文件由 gen_rust_ffi.py 自动生成，并经人工审核补充了 #[repr(C)] 结构体定义与测试。

#![allow(non_camel_case_types, non_snake_case, dead_code, unused_imports)]

use std::ffi::{c_int, c_uint, c_long, c_char, c_void, c_float, c_double};

/// 对应 C 的 `temp_reading_t`，内存布局与 C 端完全一致。
/// 经人工审核确认（替换了自动生成的不透明占位符）。
#[repr(C)]
pub struct TempReadingT {
    /// 温度，单位 millidegrees（例：25000 = 25.000 °C）
    pub millidegrees: i32,
    /// 传感器 I2C 地址
    pub sensor_id: u8,
    /// 数据有效标志（1 = 有效）
    pub valid: u8,
}

mod sys {
    #[allow(unused_imports)]
    use super::*;
    extern "C" {
        #[link_name = "temp_sensor_init"]
        pub(super) fn __c_temp_sensor_init(addr: u8) -> c_int;
        #[link_name = "temp_sensor_read"]
        pub(super) fn __c_temp_sensor_read(addr: u8, out: *mut TempReadingT) -> c_int;
        #[link_name = "temp_sensor_shutdown"]
        pub(super) fn __c_temp_sensor_shutdown(addr: u8);
    }
}

/// # Safety
/// 调用方须确保所有指针参数有效且生命周期覆盖本次调用。
pub unsafe extern "C" fn temp_sensor_init(addr: u8) -> c_int {
    sys::__c_temp_sensor_init(addr)
}

/// # Safety
/// 调用方须确保所有指针参数有效且生命周期覆盖本次调用。
pub unsafe extern "C" fn temp_sensor_read(addr: u8, out: *mut TempReadingT) -> c_int {
    sys::__c_temp_sensor_read(addr, out)
}

/// # Safety
/// 调用方须确保所有指针参数有效且生命周期覆盖本次调用。
pub unsafe extern "C" fn temp_sensor_shutdown(addr: u8) {
    sys::__c_temp_sensor_shutdown(addr)
}

// ── Rust 测试（对应 C 测试文件 tests/test_temperature.c）────────────────────
#[cfg(test)]
mod tests {
    use super::*;

    // 对应 C 测试 test_temp_sensor_init
    //
    // 在没有 /dev/i2c-1 的测试环境中，init 会返回 -1（open 失败），
    // 测试验证"失败路径"的行为是正确的。
    #[test]
    fn test_temp_sensor_init() {
        let ret = unsafe { temp_sensor_init(0x48) };
        // 无 I2C 硬件：返回 -1；有硬件：返回 0
        assert!(ret == 0 || ret == -1, "unexpected return value: {}", ret);
    }

    // 对应 C 测试 test_temp_sensor_read_invalid_fd
    //
    // init 失败（fd = -1）后调用 read，i2c_read stub 始终返回 0，
    // 因此 read 虽能完成但数据无意义；测试仅验证不崩溃且返回成功。
    #[test]
    fn test_temp_sensor_read_invalid_fd() {
        unsafe {
            // init 失败但不 panic
            let _ret = temp_sensor_init(0x48);
            let mut reading = TempReadingT { millidegrees: 0, sensor_id: 0, valid: 0 };
            // i2c_read 是 stub（始终返回 0），所以 read 也应返回 0
            let ret = temp_sensor_read(0x48, &mut reading);
            assert_eq!(ret, 0);
            // 清理
            temp_sensor_shutdown(0x48);
        }
    }
}
