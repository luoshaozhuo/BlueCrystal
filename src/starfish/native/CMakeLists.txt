cmake_minimum_required(VERSION 3.16)

project(starfish_native C)

set(CMAKE_C_STANDARD 99)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS OFF)

# Output all binaries to bin/ subdirectory
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/bin")

# ── Third-party paths ─────────────────────────────────────────────────

set(THIRD_PARTY_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../../../third_party")
set(THIRD_PARTY_INSTALL "${THIRD_PARTY_ROOT}/install")

# ── open62541 ─────────────────────────────────────────────────────────

find_library(OPEN62541_LIBRARY open62541
    PATHS "${THIRD_PARTY_ROOT}/open62541/build/bin"
    NO_DEFAULT_PATH
)
find_path(OPEN62541_INCLUDE_DIR open62541/server.h
    PATHS "${THIRD_PARTY_ROOT}/open62541/build/src_generated"
          "${THIRD_PARTY_ROOT}/open62541/include"
          "${THIRD_PARTY_ROOT}/open62541/arch"
          "${THIRD_PARTY_ROOT}/open62541/plugins/include"
    NO_DEFAULT_PATH
)
if(OPEN62541_LIBRARY AND OPEN62541_INCLUDE_DIR)
    message(STATUS "open62541: FOUND (${OPEN62541_LIBRARY})")
    set(OPEN62541_FOUND TRUE)
    # open62541 needs its own build dir includes plus plugins, arch, and generated headers
    set(OPEN62541_INCLUDE_DIRS
        "${THIRD_PARTY_ROOT}/open62541/build/src_generated"
        "${THIRD_PARTY_ROOT}/open62541/include"
        "${THIRD_PARTY_ROOT}/open62541/arch"
        "${THIRD_PARTY_ROOT}/open62541/plugins/include"
        "${OPEN62541_INCLUDE_DIR}"
    )
    set(OPEN62541_LIBRARIES ${OPEN62541_LIBRARY} pthread)
else()
    message(STATUS "open62541: NOT FOUND — OPC UA targets will be skipped")
endif()

# ── libmodbus ─────────────────────────────────────────────────────────

find_library(MODBUS_LIBRARY modbus)
find_path(MODBUS_INCLUDE_DIR modbus/modbus.h)
if(MODBUS_LIBRARY AND MODBUS_INCLUDE_DIR)
    message(STATUS "libmodbus: FOUND (${MODBUS_LIBRARY})")
    set(MODBUS_FOUND TRUE)
    set(MODBUS_INCLUDE_DIRS ${MODBUS_INCLUDE_DIR})
    set(MODBUS_LIBRARIES ${MODBUS_LIBRARY})
else()
    message(STATUS "libmodbus: NOT FOUND — Modbus targets will be skipped")
endif()

# ── lib60870 ──────────────────────────────────────────────────────────

find_library(LIB60870_LIBRARY NAMES lib60870 liblib60870
    PATHS "${THIRD_PARTY_INSTALL}/lib"
    NO_DEFAULT_PATH
)
find_path(LIB60870_INCLUDE_DIR cs104_slave.h
    PATHS "${THIRD_PARTY_INSTALL}/include/lib60870"
    NO_DEFAULT_PATH
)
if(LIB60870_LIBRARY AND LIB60870_INCLUDE_DIR)
    message(STATUS "lib60870: FOUND (${LIB60870_LIBRARY})")
    set(LIB60870_FOUND TRUE)
    set(LIB60870_INCLUDE_DIRS "${THIRD_PARTY_INSTALL}/include")
    set(LIB60870_LIBRARIES ${LIB60870_LIBRARY} pthread)
else()
    message(STATUS "lib60870: NOT FOUND — IEC 60870 targets will be skipped")
endif()

# ── libiec61850 ───────────────────────────────────────────────────────

find_library(LIBIEC61850_LIBRARY iec61850
    PATHS "${THIRD_PARTY_INSTALL}/lib"
    NO_DEFAULT_PATH
)
find_library(HAL_LIBRARY hal
    PATHS "${THIRD_PARTY_INSTALL}/lib"
    NO_DEFAULT_PATH
)
find_path(LIBIEC61850_INCLUDE_DIR iec61850_server.h
    PATHS "${THIRD_PARTY_INSTALL}/include/libiec61850"
    NO_DEFAULT_PATH
)
if(LIBIEC61850_LIBRARY AND LIBIEC61850_INCLUDE_DIR)
    message(STATUS "libiec61850: FOUND (${LIBIEC61850_LIBRARY})")
    set(LIBIEC61850_FOUND TRUE)
    set(LIBIEC61850_INCLUDE_DIRS "${THIRD_PARTY_INSTALL}/include")
    if(HAL_LIBRARY)
        set(LIBIEC61850_LIBRARIES ${LIBIEC61850_LIBRARY} ${HAL_LIBRARY} pthread m)
    else()
        set(LIBIEC61850_LIBRARIES ${LIBIEC61850_LIBRARY} pthread m)
    endif()
else()
    message(STATUS "libiec61850: NOT FOUND — IEC 61850 targets will be skipped")
endif()

# ── open62541 targets ─────────────────────────────────────────────────

if(OPEN62541_FOUND)
    foreach(_target open62541_source_simulator open62541_client_runner open62541_subscription_runner)
        if(NOT TARGET ${_target})
            add_executable(${_target})
        endif()
    endforeach()

    set_target_properties(open62541_source_simulator PROPERTIES
        SOURCES open62541/open62541_simulator_server.c)
    target_include_directories(open62541_source_simulator PRIVATE ${OPEN62541_INCLUDE_DIRS})
    target_link_libraries(open62541_source_simulator PRIVATE ${OPEN62541_LIBRARIES})

    set_target_properties(open62541_client_runner PROPERTIES
        SOURCES open62541/open62541_client_runner.c)
    target_include_directories(open62541_client_runner PRIVATE ${OPEN62541_INCLUDE_DIRS})
    target_link_libraries(open62541_client_runner PRIVATE ${OPEN62541_LIBRARIES})

    set_target_properties(open62541_subscription_runner PROPERTIES
        SOURCES open62541/open62541_subscription_runner.c)
    target_include_directories(open62541_subscription_runner PRIVATE ${OPEN62541_INCLUDE_DIRS})
    target_link_libraries(open62541_subscription_runner PRIVATE ${OPEN62541_LIBRARIES})
else()
    message(STATUS "Skipping open62541 targets (dependency missing)")
endif()

# ── libmodbus targets ─────────────────────────────────────────────────

if(MODBUS_FOUND)
    add_executable(modbus_tcp_polling_runner
        libmodbus/modbus_tcp_polling_runner.c)
    target_include_directories(modbus_tcp_polling_runner PRIVATE ${MODBUS_INCLUDE_DIRS})
    target_link_libraries(modbus_tcp_polling_runner PRIVATE ${MODBUS_LIBRARIES})

    add_executable(modbus_rtu_polling_runner
        libmodbus/modbus_rtu_polling_runner.c)
    target_include_directories(modbus_rtu_polling_runner PRIVATE ${MODBUS_INCLUDE_DIRS})
    target_link_libraries(modbus_rtu_polling_runner PRIVATE ${MODBUS_LIBRARIES} m)

    add_executable(modbus_simulator_server
        libmodbus/modbus_simulator_server.c)
    target_include_directories(modbus_simulator_server PRIVATE ${MODBUS_INCLUDE_DIRS})
    target_link_libraries(modbus_simulator_server PRIVATE ${MODBUS_LIBRARIES} m)
else()
    message(STATUS "Skipping libmodbus targets (dependency missing)")
endif()

# ── lib60870 targets ──────────────────────────────────────────────────

if(LIB60870_FOUND)
    set(IEC60870_LIBS ${LIB60870_LIBRARIES})

    foreach(_target iec104_client_runner iec104_event_runner iec104_simulator_server
                      iec101_client_runner iec101_event_runner iec101_simulator_slave)
        if(NOT TARGET ${_target})
            add_executable(${_target})
        endif()
    endforeach()

    set_target_properties(iec104_client_runner PROPERTIES
        SOURCES lib60870/iec104_client_runner.c)
    target_include_directories(iec104_client_runner PRIVATE ${LIB60870_INCLUDE_DIRS})
    target_link_libraries(iec104_client_runner PRIVATE ${IEC60870_LIBS})

    set_target_properties(iec104_event_runner PROPERTIES
        SOURCES lib60870/iec104_event_runner.c)
    target_include_directories(iec104_event_runner PRIVATE ${LIB60870_INCLUDE_DIRS})
    target_link_libraries(iec104_event_runner PRIVATE ${IEC60870_LIBS})

    set_target_properties(iec104_simulator_server PROPERTIES
        SOURCES lib60870/iec104_simulator_server.c)
    target_include_directories(iec104_simulator_server PRIVATE ${LIB60870_INCLUDE_DIRS})
    target_link_libraries(iec104_simulator_server PRIVATE ${IEC60870_LIBS})

    set_target_properties(iec101_client_runner PROPERTIES
        SOURCES lib60870/iec101_client_runner.c)
    target_include_directories(iec101_client_runner PRIVATE ${LIB60870_INCLUDE_DIRS})
    target_link_libraries(iec101_client_runner PRIVATE ${IEC60870_LIBS})

    set_target_properties(iec101_event_runner PROPERTIES
        SOURCES lib60870/iec101_event_runner.c)
    target_include_directories(iec101_event_runner PRIVATE ${LIB60870_INCLUDE_DIRS})
    target_link_libraries(iec101_event_runner PRIVATE ${IEC60870_LIBS})

    set_target_properties(iec101_simulator_slave PROPERTIES
        SOURCES lib60870/iec101_simulator_slave.c)
    target_include_directories(iec101_simulator_slave PRIVATE ${LIB60870_INCLUDE_DIRS})
    target_link_libraries(iec101_simulator_slave PRIVATE ${IEC60870_LIBS})
else()
    message(STATUS "Skipping lib60870 targets (dependency missing)")
endif()

# ── libiec61850 targets ───────────────────────────────────────────────

if(LIBIEC61850_FOUND)
    set(IEC61850_LIBS ${LIBIEC61850_LIBRARIES})

    foreach(_target iec61850_mms_client_runner iec61850_report_runner
                      iec61850_goose_subscriber_runner iec61850_goose_publisher_simulator
                      iec61850_sv_subscriber_runner iec61850_sv_publisher_simulator
                      iec61850_simulator_server)
        if(NOT TARGET ${_target})
            add_executable(${_target})
        endif()
    endforeach()

    set_target_properties(iec61850_mms_client_runner PROPERTIES
        SOURCES libiec61850/iec61850_mms_client_runner.c)
    target_include_directories(iec61850_mms_client_runner PRIVATE ${LIBIEC61850_INCLUDE_DIRS})
    target_link_libraries(iec61850_mms_client_runner PRIVATE ${IEC61850_LIBS})

    set_target_properties(iec61850_report_runner PROPERTIES
        SOURCES libiec61850/iec61850_report_runner.c)
    target_include_directories(iec61850_report_runner PRIVATE ${LIBIEC61850_INCLUDE_DIRS})
    target_link_libraries(iec61850_report_runner PRIVATE ${IEC61850_LIBS})

    set_target_properties(iec61850_goose_subscriber_runner PROPERTIES
        SOURCES libiec61850/iec61850_goose_subscriber_runner.c)
    target_include_directories(iec61850_goose_subscriber_runner PRIVATE ${LIBIEC61850_INCLUDE_DIRS})
    target_link_libraries(iec61850_goose_subscriber_runner PRIVATE ${IEC61850_LIBS})

    set_target_properties(iec61850_goose_publisher_simulator PROPERTIES
        SOURCES libiec61850/iec61850_goose_publisher_simulator.c)
    target_include_directories(iec61850_goose_publisher_simulator PRIVATE ${LIBIEC61850_INCLUDE_DIRS})
    target_link_libraries(iec61850_goose_publisher_simulator PRIVATE ${IEC61850_LIBS})

    set_target_properties(iec61850_sv_subscriber_runner PROPERTIES
        SOURCES libiec61850/iec61850_sv_subscriber_runner.c)
    target_include_directories(iec61850_sv_subscriber_runner PRIVATE ${LIBIEC61850_INCLUDE_DIRS})
    target_link_libraries(iec61850_sv_subscriber_runner PRIVATE ${IEC61850_LIBS})

    set_target_properties(iec61850_sv_publisher_simulator PROPERTIES
        SOURCES libiec61850/iec61850_sv_publisher_simulator.c)
    target_include_directories(iec61850_sv_publisher_simulator PRIVATE ${LIBIEC61850_INCLUDE_DIRS})
    target_link_libraries(iec61850_sv_publisher_simulator PRIVATE ${IEC61850_LIBS})

    set_target_properties(iec61850_simulator_server PROPERTIES
        SOURCES libiec61850/iec61850_simulator_server.c)
    target_include_directories(iec61850_simulator_server PRIVATE ${LIBIEC61850_INCLUDE_DIRS})
    target_link_libraries(iec61850_simulator_server PRIVATE ${IEC61850_LIBS})
else()
    message(STATUS "Skipping libiec61850 targets (dependency missing)")
endif()

# ── Summary ───────────────────────────────────────────────────────────

message(STATUS "=== Starfish native build summary ===")
message(STATUS "open62541:   ${OPEN62541_FOUND}")
message(STATUS "libmodbus:   ${MODBUS_FOUND}")
message(STATUS "lib60870:    ${LIB60870_FOUND}")
message(STATUS "libiec61850: ${LIBIEC61850_FOUND}")
