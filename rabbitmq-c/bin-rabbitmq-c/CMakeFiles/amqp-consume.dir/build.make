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
include CMakeFiles/amqp-consume.dir/depend.make

# Include the progress variables for this target.
include CMakeFiles/amqp-consume.dir/progress.make

# Include the compile flags for this target's objects.
include CMakeFiles/amqp-consume.dir/flags.make

CMakeFiles/amqp-consume.dir/consume.o: CMakeFiles/amqp-consume.dir/flags.make
CMakeFiles/amqp-consume.dir/consume.o: /home/pi/rabbitmq-c/tools/consume.c
	$(CMAKE_COMMAND) -E cmake_progress_report /home/pi/rabbitmq-c/bin-rabbitmq-c/CMakeFiles $(CMAKE_PROGRESS_1)
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Building C object CMakeFiles/amqp-consume.dir/consume.o"
	/usr/bin/gcc  $(C_DEFINES) $(C_FLAGS) -o CMakeFiles/amqp-consume.dir/consume.o   -c /home/pi/rabbitmq-c/tools/consume.c

CMakeFiles/amqp-consume.dir/consume.i: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Preprocessing C source to CMakeFiles/amqp-consume.dir/consume.i"
	/usr/bin/gcc  $(C_DEFINES) $(C_FLAGS) -E /home/pi/rabbitmq-c/tools/consume.c > CMakeFiles/amqp-consume.dir/consume.i

CMakeFiles/amqp-consume.dir/consume.s: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Compiling C source to assembly CMakeFiles/amqp-consume.dir/consume.s"
	/usr/bin/gcc  $(C_DEFINES) $(C_FLAGS) -S /home/pi/rabbitmq-c/tools/consume.c -o CMakeFiles/amqp-consume.dir/consume.s

CMakeFiles/amqp-consume.dir/consume.o.requires:
.PHONY : CMakeFiles/amqp-consume.dir/consume.o.requires

CMakeFiles/amqp-consume.dir/consume.o.provides: CMakeFiles/amqp-consume.dir/consume.o.requires
	$(MAKE) -f CMakeFiles/amqp-consume.dir/build.make CMakeFiles/amqp-consume.dir/consume.o.provides.build
.PHONY : CMakeFiles/amqp-consume.dir/consume.o.provides

CMakeFiles/amqp-consume.dir/consume.o.provides.build: CMakeFiles/amqp-consume.dir/consume.o

CMakeFiles/amqp-consume.dir/unix/process.o: CMakeFiles/amqp-consume.dir/flags.make
CMakeFiles/amqp-consume.dir/unix/process.o: /home/pi/rabbitmq-c/tools/unix/process.c
	$(CMAKE_COMMAND) -E cmake_progress_report /home/pi/rabbitmq-c/bin-rabbitmq-c/CMakeFiles $(CMAKE_PROGRESS_2)
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Building C object CMakeFiles/amqp-consume.dir/unix/process.o"
	/usr/bin/gcc  $(C_DEFINES) $(C_FLAGS) -o CMakeFiles/amqp-consume.dir/unix/process.o   -c /home/pi/rabbitmq-c/tools/unix/process.c

CMakeFiles/amqp-consume.dir/unix/process.i: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Preprocessing C source to CMakeFiles/amqp-consume.dir/unix/process.i"
	/usr/bin/gcc  $(C_DEFINES) $(C_FLAGS) -E /home/pi/rabbitmq-c/tools/unix/process.c > CMakeFiles/amqp-consume.dir/unix/process.i

CMakeFiles/amqp-consume.dir/unix/process.s: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Compiling C source to assembly CMakeFiles/amqp-consume.dir/unix/process.s"
	/usr/bin/gcc  $(C_DEFINES) $(C_FLAGS) -S /home/pi/rabbitmq-c/tools/unix/process.c -o CMakeFiles/amqp-consume.dir/unix/process.s

CMakeFiles/amqp-consume.dir/unix/process.o.requires:
.PHONY : CMakeFiles/amqp-consume.dir/unix/process.o.requires

CMakeFiles/amqp-consume.dir/unix/process.o.provides: CMakeFiles/amqp-consume.dir/unix/process.o.requires
	$(MAKE) -f CMakeFiles/amqp-consume.dir/build.make CMakeFiles/amqp-consume.dir/unix/process.o.provides.build
.PHONY : CMakeFiles/amqp-consume.dir/unix/process.o.provides

