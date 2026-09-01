# **********************************************************************
# *
# * PostGIS - Spatial Types for PostgreSQL
# * http://postgis.net
# * Copyright 2008 Paul Ramsey, Mark Cave-Ayland
# *
# * This is free software; you can redistribute and/or modify it under
# * the terms of the GNU General Public Licence. See the COPYING file.
# *
# **********************************************************************

top_builddir = ../../..
top_srcdir = ../../..
builddir = .
srcdir = .

CC=gcc
SHELL = /bin/bash
LIBTOOL = $(SHELL) $(top_builddir)/libtool

LIBLWGEOM_LDFLAGS=../../../liblwgeom/.libs/liblwgeom.a
LIBLWGEOM_CFLAGS = -I$(top_srcdir)/liblwgeom -I$(top_builddir)/liblwgeom
LIBGDAL_CFLAGS=-I/usr/include/gdal
LIBGDAL_LDFLAGS=-L/usr/lib/x86_64-linux-gnu -lgdal
PROJ_CFLAGS=-I/usr/include
PROJ_LDFLAGS=-L/usr/lib -lproj
GEOS_CFLAGS=-I/usr/include
GEOS_LDFLAGS=-L/usr/lib/x86_64-linux-gnu -lgeos_c
CUNIT_LDFLAGS=

RTCORE_CFLAGS = -I$(top_srcdir)/raster/rt_core
RTCORE_LDFLAGS = $(top_builddir)/raster/rt_core/librtcore.a



CC=gcc
CFLAGS = \
	-I$(top_builddir) \
	-I$(top_builddir)/raster \
	-I$(builddir) \
	-I$(builddir)/.. \
	-DPOSTGIS_TOP_SRC_DIR='"$(realpath $(top_srcdir))"' \
	$(LIBLWGEOM_CFLAGS) \
	$(RTCORE_CFLAGS) \
	$(PROJ_CFLAGS) \
	$(LIBGDAL_CFLAGS) \
	$(GEOS_CFLAGS) \
	 \
	-std=gnu11 -O3 -march=native -pipe -Wno-array-bounds -fno-math-errno -fno-signed-zeros -Wall -O2

LDFLAGS = \
	$(RTCORE_LDFLAGS) \
	$(LIBLWGEOM_LDFLAGS) \
	$(LIBGDAL_LDFLAGS) \
	$(GEOS_LDFLAGS) \
	$(PROJ_LDFLAGS)


# ADD YOUR NEW TEST FILE HERE (1/1)
OBJS=	\
	cu_pixtype.o \
	cu_raster_basics.o \
	cu_band_basics.o \
	cu_raster_wkb.o \
	cu_raster_geometry.o \
	cu_raster_misc.o \
	cu_band_stats.o \
	cu_band_misc.o \
	cu_gdal.o \
	cu_spatial_relationship.o \
	cu_mapalgebra.o \
	cu_misc.o \
	cu_tester.o

# If we couldn't find the cunit library then display a helpful message
ifeq ($(CUNIT_LDFLAGS),)
all: requirements_not_met_cunit
check: requirements_not_met_cunit
else

# Build the unit tester
all: cu_tester

# Build and run the unit tester
check: cu_tester
	@./cu_tester

endif

# Build the main unit test executable
cu_tester: $(top_builddir)/raster/rt_core/librtcore.a $(OBJS)
	$(LIBTOOL) --mode=link $(CC) $(CFLAGS) -o $@ $(OBJS) $(LDFLAGS) $(CUNIT_LDFLAGS)

# Command to build each of the .o files
$(OBJS): %.o: %.c
	$(CC) $(CFLAGS) -c -o $@ $<

$(top_builddir)/raster/rt_core/librtcore.a:
	$(MAKE) -C $(top_builddir)/raster/rt_core

# Clean target
clean:
	rm -rf .libs
	rm -f $(OBJS)
	rm -f cu_tester

distclean: clean
	rm -f Makefile

# Requirements message
requirements_not_met_cunit:
	@echo
	@echo "WARNING:"
	@echo
	@echo "configure was unable to find CUnit which is required for unit testing."
	@echo "In order to enable unit testing, you must install CUnit and then re-run configure."
	@echo
