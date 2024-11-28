# Copyright (c) 2024, Signaloid.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.


# The CircuitPython device mount path to sync the host application.
DEVICE := /run/media/$(shell whoami)/CIRCUITPY

# Adafruit and Community CircuitPython library bundles.
# To use a different bundle version, just change the version numbers below.
CIRCUITPYTHON_ADAFRUIT_BUNDLE_VERSION 	:= 20241023
CIRCUITPYTHON_ADAFRUIT_BUNDLE_NAME 	:= adafruit-circuitpython-bundle-9.x-mpy-$(CIRCUITPYTHON_ADAFRUIT_BUNDLE_VERSION)
CIRCUITPYTHON_ADAFRUIT_BUNDLE_URL 	:= https://github.com/adafruit/Adafruit_CircuitPython_Bundle/releases/download/$(CIRCUITPYTHON_ADAFRUIT_BUNDLE_VERSION)/$(CIRCUITPYTHON_ADAFRUIT_BUNDLE_NAME).zip

CIRCUITPYTHON_COMMUNITY_BUNDLE_VERSION 	:= 20241005
CIRCUITPYTHON_COMMUNITY_BUNDLE_NAME 	:= circuitpython-community-bundle-9.x-mpy-$(CIRCUITPYTHON_COMMUNITY_BUNDLE_VERSION)
CIRCUITPYTHON_COMMUNITY_BUNDLE_URL 	:= https://github.com/adafruit/CircuitPython_Community_Bundle/releases/download/$(CIRCUITPYTHON_COMMUNITY_BUNDLE_VERSION)/$(CIRCUITPYTHON_COMMUNITY_BUNDLE_NAME).zip


# Acquire the project root directory, used to locate all other directories.
MAKEFILE_PATH 	:= $(abspath $(firstword $(MAKEFILE_LIST)))
MAKEFILE_DIR 	:= $(dir $(MAKEFILE_PATH))
ROOT_DIR 	:= $(abspath $(MAKEFILE_DIR))

# Define the CircuitPython library directory, where the CircuitPython libraries
# are downloaded and extracted.
CIRCUITPYTHON_LIBS_DIR := $(ROOT_DIR)/CircuitPythonLibs

# The host application source directory, where all the host application source
# code, libraries, and assets are located.
SRC_DIR := $(ROOT_DIR)/src


.PHONY: bundle sync live-sync clean clean-device

all: bundle

# Bundle the host application and CircuitPython libraries.
bundle: clean
	@echo "Bundling files to project"
	git submodule update --init --recursive
	cd $(ROOT_DIR)/submodules/signaloid-python && \
	git apply $(ROOT_DIR)/signaloid-python.patch
	mkdir -p $(CIRCUITPYTHON_LIBS_DIR)
	cd $(CIRCUITPYTHON_LIBS_DIR) && \
	wget $(CIRCUITPYTHON_ADAFRUIT_BUNDLE_URL) && \
	wget $(CIRCUITPYTHON_COMMUNITY_BUNDLE_URL) && \
	unzip -o $(CIRCUITPYTHON_ADAFRUIT_BUNDLE_NAME).zip && \
	unzip -o $(CIRCUITPYTHON_COMMUNITY_BUNDLE_NAME).zip
	mkdir -p $(ROOT_DIR)/src/lib
	cd $(ROOT_DIR)/src/lib && \
	ln -s $(CIRCUITPYTHON_LIBS_DIR)/$(CIRCUITPYTHON_ADAFRUIT_BUNDLE_NAME)/lib/adafruit_display_text && \
	ln -s $(CIRCUITPYTHON_LIBS_DIR)/$(CIRCUITPYTHON_ADAFRUIT_BUNDLE_NAME)/lib/adafruit_imageload && \
	ln -s $(CIRCUITPYTHON_LIBS_DIR)/$(CIRCUITPYTHON_COMMUNITY_BUNDLE_NAME)/lib/circuitpython_uplot

# Sync the host application and CircuitPython libraries to the device.
sync: clean-device
	@echo "Syncing files to $(DEVICE)"
	cp -Lrv $(ROOT_DIR)/src/* $(DEVICE)

# Sync the host application and CircuitPython libraries to the device, and
# watch for any changes in the host application source code, and live sync them
# to the device.
live-sync: sync
	@echo "Live Syncing files to $(DEVICE)"
	@inotifywait -m -r -e create,close_write,moved_from,moved_to --format '%e %w%f' $(SRC_DIR) | \
	while read EVENT FILE_PATH; do \
	NEW_FILE_PATH="$(DEVICE)$${FILE_PATH/"$(SRC_DIR)"/""}"; \
	if [ $$EVENT = "CREATE,ISDIR" ]; then \
		echo "  MKDIR $$NEW_FILE_PATH"; \
		mkdir -p $$NEW_FILE_PATH; \
	elif [ $$EVENT = "MOVED_FROM" ] || [ $$EVENT = "MOVED_FROM,ISDIR" ]; then \
		echo "  RM    $$NEW_FILE_PATH"; \
		rm -rf $$NEW_FILE_PATH; \
	elif [ $$EVENT = "CLOSE_WRITE,CLOSE" ] || [ $$EVENT = "MOVED_TO" ] || [ $$EVENT = "MOVED_TO,ISDIR" ]; then \
		echo "  CP    $$NEW_FILE_PATH"; \
		cp -r $$FILE_PATH $$NEW_FILE_PATH; \
	elif [ $$EVENT = "CREATE" ]; then \
		: \
	else \
		echo "  Unhandled event $$EVENT for $$FILE_PATH"; \
	fi; \
	done;

# Clean the project.
clean:
	rm -rf $(CIRCUITPYTHON_LIBS_DIR)
	rm -rf $(ROOT_DIR)/src/lib

# Clean the device.
clean-device:
	rm -rf $(DEVICE)/*
	@echo "print(\"Hello World!\")" > $(DEVICE)/code.py
