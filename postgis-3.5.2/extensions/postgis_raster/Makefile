include ./../upgradeable_versions.mk

EXTENSION     = postgis_raster
EXTVERSION    = 3.5.2
MINORVERSION  = 3.5
MODULEPATH    = $$libdir/$(EXTENSION)-3

ifeq (no,yes)
MODULEPATH=$$libdir/$(EXTENSION)-$(MINORVERSION)
endif
GREP = /usr/bin/grep

# SQL preprocessor
SQLPP = /usr/bin/cpp -traditional-cpp -w -P -Upixel -Ubool

MICRO_NUMBER  = $(shell echo $(EXTVERSION) | \
						$(PERL) -pe 's/\d.\d.(\d+)[a-zA-Z]*\d*/$1/'

PREREL_NUMBER = $(shell echo $(EXTVERSION) | \
                        $(PERL) -pe 's/\d\.\d\.(.*)/\1/' | \
                        $(GREP) "[a-zA-Z]" | \
                        $(PERL) -pe 's/\d+[a-zA-Z]+(\d+)/\1/'

MICRO_PREV    = $(shell if test "$(MICRO_NUMBER)x" != "x"; then expr $(MICRO_NUMBER) - 1; fi)
PREREL_PREV   = $(shell if test "$(PREREL_NUMBER)x" != "x"; then expr $(PREREL_NUMBER) - 1; fi)

PREREL_PREFIX = $(shell echo $(EXTVERSION) | \
                        $(PERL) -pe 's/\d\.\d\.(.*)/\1/' | \
                        $(GREP) "[a-zA-Z]" | \
                        $(PERL) -pe 's/(\d+[a-zA-Z]+)\d*/\1/'

DATA_built = \
	$(EXTENSION).control \
	sql/$(EXTENSION)--$(EXTVERSION).sql \
	sql/$(EXTENSION)--unpackaged.sql \
	sql/$(EXTENSION)--unpackaged--$(EXTVERSION).sql \
	$(NULL)

# Scripts making up the extension file
# NOTE: order matters
EXTENSION_SCRIPTS = \
	sql/rtpostgis.sql

# Scripts making up the extension minor upgrade file
# NOTE: order matters
EXTENSION_UPGRADE_SCRIPTS = \
	../postgis_extension_helper.sql \
	sql/rtpostgis_upgrade.sql \
	../postgis_extension_helper_uninstall.sql

# Scripts making up the extension upgrade-from-unpackaged file
# NOTE: order matters
EXTENSION_UNPACKAGED_UPGRADE_SCRIPTS = \
	sql/$(EXTENSION)--$(EXTVERSION).sql

EXTRA_CLEAN = sql

CURV_big=35

all: sql/$(EXTENSION)--$(EXTVERSION).sql sql/$(EXTENSION)--unpackaged--$(EXTVERSION).sql

sql:
	mkdir -p $@

$(EXTENSION).control: $(EXTENSION).control.in Makefile
	cat $< \
		| sed -e 's|@EXTVERSION@|$(EXTVERSION)|g' \
		| sed -e 's|@EXTENSION@|$(EXTENSION)|g' \
		| sed -e 's|@MODULEPATH@|$(MODULEPATH)|g' \
		> $@

sql/$(EXTENSION)--$(EXTVERSION).sql: $(EXTENSION_SCRIPTS) | sql
	printf '\\echo Use "CREATE EXTENSION $(EXTENSION)" to load this file. \\quit\n' > $@
	cat $^ >> $@

sql/$(EXTENSION)--unpackaged.sql: Makefile | sql
	echo "-- Nothing to do here" > $@

sql/$(EXTENSION)--unpackaged--$(EXTVERSION).sql: sql/$(EXTENSION)--ANY--$(EXTVERSION).sql sql/$(EXTENSION)--$(EXTVERSION).sql ../../utils/create_unpackaged.pl Makefile | sql
	cat sql/$(EXTENSION)--$(EXTVERSION).sql | $(PERL) ../../utils/create_unpackaged.pl $(EXTENSION) > $@
	# Upgrade after packaging
	cat sql/$(EXTENSION)--ANY--$(EXTVERSION).sql >> $@

unpackaged_check.sql: unpackaged_check.sql.in Makefile
	cat $< \
		| sed -e 's|@EXTVERSION@|$(EXTVERSION)|g' \
		> $@

#strip BEGIN/COMMIT since these are not allowed in extensions
sql/rtpostgis.sql: sql/rtpostgis_for_extension.sql | sql
	$(PERL) -pe 's/BEGIN\;//g ; s/COMMIT\;//g' $< > $@

sql/rtpostgis_for_extension.sql: ../../raster/rt_pg/rtpostgis.sql.in ../../postgis_revision.h | sql
	$(SQLPP) -I./../../postgis/ -I../../ $< > $@.tmp
	grep -v '^#' $@.tmp | \
	$(PERL) -lpe "s'MODULE_PATHNAME'\$(MODULEPATH)'g" > $@
	rm -f $@.tmp

sql/rtpostgis_upgrade.sql: sql/rtpostgis_upgrade_for_extension.sql | sql
	$(PERL) -pe "s/BEGIN\;//g ; s/COMMIT\;//g; s/^(DROP .*)\;/SELECT postgis_extension_drop_if_exists('$(EXTENSION)', '\1');\n\1\;/" $< > $@

#this keeps the @extschema@. in place since extension machinery will replace during install
sql/rtpostgis_upgrade_for_extension.sql: ../../postgis/common_before_upgrade.sql ../../raster/rt_pg/rtpostgis_upgrade_cleanup.sql sql/rtpostgis_upgrade_for_extension.sql.in ../../raster/rt_pg/rtpostgis_drop.sql ../../postgis/common_after_upgrade.sql | sql
	echo 'BEGIN;' > $@
	cat $^ | sed -e 's/^BEGIN;$$//' -e 's/^COMMIT;$$//' >> $@
	echo 'COMMIT;' >> $@


sql/rtpostgis_upgrade_for_extension.sql.in: sql/rtpostgis_for_extension.sql ../../utils/create_upgrade.pl | sql
	$(PERL) ../../utils/create_upgrade.pl $< > $@


sql/$(EXTENSION)--ANY--$(EXTVERSION).sql: $(EXTENSION_UPGRADE_SCRIPTS) | sql
	printf '\\echo Use "CREATE EXTENSION $(EXTENSION)" to load this file. \\quit\n' > $@
	cat $^ >> $@

include ./../upgrade-paths-rules.mk

distclean: clean
	rm -f Makefile

PG_CONFIG := /usr/local/pgsql-18/bin/pg_config
PGXS := /usr/local/pgsql-18/lib/pgxs/src/makefiles/pgxs.mk
include $(PGXS)
PERL = /usr/bin/perl
INSTALL=/usr/bin/install -c
INSTALL_DATA=${INSTALL} -m 644
ifneq (/usr/bin/mkdir -p,)
	MKDIR_P = /usr/bin/mkdir -p
endif



top_srcdir = ../..
top_builddir = ../..
abs_topbuilddir=$(abspath $(top_builddir))
