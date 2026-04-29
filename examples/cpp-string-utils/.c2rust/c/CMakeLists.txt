cmake_minimum_required(VERSION 3.10)
project(str_counter C)

set(CMAKE_C_STANDARD 11)

add_library(str_counter STATIC src/str_counter.c)
target_include_directories(str_counter PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)

add_executable(test_str_counter tests/test_str_counter.c)
target_link_libraries(test_str_counter str_counter)

enable_testing()
add_test(NAME str_counter_tests COMMAND test_str_counter)
