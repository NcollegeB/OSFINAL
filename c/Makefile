CC ?= gcc
CFLAGS ?= -std=c11 -O2 -Wall -Wextra -pedantic -D_POSIX_C_SOURCE=200809L
LDFLAGS ?= -pthread

BUILD_DIR := build
TARGETS := \
	$(BUILD_DIR)/monte_carlo_c \
	$(BUILD_DIR)/matrix_mul_c \
	$(BUILD_DIR)/dns_lookup_c

.PHONY: all clean

all: $(TARGETS)

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

$(BUILD_DIR)/monte_carlo_c: src/monte_carlo.c src/common.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

$(BUILD_DIR)/matrix_mul_c: src/matrix_mul.c src/common.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

$(BUILD_DIR)/dns_lookup_c: src/dns_lookup.c src/common.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

clean:
	rm -rf $(BUILD_DIR)

