# Copyright 2014-present PlatformIO <contact@platformio.org>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Arduino

Arduino Wiring-based Framework allows writing cross-platform software to
control devices attached to a wide range of Arduino boards to create all
kinds of creative coding, interactive objects, spaces or physical experiences.

https://github.com/Air-duino/Arduino-AirMCU
"""

import json
import sys
from os.path import isfile, isdir, join

from SCons.Script import COMMAND_LINE_TARGETS, DefaultEnvironment

env = DefaultEnvironment()
platform = env.PioPlatform()
board_config = env.BoardConfig()

IS_WINDOWS = sys.platform.startswith("win")
FRAMEWORK_DIR = platform.get_package_dir("framework-arduinopy32")
CMSIS_DIR = join(platform.get_package_dir("framework-cmsis"), "CMSIS")
assert isdir(FRAMEWORK_DIR)
assert isdir(CMSIS_DIR)


mcu = board_config.get("build.mcu", "")
vdd = board_config.get("build.vdd", "")
# mcu_type = mcu[:-2]
if mcu == "PY32F002Axx":
    mcu_type = "Arduino-PY32F0xx"
elif mcu == "PY32F003xx":
    mcu_type = "Arduino-PY32F0xx"
elif mcu == "PY32F030xx":
    mcu_type = "Arduino-PY32F0xx"
variant = board_config.get(
    "build.variant", board_config.get("build.arduino.variant", "generic")
)
# series = mcu_type[:7].upper() + "xx"
if mcu == "PY32F002Axx":
    series = "PY32F0" + "xx"
    series_1 = series
    plt = series
elif mcu == "PY32F003xx":
    series = "PY32F0" + "xx"
    series_1 = series
    plt = series
elif mcu == "PY32F030xx":
    series = "PY32F0" + "xx"
    series_1 = series
    plt = series
variants_dir = (
    join("$PROJECT_DIR", board_config.get("build.variants_dir"))
    if board_config.get("build.variants_dir", "")
    else join(FRAMEWORK_DIR, "variants")
)
variant_dir = join(variants_dir, variant)
inc_variant_dir = variant_dir
if not IS_WINDOWS and not (
    set(["_idedata", "idedata"]) & set(COMMAND_LINE_TARGETS) and " " not in variant_dir
):
    inc_variant_dir = variant_dir.replace("(", r"\(").replace(")", r"\)")

upload_protocol = env.subst("$UPLOAD_PROTOCOL")


def process_standard_library_configuration(cpp_defines):
    if "PIO_FRAMEWORK_ARDUINO_STANDARD_LIB" in cpp_defines:
        env["LINKFLAGS"].remove("--specs=nano.specs")
    if "PIO_FRAMEWORK_ARDUINO_NANOLIB_FLOAT_PRINTF" in cpp_defines:
        env.Append(LINKFLAGS=["-u_printf_float"])
    if "PIO_FRAMEWORK_ARDUINO_NANOLIB_FLOAT_SCANF" in cpp_defines:
        env.Append(LINKFLAGS=["-u_scanf_float"])


def process_usart_configuration(cpp_defines):
    if "PIO_FRAMEWORK_ARDUINO_SERIAL_DISABLED" in cpp_defines:
        env["CPPDEFINES"].remove("HAL_UART_MODULE_ENABLED")

    elif "PIO_FRAMEWORK_ARDUINO_SERIAL_WITHOUT_GENERIC" in cpp_defines:
        env.Append(CPPDEFINES=["HWSERIAL_NONE"])


def process_usb_speed_configuration(cpp_defines):
    if "PIO_FRAMEWORK_ARDUINO_USB_HIGHSPEED" in cpp_defines:
        env.Append(CPPDEFINES=["USE_USB_HS"])

    elif "PIO_FRAMEWORK_ARDUINO_USB_HIGHSPEED_FULLMODE" in cpp_defines:
        env.Append(CPPDEFINES=["USE_USB_HS", "USE_USB_HS_IN_FS"])


def process_usb_configuration(cpp_defines):
    if "PIO_FRAMEWORK_ARDUINO_ENABLE_CDC" in cpp_defines:
        env.Append(CPPDEFINES=["USBD_USE_CDC"])

    elif "PIO_FRAMEWORK_ARDUINO_ENABLE_CDC_WITHOUT_SERIAL" in cpp_defines:
        env.Append(CPPDEFINES=["USBD_USE_CDC", "DISABLE_GENERIC_SERIALUSB"])

    elif "PIO_FRAMEWORK_ARDUINO_ENABLE_HID" in cpp_defines:
        env.Append(CPPDEFINES=["USBD_USE_HID_COMPOSITE"])

    if any(
        d in cpp_defines
        for d in (
            "PIO_FRAMEWORK_ARDUINO_ENABLE_CDC",
            "PIO_FRAMEWORK_ARDUINO_ENABLE_CDC_WITHOUT_SERIAL",
            "PIO_FRAMEWORK_ARDUINO_ENABLE_HID",
        )
    ):
        env.Append(
            CPPDEFINES=[
                "USBCON",
                ("USB_VID", board_config.get("build.hwids", [[0, 0]])[0][0]),
                ("USB_PID", board_config.get("build.hwids", [[0, 0]])[0][1]),
            ]
        )

    if any(f in env["CPPDEFINES"] for f in ("USBD_USE_CDC", "USBD_USE_HID_COMPOSITE")):
        env.Append(CPPDEFINES=["HAL_PCD_MODULE_ENABLED"])


def configure_application_offset(mcu, upload_protocol):
    offset = 0


    env.Append(
        CPPDEFINES=[
            # ("VECT_TAB_OFFSET", board_config.get("build.flash_offset", hex(offset)))
        ],
    )

    # LD_FLASH_OFFSET is mandatory even if there is no offset
    env.Append(
        LINKFLAGS=[
            "-Wl,--defsym=LD_FLASH_OFFSET=%s"
            % board_config.get("build.flash_offset", hex(offset))
        ]
    )


def load_boards_remap():
    remap_file = join(FRAMEWORK_DIR, "tools", "platformio", "boards_remap.json")
    if not isfile(remap_file):
        print("Warning! Couldn't find board remap file!")
        return {}

    with open(remap_file, "r") as fp:
        try:
            return json.load(fp)
        except:
            print("Warning! Failed to parse board remap file!")
            return {}


def get_arduino_board_id(board_config, mcu):
    # User-specified value
    if board_config.get("build.arduino.board", ""):
        return board_config.get("build.arduino.board")

    # Default boards
    boards_remap = load_boards_remap()
    board_id = env.subst("$BOARD")
    if board_id == "PY32F002Ax5" or board_id == "AIR001_DEV" or board_id == "AIR32F103CB" or board_id == "AIR401_DEV" :
        return board_id

    if board_id in boards_remap:
        return boards_remap[board_id]

    # Fall back to default cases according to MCU value for generic boards
    if board_id.lower().startswith("generic"):
        board_id = "GENERIC_"
        mcu = mcu.upper()
        if len(mcu) > 12:
            board_id += mcu[5:12] + "X"
        else:
            if len(mcu) > 10:
                board_id += mcu[5:11] + "TX"
            else:
                board_id += mcu
            print(
                "Warning! Couldn't generate proper internal board id from the `%s` MCU "
                "field! At least 12 symbols are required!" % mcu
            )

            print("Falling back to `%s`." % board_id)

    return board_id.upper()


board_id = get_arduino_board_id(board_config, mcu)
machine_flags = [
    "-mcpu=%s" % board_config.get("build.cpu"),
    "-mthumb",
]


env.Append(
    ASFLAGS=machine_flags,
    ASPPFLAGS=[
        "-x",
        "assembler-with-cpp",
    ],
    CFLAGS=["-std=gnu17"],
    CXXFLAGS=[
        "-std=gnu++17",
        "-fno-threadsafe-statics",
        "-fno-rtti",
        "-fno-exceptions",
        "-fno-use-cxa-atexit",
    ],
    CCFLAGS=machine_flags
    + [
        "-Os",  # optimize for size
        "-fsingle-precision-constant",
        "-ffunction-sections",  # place each function in its own section
        "-fdata-sections",
        "-nostdlib",
        "--param",
        "max-inline-insns-single=500",
    ],
    CPPDEFINES=[
        series,
        ("ARDUINO", 10607),
        "ARDUINO_ARCH_PY32",
        "NDEBUG",
        "ARDUINO_%s" % board_id,
        ("BOARD_NAME", '\\"%s\\"' % board_id),
        "HAL_UART_MODULE_ENABLED",
        "USE_FULL_LL_DRIVER",
        (
            "VARIANT_H",
            '\\"%s\\"'
            % board_config.get(
                "build.arduino.variant_h",
                "variant_generic.h"
                # "variant_%s.h"
                # % ("generic" if board_id.lower().startswith("generic") else board_id),
            ),
        ),
        # "AIR001",
        # "AIR001xx_HSE_24M_HCLK_48M",
        # "F_CPU=48000000",
        # "AIR001xx_LSC_LSI",
        # "VDD_3V3",
        # "AIR001_DEV",
        # plt,
        vdd,

    ],
    CPPPATH=[
        join(FRAMEWORK_DIR, "cores", "arduino", "avr"),
        join(FRAMEWORK_DIR, "cores", "arduino", "py32"),
        join(FRAMEWORK_DIR, "cores", "arduino", "py32", "LL"),
        join(FRAMEWORK_DIR, "cores", "arduino", "py32", "usb"),
        join(FRAMEWORK_DIR, "cores", "arduino", "py32", "usb", "hid"),
        join(FRAMEWORK_DIR, "cores", "arduino", "py32", "usb", "cdc"),
        join(FRAMEWORK_DIR, "system", mcu_type + "-Drivers", series_1 + "_HAL_Driver", "Inc"),
        join(FRAMEWORK_DIR, "system", mcu_type + "-Drivers", series_1 + "_HAL_Driver", "Src"),
        join(FRAMEWORK_DIR, "system", series),
        join(CMSIS_DIR, "Core", "Include"),
        join(
            FRAMEWORK_DIR,
            "system",
            mcu_type + "-Drivers",
            "CMSIS",
            "Device",
            series_1,
            "Include",
        ),
        join(
            FRAMEWORK_DIR,
            "system",
            mcu_type + "-Drivers",
            "CMSIS",
            "Device",
            series_1,
            "Source",
            "gcc",
        ),
        join(CMSIS_DIR, "DSP", "Include"),
        join(CMSIS_DIR, "DSP", "PrivateInclude"),
        join(FRAMEWORK_DIR, "cores", "arduino"),
    ],
    LINKFLAGS=machine_flags
    + [
        "-Os",
        "--specs=nano.specs",
        "-Wl,--gc-sections,--relax",
        "-Wl,--check-sections",
        "-Wl,--entry=Reset_Handler",
        "-Wl,--unresolved-symbols=report-all",
        "-Wl,--warn-common",
        "-Wl,--defsym=LD_MAX_SIZE=%d" % board_config.get("upload.maximum_size"),
        "-Wl,--defsym=LD_MAX_DATA_SIZE=%d"
        % board_config.get("upload.maximum_ram_size"),
        '-Wl,-Map="%s"' % join("${BUILD_DIR}", "${PROGNAME}.map"),
    ],
    LIBS=[
        "c",
        "m",
        "gcc",
        "stdc++",
    ],
)

env.ProcessFlags(board_config.get("build.framework_extra_flags.arduino", ""))

configure_application_offset(mcu, upload_protocol)

#
# Linker requires preprocessing with correct RAM|ROM sizes
#

if not board_config.get("build.ldscript", ""):
    env.Replace(LDSCRIPT_PATH=join(FRAMEWORK_DIR, "system", "ldscript.ld"))
    if not isfile(join(env.subst(variant_dir), "ldscript.ld")):
        print("Warning! Cannot find linker script for the current target!\n")
    env.Append(
        LINKFLAGS=[
            (
                "-Wl,--default-script",
                join(
                    inc_variant_dir,
                    board_config.get("build.arduino.ldscript", "ldscript.ld"),
                ),
            )
        ]
    )

#
# Process configuration flags
#

cpp_defines = env.Flatten(env.get("CPPDEFINES", []))

process_standard_library_configuration(cpp_defines)
process_usb_configuration(cpp_defines)
process_usb_speed_configuration(cpp_defines)
process_usart_configuration(cpp_defines)

env.Append(
    LIBSOURCE_DIRS=[
        # join(FRAMEWORK_DIR, "libraries", "__cores__", "arduino"),
        join(FRAMEWORK_DIR, "libraries"),
    ]
)

#
# Target: Build Core Library
#

libs = []

if "build.variant" in board_config:
    env.Append(CPPPATH=[inc_variant_dir], LIBPATH=[inc_variant_dir])
    env.BuildSources(join("$BUILD_DIR", "FrameworkArduinoVariant"), variant_dir)

libs.append(
    env.BuildLibrary(
        join("$BUILD_DIR", "FrameworkArduino"), join(FRAMEWORK_DIR, "cores", "arduino")
    )
)

env.BuildSources(
    join("$BUILD_DIR", "SrcWrapper"), join(FRAMEWORK_DIR, "libraries", "SrcWrapper")
)

env.Prepend(LIBS=libs)