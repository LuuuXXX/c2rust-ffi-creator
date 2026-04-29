//! FFI 封装：pressure 模块
//! 原 C 头文件：include/sensor/pressure.h
//! 警告：此文件由 gen_rust_ffi.py 自动生成，并经人工审核补充了 #[repr(C)] 结构体定义与测试。

#![allow(non_camel_case_types, non_snake_case, dead_code, unused_imports)]

use std::ffi::{c_int, c_uint, c_long, c_char, c_void, c_float, c_double};

/// 对应 C 的 `pressure_reading_t`，内存布局与 C 端完全一致。
/// 经人工审核确认（替换了自动生成的不透明占位符）。
#[repr(C)]
pub struct PressureReadingT {
    /// 气压，单位 Pascal
    pub pascal: u32,
    /// 传感器 I2C 地址
    pub sensor_id: u8,
    /// 数据有效标志（1 = 有效）
    pub valid: u8,
}

mod sys {
    #[allow(unused_imports)]
    use super::*;
    extern "C" {
        #[link_name = "pressure_sensor_init"]
        pub(super) fn __c_pressure_sensor_init(addr: u8) -> c_int;
        #[link_name = "pressure_sensor_read"]
        pub(super) fn __c_pressure_sensor_read(addr: u8, out: *mut PressureReadingT) -> c_int;
        #[link_name = "pressure_sensor_shutdown"]
        pub(super) fn __c_pressure_sensor_shutdown(addr: u8);
    }
}

/// # Safety
/// 调用方须确保所有指针参数有效且生命周期覆盖本次调用。
pub unsafe extern "C" fn pressure_sensor_init(addr: u8) -> c_int {
    sys::__c_pressure_sensor_init(addr)
}

/// # Safety
/// 调用方须确保所有指针参数有效且生命周期覆盖本次调用。
pub unsafe extern "C" fn pressure_sensor_read(addr: u8, out: *mut PressureReadingT) -> c_int {
    sys::__c_pressure_sensor_read(addr, out)
}

/// # Safety
/// 调用方须确保所有指针参数有效且生命周期覆盖本次调用。
pub unsafe extern "C" fn pressure_sensor_shutdown(addr: u8) {
    sys::__c_pressure_sensor_shutdown(addr)
}

// ── Rust 测试（对应 C 测试文件 tests/test_pressure.c）───────────────────────
#[cfg(test)]
mod tests {
    use super::*;

    // 对应 C 测试 test_pressure_sensor_init
    //
    // 无 I2C 硬件时 init 返回 -1；有硬件时返回 0。
    #[test]
    fn test_pressure_sensor_init() {
        let ret = unsafe { pressure_sensor_init(0x77) };
        assert!(ret == 0 || ret == -1, "unexpected return value: {}", ret);
    }

    // 验证 read 在 i2c_read stub 下不崩溃
    #[test]
    fn test_pressure_sensor_read_stub() {
        unsafe {
            let _init_ret = pressure_sensor_init(0x77);
            let mut reading = PressureReadingT { pascal: 0, sensor_id: 0, valid: 0 };
            // i2c_read 是 stub（始终返回 0），read 应完成且返回 0
            let ret = pressure_sensor_read(0x77, &mut reading);
            assert_eq!(ret, 0);
            pressure_sensor_shutdown(0x77);
        }
    }
}