CMakeFiles/amqp-consume.dir/unix/process.o.provides.build: CMakeFiles/amqp-consume.dir/unix/process.o

CMakeFiles/amqp-consume.dir/common.o: CMakeFiles/amqp-consume.dir/flags.make
CMakeFiles/amqp-consume.dir/common.o: /home/pi/rabbitmq-c/tools/common.c
	$(CMAKE_COMMAND) -E cmake_progress_report /home/pi/rabbitmq-c/bin-rabbitmq-c/CMakeFiles $(CMAKE_PROGRESS_3)
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Building C object CMakeFiles/amqp-consume.dir/common.o"
	/usr/bin/gcc  $(C_DEFINES) $(C_FLAGS) -o CMakeFiles/amqp-consume.dir/common.o   -c /home/pi/rabbitmq-c/tools/common.c

CMakeFiles/amqp-consume.dir/common.i: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Preprocessing C source to CMakeFiles/amqp-consume.dir/common.i"
	/usr/bin/gcc  $(C_DEFINES) $(C_FLAGS) -E /home/pi/rabbitmq-c/tools/common.c > CMakeFiles/amqp-consume.dir/common.i

CMakeFiles/amqp-consume.dir/common.s: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Compiling C source to assembly CMakeFiles/amqp-consume.dir/common.s"
	/usr/bin/gcc  $(C_DEFINES) $(C_FLAGS) -S /home/pi/rabbitmq-c/tools/common.c -o CMakeFiles/amqp-consume.dir/common.s

CMakeFiles/amqp-consume.dir/common.o.requires:
.PHONY : CMakeFiles/amqp-consume.dir/common.o.requires

CMakeFiles/amqp-consume.dir/common.o.provides: CMakeFiles/amqp-consume.dir/common.o.requires
	$(MAKE) -f CMakeFiles/amqp-consume.dir/build.make CMakeFiles/amqp-consume.dir/common.o.provides.build
.PHONY : CMakeFiles/amqp-consume.dir/common.o.provides

CMakeFiles/amqp-consume.dir/common.o.provides.build: CMakeFiles/amqp-consume.dir/common.o

# Object files for target amqp-consume
amqp__consume_OBJECTS = \
"CMakeFiles/amqp-consume.dir/consume.o" \
"CMakeFiles/amqp-consume.dir/unix/process.o" \
"CMakeFiles/amqp-consume.dir/common.o"

# External object files for target amqp-consume
amqp__consume_EXTERNAL_OBJECTS =

amqp-consume: CMakeFiles/amqp-consume.dir/consume.o
amqp-consume: CMakeFiles/amqp-consume.dir/unix/process.o
amqp-consume: CMakeFiles/amqp-consume.dir/common.o
amqp-consume: CMakeFiles/amqp-consume.dir/build.make
amqp-consume: CMakeFiles/amqp-consume.dir/link.txt
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --red --bold "Linking C executable amqp-consume"
	$(CMAKE_COMMAND) -E cmake_link_script CMakeFiles/amqp-consume.dir/link.txt --verbose=$(VERBOSE)

# Rule to build all files generated by this target.
CMakeFiles/amqp-consume.dir/build: amqp-consume
.PHONY : CMakeFiles/amqp-consume.dir/build

CMakeFiles/amqp-consume.dir/requires: CMakeFiles/amqp-consume.dir/consume.o.requires
CMakeFiles/amqp-consume.dir/requires: CMakeFiles/amqp-consume.dir/unix/process.o.requires
CMakeFiles/amqp-consume.dir/requires: CMakeFiles/amqp-consume.dir/common.o.requires
.PHONY : CMakeFiles/amqp-consume.dir/requires

CMakeFiles/amqp-consume.dir/clean:
	$(CMAKE_COMMAND) -P CMakeFiles/amqp-consume.dir/cmake_clean.cmake
.PHONY : CMakeFiles/amqp-consume.dir/clean

CMakeFiles/amqp-consume.dir/depend:
	cd /home/pi/rabbitmq-c/bin-rabbitmq-c && $(CMAKE_COMMAND) -E cmake_depends "Unix Makefiles" /home/pi/rabbitmq-c/tools /home/pi/rabbitmq-c/tools /home/pi/rabbitmq-c/bin-rabbitmq-c /home/pi/rabbitmq-c/bin-rabbitmq-c /home/pi/rabbitmq-c/bin-rabbitmq-c/CMakeFiles/amqp-consume.dir/DependInfo.cmake --color=$(COLOR)
.PHONY : CMakeFiles/amqp-consume.dir/depend
