# mxstore: the store of mx OS, its programs from GitHub's releases. So far its
# first step, tlstest: DNS, a TLS handshake and an HTTPS GET, timed.
#
#   make           build/apps/mxstore/tlstest.elf: an MXOS program (libmxk)
#
# mbedTLS (libs/mbedtls, upstream at v3.6.8) with src/mbedtls_user.h.

HERE     := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
PS2MAX   ?= $(abspath $(HERE)/../..)
MAXSDK   ?= $(PS2MAX)/libs/maxsdk
MBEDTLS  ?= $(PS2MAX)/libs/mbedtls
MX_TARGET ?= mxos
OUT      ?= $(PS2MAX)/build/apps/mxstore

all: $(OUT)/tlstest.elf

MAXSDK_OUT ?= $(OUT)/maxsdk
export EXTRA_CFLAGS = -ffunction-sections -fdata-sections
include $(MAXSDK)/mk/maxsdk.mk

PICOLIBC ?= $(PS2MAX)/build/libs/picolibc/install
LIBC_LIBS = $(MAXSDK_OUT)/libc/glue.c.o $(MAXSDK_OUT)/libmxc.a $(PICOLIBC)/lib/libc.a \
            $(MX_LIB) $(MAXSDK_OUT)/librt.a
$(MAXSDK_OUT)/libc/glue.c.o $(MAXSDK_OUT)/libmxc.a $(MAXSDK_OUT)/librt.a &: $(MX_LIB)
	$(MAKE) -C $(MAXSDK) OUT=$(MAXSDK_OUT) libc
SCFLAGS = $(filter-out -ffreestanding,$(CFLAGS)) -MMD -nostdlibinc -isystem $(PICOLIBC)/include \
          -I$(MBEDTLS)/include -I$(HERE)/src -DMBEDTLS_USER_CONFIG_FILE='"mbedtls_user.h"'

MBEDTLS_SRCS = $(notdir $(wildcard $(MBEDTLS)/library/*.c))
MBEDTLS_OBJS = $(MBEDTLS_SRCS:%.c=$(OUT)/obj/mbedtls/%.o)
SRCS = tlstest port
OBJS = $(SRCS:%=$(OUT)/obj/%.o) $(OUT)/obj/roots.o

$(OUT)/obj/mbedtls/%.o: $(MBEDTLS)/library/%.c $(HERE)/src/mbedtls_user.h
	@mkdir -p $(dir $@)
	$(CC) $(SCFLAGS) -I$(MBEDTLS)/library -c $< -o $@

$(OUT)/obj/%.o: $(HERE)/src/%.c
	@mkdir -p $(dir $@)
	$(CC) $(SCFLAGS) $(MX_NET_CFLAGS) -c $< -o $@

$(OUT)/roots.pem: $(sort $(wildcard $(HERE)/certs/*.pem))
	@mkdir -p $(dir $@)
	cat $^ > $@

$(OUT)/obj/roots.o: $(HERE)/src/roots.S $(OUT)/roots.pem
	@mkdir -p $(dir $@)
	$(CC) $(CFLAGS) -Wa,-I$(OUT) -c $< -o $@

$(OUT)/tlstest.elf: $(OBJS) $(MBEDTLS_OBJS) $(MX_LIB) $(MX_CRT0) $(MX_LD) $(LIBC_LIBS)
	$(call link,$@,$(MX_CRT0) $(OBJS) $(MBEDTLS_OBJS) $(LIBC_LIBS))

-include $(OBJS:.o=.d) $(MBEDTLS_OBJS:.o=.d)

.PHONY: all
