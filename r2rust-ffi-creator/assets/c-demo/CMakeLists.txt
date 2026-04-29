cmake_minimum_required(VERSION 3.10)
project(calc VERSION 1.0.0 LANGUAGES C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

# Build the shared library
add_library(calc SHARED src/calc.c)
target_include_directories(calc PUBLIC include)
target_link_libraries(calc m)  # link libm for sqrt

# Also build the static library
add_library(calc_static STATIC src/calc.c)
set_target_properties(calc_static PROPERTIES OUTPUT_NAME calc)
target_include_directories(calc_static PUBLIC include)
target_link_libraries(calc_static m)

# Install headers
install(FILES include/calc.h DESTINATION include)
install(TARGETS calc calc_static
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
)

# Build tests
enable_testing()
add_executable(test_calc tests/test_calc.c)
target_include_directories(test_calc PRIVATE include)
target_link_libraries(test_calc calc m)

add_test(NAME calc_tests COMMAND test_calc)
