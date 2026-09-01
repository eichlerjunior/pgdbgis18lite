# **********************************************************************
# *
# * PostGIS - Spatial Types for PostgreSQL
# * http://postgis.net
# * Copyright 2008 Mark Cave-Ayland
# *
# * This is free software; you can redistribute and/or modify it under
# * the terms of the GNU General Public Licence. See the COPYING file.
# *
# **********************************************************************

srcdir = .
top_builddir = ..

CC=gcc
CFLAGS= -I$(srcdir)/../liblwgeom -I$(top_builddir)/liblwgeom  -I/usr/include -I/usr/include  -I/usr/include/libxml2  -I/usr/include/json-c   -DNDEBUG  -std=gnu11 -O3 -march=native -pipe -Wno-array-bounds -fno-math-errno -fno-signed-zeros -Wall -O2 -I/usr/local/pgsql-18/include/server -I/usr/include  -fPIC -DPIC 
LDFLAGS= 

YACC=/usr/bin/bison
LEX=flex



# Standalone COMMON objects
SA_OBJS = \
	gserialized_gist.o \
	lwgeom_transform.o \
	lwgeom_cache.o \
	lwgeom_pg.o \
	shared_gserialized.o


SA_HEADERS = \
	lwgeom_pg.h \
	lwgeom_transform.h \
	lwgeom_cache.h \
	gserialized_gist.h

all: libpgcommon.a

# nothing to install or uninstall
install uninstall:

libpgcommon.a: $(SA_OBJS) $(SA_HEADERS)
	gcc-ar rs libpgcommon.a $(SA_OBJS)

maintainer-clean: clean

clean:
	$(MAKE) -C cunit clean
	rm -f $(SA_OBJS)
	rm -f $(NM_OBJS)
	rm -f libpgcommon.a

distclean: clean
	$(MAKE) -C cunit distclean
	rm -f Makefile

check: check-unit

check-regress:

check-unit: libpgcommon.a
	$(MAKE) -C cunit check

# Command to build each of the .o files
$(SA_OBJS): %.o: %.c
	$(CC) $(CFLAGS) -c -o $@ $<

$(SA_OBJS): ../postgis_config.h

