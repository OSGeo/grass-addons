# adds a .cpp file as a test
# takes one parameter which is a filename without an extension
function(add_pops_test NAME)
    # a test is an executable
    add_executable("${NAME}" "${NAME}")

    # make the PoPS library a dependency
    target_link_libraries(${NAME} pops)

    # Enable compiler warnings
    target_compile_options(${NAME} PRIVATE
         $<$<OR:$<CXX_COMPILER_ID:Clang>,$<CXX_COMPILER_ID:AppleClang>,$<CXX_COMPILER_ID:GNU>>:
              -Wall -Wextra -pedantic>
         $<$<CXX_COMPILER_ID:MSVC>:
              /W4>)

    # register a test
    add_test(NAME "${NAME}" COMMAND ${NAME})
endfunction()

add_pops_test(test_date)
add_pops_test(test_deterministic)
add_pops_test(test_model)
#add_pops_test(test_mortality)
add_pops_test(test_raster)
add_pops_test(test_scheduling)
add_pops_test(test_simulation)
add_pops_test(test_spread_rate)
add_pops_test(test_statistics)
add_pops_test(test_treatments)
add_pops_test(test_quarantine)
