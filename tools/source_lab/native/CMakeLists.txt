cmake_minimum_required(VERSION 3.16)

project(source_lab_native C)

set(CMAKE_C_STANDARD 99)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)

# ── External dependency detection ─────────────────────────────────────

# open62541 (via CMake config)
find_package(open62541 QUIET)
if(NOT open62541_FOUND)
    message(STATUS "open62541: NOT FOUND — OPC UA targets will be skipped")
endif()

# libmodbus
find_library(MODBUS_LIBRARY modbus)
find_path(MODBUS_INCLUDE_DIR modbus/modbus.h)
if(MODBUS_LIBRARY AND MODBUS_INCLUDE_DIR)
    message(STATUS "libmodbus: FOUND (${MODBUS_LIBRARY})")
    set(MODBUS_FOUND TRUE)
else()
    message(STATUS "libmodbus: NOT FOUND — Modbus targets will be skipped")
endif()

# lib60870
find_library(LIB60870_LIBRARY NAMES lib60870 iec60870)
find_path(LIB60870_INCLUDE_DIR lib60870/cs104_connection.h
    PATHS /usr/local/include /usr/include /home/luosh/Whale/third_party/install/include)
if(LIB60870_LIBRARY AND LIB60870_INCLUDE_DIR)
    message(STATUS "lib60870: FOUND (${LIB60870_LIBRARY})")
    set(LIB60870_FOUND TRUE)
else()
    message(STATUS "lib60870: NOT FOUND — IEC 60870 targets will be skipped")
endif()

# libiec61850
find_library(LIBIEC61850_LIBRARY NAMES iec61850 libiec61850)
find_library(HAL_LIBRARY hal)
find_path(LIBIEC61850_INCLUDE_DIR libiec61850/iec61850_client.h
    PATHS /usr/local/include /usr/include /home/luosh/Whale/third_party/install/include)
if(LIBIEC61850_LIBRARY AND LIBIEC61850_INCLUDE_DIR)
    message(STATUS "libiec61850: FOUND (${LIBIEC61850_LIBRARY})")
    set(LIBIEC61850_FOUND TRUE)
else()
    message(STATUS "libiec61850: NOT FOUND — IEC 61850 targets will be skipped")
endif()

# ── Helper: add_executable with dependency guard ──────────────────────

function(add_native_target name source libs)
    if(NOT add_executable_guard_${name})
        add_executable(${name} ${source})
        target_link_libraries(${name} PRIVATE ${libs})
        set(add_executable_guard_${name} TRUE PARENT_SCOPE)
    endif()
endfunction()

# ── open62541 targets ────────────────────────────────────────────────

if(open62541_FOUND)
    add_executable(open62541_source_simulator
        open62541/open62541_simulator_server.c
    )
    target_link_libraries(open62541_source_simulator PRIVATE open62541::open62541)

    add_executable(open62541_client_runner
        open62541/open62541_client_runner.c
    )
    target_link_libraries(open62541_client_runner PRIVATE open62541::open62541)

    add_executable(open62541_subscription_runner
        open62541/open62541_subscription_runner.c
    )
    target_link_libraries(open62541_subscription_runner PRIVATE open62541::open62541)
else()
    message(STATUS "Skipping open62541 targets (dependency missing)")
endif()

# ── libmodbus targets ────────────────────────────────────────────────

if(MODBUS_FOUND)
    add_executable(modbus_tcp_polling_runner
        libmodbus/modbus_tcp_polling_runner.c
    )
    target_include_directories(modbus_tcp_polling_runner PRIVATE ${MODBUS_INCLUDE_DIR})
    target_link_libraries(modbus_tcp_polling_runner PRIVATE ${MODBUS_LIBRARY})

    add_executable(modbus_rtu_polling_runner
        libmodbus/modbus_rtu_polling_runner.c
    )
    target_include_directories(modbus_rtu_polling_runner PRIVATE ${MODBUS_INCLUDE_DIR})
    target_link_libraries(modbus_rtu_polling_runner PRIVATE ${MODBUS_LIBRARY} m)

    add_executable(modbus_simulator_server
        libmodbus/modbus_simulator_server.c
    )
    target_include_directories(modbus_simulator_server PRIVATE ${MODBUS_INCLUDE_DIR})
    target_link_libraries(modbus_simulator_server PRIVATE ${MODBUS_LIBRARY} m)
else()
    message(STATUS "Skipping libmodbus targets (dependency missing)")
endif()

# ── lib60870 targets ─────────────────────────────────────────────────

