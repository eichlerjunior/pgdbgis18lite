#/**********************************************************************
# *
# * PostGIS - Spatial Types for PostgreSQL
# * http://postgis.net
# *
# * PostGIS is free software: you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation, either version 2 of the License, or
# * (at your option) any later version.
# *
# * PostGIS is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# * GNU General Public License for more details.
# *
# * You should have received a copy of the GNU General Public License
# * along with PostGIS.  If not, see <http://www.gnu.org/licenses/>.
# *
# **********************************************************************
# *
# * Copyright 2019 Raúl Marín
# *
# **********************************************************************/

CC=gcc
CXX=
CFLAGS=-I../liblwgeom  -I/usr/include -I/usr/include  -I/usr/include/libxml2  -I/usr/include/json-c   -DNDEBUG  -std=gnu11 -O3 -march=native -pipe -Wno-array-bounds -fno-math-errno -fno-signed-zeros -Wall -O2  -fPIC -DPIC
CXXFLAGS=-I../liblwgeom  -I/usr/include -I/usr/include  -I/usr/include/libxml2  -I/usr/include/json-c   -DNDEBUG  -O3 -march=native -pipe -Wno-array-bounds  -fPIC -DPIC
LDFLAGS =  -lm
top_builddir = ..
libdir = ${exec_prefix}/lib
LIBTOOL = $(SHELL) $(top_builddir)/libtool

all: libwagyu.la libryu.la libflatgeobuf.la

libwagyu.la:
	$(MAKE) -C wagyu $@

libryu.la:
	$(MAKE) -C ryu $@

libflatgeobuf.la:
	$(MAKE) -C flatgeobuf $@

clean:
	$(MAKE) -C wagyu $@
	$(MAKE) -C ryu $@
	$(MAKE) -C flatgeobuf $@

distclean: clean
	$(MAKE) -C wagyu $@
	$(MAKE) -C ryu $@
	$(MAKE) -C flatgeobuf $@
	rm -f Makefile

.PHONY: install uninstall check check-unit check-regress
