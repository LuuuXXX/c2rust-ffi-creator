cmake_minimum_required(VERSION 3.10)
project(kv_store C)

set(CMAKE_C_STANDARD 11)

# ── Library ──────────────────────────────────────────────────────────────────
add_library(kv STATIC src/kv.c)
target_include_directories(kv PUBLIC include)

# ── Test executable ──────────────────────────────────────────────────────────
add_executable(test_kv tests/test_kv.c)
target_link_libraries(test_kv kv)

enable_testing()
add_test(NAME kv_tests COMMAND test_kv)
