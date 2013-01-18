# CMAKE generated file: DO NOT EDIT!
# Generated by "Unix Makefiles" Generator, CMake Version 2.8

#=============================================================================
# Special targets provided by cmake.

# Disable implicit rules so canonical targets will work.
.SUFFIXES:

# Remove some rules from gmake that .SUFFIXES does not remove.
SUFFIXES =

.SUFFIXES: .hpux_make_needs_suffix_list

# Suppress display of executed commands.
$(VERBOSE).SILENT:

# A target that is always out of date.
cmake_force:
.PHONY : cmake_force

#=============================================================================
# Set environment variables for the build.

# The shell in which to execute make rules.
SHELL = /bin/sh

# The CMake executable.
CMAKE_COMMAND = /usr/bin/cmake

# The command to remove a file.
RM = /usr/bin/cmake -E remove -f

# Escaping for special characters.
EQUALS = =

# The top-level source directory on which CMake was run.
CMAKE_SOURCE_DIR = /home/pi/rabbitmq-c/tools

# The top-level build directory on which CMake was run.
CMAKE_BINARY_DIR = /home/pi/rabbitmq-c/bin-rabbitmq-c

# Include any dependencies generated for this target.
include CMakeFiles/amqp-get.dir/depend.make

# Include the progress variables for this target.
include CMakeFiles/amqp-get.dir/progress.make

# Include the compile flags for this target's objects.
include CMakeFiles/amqp-get.dir/flags.make

CMakeFiles/amqp-get.dir/get.o: CMakeFiles/amqp-get.dir/flags.make
CMakeFiles/amqp-get.dir/get.o: /home/pi/rabbitmq-c/tools/get.c
	$(CMAKE_COMMAND) -E cmake_progress_report /home/pi/rabbitmq-c/bin-rabbitmq-c/CMakeFiles $(CMAKE_PROGRESS_1)
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Building C object CMakeFiles/amqp-get.dir/get.o"
	/usr/bin/gcc  $(C_DEFINES) $(C_FLAGS) -o CMakeFiles/amqp-get.dir/get.o   -c /home/pi/rabbitmq-c/tools/get.c

CMakeFiles/amqp-get.dir/get.i: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Preprocessing C source to CMakeFiles/amqp-get.dir/get.i"
	/usr/bin/gcc  $(C_DEFINES) $(C_FLAGS) -E /home/pi/rabbitmq-c/tools/get.c > CMakeFiles/amqp-get.dir/get.i

CMakeFiles/amqp-get.dir/get.s: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Compiling C source to assembly CMakeFiles/amqp-get.dir/get.s"
	/usr/bin/gcc  $(C_DEFINES) $(C_FLAGS) -S /home/pi/rabbitmq-c/tools/get.c -o CMakeFiles/amqp-get.dir/get.s

CMakeFiles/amqp-get.dir/get.o.requires:
.PHONY : CMakeFiles/amqp-get.dir/get.o.requires

CMakeFiles/amqp-get.dir/get.o.provides: CMakeFiles/amqp-get.dir/get.o.requires
	$(MAKE) -f CMakeFiles/amqp-get.dir/build.make CMakeFiles/amqp-get.dir/get.o.provides.build
.PHONY : CMakeFiles/amqp-get.dir/get.o.provides

CMakeFiles/amqp-get.dir/get.o.provides.build: CMakeFiles/amqp-get.dir/get.o

CMakeFiles/amqp-get.dir/common.o: CMakeFiles/amqp-get.dir/flags.make
CMakeFiles/amqp-get.dir/common.o: /home/pi/rabbitmq-c/tools/common.c
	$(CMAKE_COMMAND) -E cmake_progress_report /home/pi/rabbitmq-c/bin-rabbitmq-c/CMakeFiles $(CMAKE_PROGRESS_2)
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Building C object CMakeFiles/amqp-get.dir/common.o"
	/usr/bin/gcc  $(C_DEFINES) $(C_FLAGS) -o CMakeFiles/amqp-get.dir/common.o   -c /home/pi/rabbitmq-c/tools/common.c

CMakeFiles/amqp-get.dir/common.i: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Preprocessing C source to CMakeFiles/amqp-get.dir/common.i"
	/usr/bin/gcc  $(C_DEFINES) $(C_FLAGS) -E /home/pi/rabbitmq-c/tools/common.c > CMakeFiles/amqp-get.dir/common.i

CMakeFiles/amqp-get.dir/common.s: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Compiling C source to assembly CMakeFiles/amqp-get.dir/common.s"
	/usr/bin/gcc  $(C_DEFINES) $(C_FLAGS) -S /home/pi/rabbitmq-c/tools/common.c -o CMakeFiles/amqp-get.dir/common.s

CMakeFiles/amqp-get.dir/common.o.requires:
.PHONY : CMakeFiles/amqp-get.dir/common.o.requires

CMakeFiles/amqp-get.dir/common.o.provides: CMakeFiles/amqp-get.dir/common.o.requires
	$(MAKE) -f CMakeFiles/amqp-get.dir/build.make CMakeFiles/amqp-get.dir/common.o.provides.build
.PHONY : CMakeFiles/amqp-get.dir/common.o.provides

CMakeFiles/amqp-get.dir/common.o.provides.build: CMakeFiles/amqp-get.dir/common.o

# Object files for target amqp-get
amqp__get_OBJECTS = \
"CMakeFiles/amqp-get.dir/get.o" \
"CMakeFiles/amqp-get.dir/common.o"

# External object files for target amqp-get
amqp__get_EXTERNAL_OBJECTS =

amqp-get: CMakeFiles/amqp-get.dir/get.o
amqp-get: CMakeFiles/amqp-get.dir/common.o
amqp-get: CMakeFiles/amqp-get.dir/build.make
amqp-get: CMakeFiles/amqp-get.dir/link.txt
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --red --bold "Linking C executable amqp-get"
	$(CMAKE_COMMAND) -E cmake_link_script CMakeFiles/amqp-get.dir/link.txt --verbose=$(VERBOSE)

# Rule to build all files generated by this target.
CMakeFiles/amqp-get.dir/build: amqp-get
.PHONY : CMakeFiles/amqp-get.dir/build

CMakeFiles/amqp-get.dir/requires: CMakeFiles/amqp-get.dir/get.o.requires
CMakeFiles/amqp-get.dir/requires: CMakeFiles/amqp-get.dir/common.o.requires
.PHONY : CMakeFiles/amqp-get.dir/requires

CMakeFiles/amqp-get.dir/clean:
	$(CMAKE_COMMAND) -P CMakeFiles/amqp-get.dir/cmake_clean.cmake
.PHONY : CMakeFiles/amqp-get.dir/clean

CMakeFiles/amqp-get.dir/depend:
	cd /home/pi/rabbitmq-c/bin-rabbitmq-c && $(CMAKE_COMMAND) -E cmake_depends "Unix Makefiles" /home/pi/rabbitmq-c/tools /home/pi/rabbitmq-c/tools /home/pi/rabbitmq-c/bin-rabbitmq-c /home/pi/rabbitmq-c/bin-rabbitmq-c /home/pi/rabbitmq-c/bin-rabbitmq-c/CMakeFiles/amqp-get.dir/DependInfo.cmake --color=$(COLOR)
.PHONY : CMakeFiles/amqp-get.dir/depend