if(LIB60870_FOUND)
    set(IEC60870_LIBS ${LIB60870_LIBRARY} pthread)

    add_executable(iec104_client_runner
        lib60870/iec104_client_runner.c
    )
    target_include_directories(iec104_client_runner PRIVATE ${LIB60870_INCLUDE_DIR})
    target_link_libraries(iec104_client_runner PRIVATE ${IEC60870_LIBS})

    add_executable(iec104_event_runner
        lib60870/iec104_event_runner.c
    )
    target_include_directories(iec104_event_runner PRIVATE ${LIB60870_INCLUDE_DIR})
    target_link_libraries(iec104_event_runner PRIVATE ${IEC60870_LIBS})

    add_executable(iec104_simulator_server
        lib60870/iec104_simulator_server.c
    )
    target_include_directories(iec104_simulator_server PRIVATE ${LIB60870_INCLUDE_DIR})
    target_link_libraries(iec104_simulator_server PRIVATE ${IEC60870_LIBS})

    add_executable(iec101_client_runner
        lib60870/iec101_client_runner.c
    )
    target_include_directories(iec101_client_runner PRIVATE ${LIB60870_INCLUDE_DIR})
    target_link_libraries(iec101_client_runner PRIVATE ${IEC60870_LIBS})

    add_executable(iec101_event_runner
        lib60870/iec101_event_runner.c
    )
    target_include_directories(iec101_event_runner PRIVATE ${LIB60870_INCLUDE_DIR})
    target_link_libraries(iec101_event_runner PRIVATE ${IEC60870_LIBS})

    add_executable(iec101_simulator_slave
        lib60870/iec101_simulator_slave.c
    )
    target_include_directories(iec101_simulator_slave PRIVATE ${LIB60870_INCLUDE_DIR})
    target_link_libraries(iec101_simulator_slave PRIVATE ${IEC60870_LIBS})
else()
    message(STATUS "Skipping lib60870 targets (dependency missing)")
endif()

# ── libiec61850 targets ──────────────────────────────────────────────

if(LIBIEC61850_FOUND)
    set(IEC61850_LIBS ${LIBIEC61850_LIBRARY} ${HAL_LIBRARY} pthread m)

    add_executable(iec61850_mms_client_runner
        libiec61850/iec61850_mms_client_runner.c
    )
    target_include_directories(iec61850_mms_client_runner PRIVATE ${LIBIEC61850_INCLUDE_DIR})
    target_link_libraries(iec61850_mms_client_runner PRIVATE ${IEC61850_LIBS})

    add_executable(iec61850_report_runner
        libiec61850/iec61850_report_runner.c
    )
    target_include_directories(iec61850_report_runner PRIVATE ${LIBIEC61850_INCLUDE_DIR})
    target_link_libraries(iec61850_report_runner PRIVATE ${IEC61850_LIBS})

    add_executable(iec61850_goose_subscriber_runner
        libiec61850/iec61850_goose_subscriber_runner.c
    )
    target_include_directories(iec61850_goose_subscriber_runner PRIVATE ${LIBIEC61850_INCLUDE_DIR})
    target_link_libraries(iec61850_goose_subscriber_runner PRIVATE ${IEC61850_LIBS})

    add_executable(iec61850_goose_publisher_simulator
        libiec61850/iec61850_goose_publisher_simulator.c
    )
    target_include_directories(iec61850_goose_publisher_simulator PRIVATE ${LIBIEC61850_INCLUDE_DIR})
    target_link_libraries(iec61850_goose_publisher_simulator PRIVATE ${IEC61850_LIBS})

    add_executable(iec61850_sv_subscriber_runner
        libiec61850/iec61850_sv_subscriber_runner.c
    )
    target_include_directories(iec61850_sv_subscriber_runner PRIVATE ${LIBIEC61850_INCLUDE_DIR})
    target_link_libraries(iec61850_sv_subscriber_runner PRIVATE ${IEC61850_LIBS})

    add_executable(iec61850_sv_publisher_simulator
        libiec61850/iec61850_sv_publisher_simulator.c
    )
    target_include_directories(iec61850_sv_publisher_simulator PRIVATE ${LIBIEC61850_INCLUDE_DIR})
    target_link_libraries(iec61850_sv_publisher_simulator PRIVATE ${IEC61850_LIBS})

    add_executable(iec61850_simulator_server
        libiec61850/iec61850_simulator_server.c
    )
    target_include_directories(iec61850_simulator_server PRIVATE ${LIBIEC61850_INCLUDE_DIR})
    target_link_libraries(iec61850_simulator_server PRIVATE ${IEC61850_LIBS})
else()
    message(STATUS "Skipping libiec61850 targets (dependency missing)")
endif()

# ── Summary ──────────────────────────────────────────────────────────

message(STATUS "=== Native build summary ===")
message(STATUS "open62541:     ${open62541_FOUND}")
message(STATUS "libmodbus:     ${MODBUS_FOUND}")
message(STATUS "lib60870:      ${LIB60870_FOUND}")
message(STATUS "libiec61850:   ${LIBIEC61850_FOUND}")
