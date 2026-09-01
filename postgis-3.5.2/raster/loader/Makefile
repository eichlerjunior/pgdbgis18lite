#############################################################################
#
# Copyright (c) 2011 Regents of the University of California
#   <bkpark@ucdavis.edu>
# Copyright (c) 2009-2022 Sandro Santilli <strk@kbt.io>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
#############################################################################

top_builddir = ../..
builddir = .
top_srcdir = ../..
srcdir = .
prefix = /usr/local
exec_prefix = ${prefix}
bindir = ${exec_prefix}/bin



CC=gcc
SHELL = /bin/bash
INSTALL = /usr/bin/install -c
LIBTOOL = $(SHELL) $(top_builddir)/libtool

# Filenames with extension as determined by the OS
RASTER2PGSQL=raster2pgsql

# PostgreSQL executable directory
PGSQL_BINDIR=/usr/local/pgsql-18/bin

LIBLWGEOM_LDFLAGS = $(top_builddir)/liblwgeom/liblwgeom.la
LIBLWGEOM_CFLAGS = -I$(top_builddir)/liblwgeom -I$(top_srcdir)/liblwgeom
LIBGDAL_CFLAGS=-I/usr/include/gdal
LIBGDAL_LDFLAGS=-L/usr/lib/x86_64-linux-gnu -lgdal
LIBGDAL_DEPLIBS_LDFLAGS=
PROJ_CFLAGS=-I/usr/include
PROJ_LDFLAGS=-L/usr/lib -lproj
GEOS_CFLAGS=-I/usr/include
GEOS_LDFLAGS=-L/usr/lib/x86_64-linux-gnu -lgeos_c

RTCORE_CFLAGS = -I$(srcdir)/../rt_core -I$(builddir)/.. -I$(builddir) -I$(top_builddir)
RTCORE_LDFLAGS = $(builddir)/../rt_core/librtcore.a

# GetText includes and libraries
GETTEXT_CFLAGS = 
GETTEXT_LDFLAGS =  

# iconv flags
ICONV_LDFLAGS= -lc
ICONV_CFLAGS=

CFLAGS = \
	-std=gnu11 -O3 -march=native -pipe -Wno-array-bounds -fno-math-errno -fno-signed-zeros -Wall -O2  -fPIC -DPIC \
	$(RTCORE_CFLAGS) \
	$(LIBLWGEOM_CFLAGS) \
	$(PROJ_CFLAGS) \
	$(LIBGDAL_CFLAGS) \
	$(GEOS_CFLAGS) \
	$(GETTEXT_CFLAGS) \
	$(ICONV_CFLAGS)

LDFLAGS = \
	 -lm \
	$(LIBLWGEOM_LDFLAGS) \
	$(LIBGDAL_LDFLAGS) \
	$(LIBGDAL_DEPLIBS_LDFLAGS) \
	$(GEOS_LDFLAGS) \
	$(PROJ_LDFLAGS) \
	$(GETTEXT_LDFLAGS) \
	$(ICONV_LDFLAGS)

all: $(RASTER2PGSQL)

raster2pgsql.o: raster2pgsql.c
	$(CC) $(CPPFLAGS) $(CFLAGS) -c $<

$(RASTER2PGSQL): ../rt_core/librtcore.a raster2pgsql.o
	$(LIBTOOL) --mode=link $(CC) $(CFLAGS) $^ $(LDFLAGS) -o $@

installdir:
	@mkdir -p $(DESTDIR)$(bindir)

install: installdir
	$(LIBTOOL) --mode=install $(INSTALL) $(RASTER2PGSQL) "$(DESTDIR)$(bindir)/$(RASTER2PGSQL)"

uninstall:
	$(LIBTOOL) --mode=uninstall $(RM) "$(DESTDIR)$(bindir)/$(RASTER2PGSQL)"

../rt_core/librtcore.a:
	$(MAKE) -C $(buidldir)/../rt_core

clean:
	rm -rf .libs
	rm -f *.o $(RASTER2PGSQL)

distclean: clean
	rm -f Makefile
