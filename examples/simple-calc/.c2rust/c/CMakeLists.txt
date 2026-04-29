cmake_minimum_required(VERSION 3.10)
project(simple_calc C)

set(CMAKE_C_STANDARD 11)

# ── Library ──────────────────────────────────────────────────────────────────
add_library(calc STATIC calc.c)
target_include_directories(calc PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})

# ── Test executable ──────────────────────────────────────────────────────────
add_executable(test_calc tests/test_calc.c)
target_link_libraries(test_calc calc)

enable_testing()
add_test(NAME calc_tests COMMAND test_calc)
