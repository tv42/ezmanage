#
# $Id: Makefile,v 1.1 2000/03/20 17:29:38 tv42 Exp $
#
# Makefile for ezmanage - a mailing list management system
#
# Copyright (C) 1998 Tommi Virtanen
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
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
############################################################################

PREFIX=/usr
DESTDIR=
INSTDIR=$(DESTDIR)$(PREFIX)/lib/ezmanage
ETCDIR=$(DESTDIR)/etc/ezmanage
CGIDIR=$(INSTDIR)/cgi
PUBCGIDIR=$(INSTDIR)/publiccgi
LIBDIR=$(INSTDIR)/lib

DOCDIR=$(DESTDIR)$(PREFIX)/doc/ezmanage
BINDIR=$(DESTDIR)$(PREFIX)/bin
MANDIR=$(DESTDIR)$(PREFIX)/man/man1

LIBFILES=lib/Mail/Ezmanage/Fullnames.pm lib/Mail/Ezmanage/Mod.pm \
	lib/Mail/Ezmlm/Maintenance.pm lib/Mail/Ezmanage.pm \
	lib/Mail/Ezmlm.pm

PERLBINFILES=bin/ezmanage-skeleton bin/ezmanage-webarchive \
	bin/ezmanage-fullnames-maintenance
BINFILES=bin/ezmanage-archive $(PERLBINFILES)

all: doc man

doc:
	make -C doc

man:
	for a in $(PERLBINFILES) ; do pod2man $$a >$$a.1 ; done

clean:
	make -C doc clean
	-for a in $(PERLBINFILES) ; do rm -f $$a.1 ; done

install: install-cgi install-pubcgi install-config install-lib install-doc \
	install-bin install-man

install-doc: doc
	make -C doc install INSTDIR=$(DOCDIR)

install-cgi:
	install -d $(CGIDIR)
	install cgi/*.cgi $(CGIDIR)

install-pubcgi:
	install -d $(PUBCGIDIR)
	install publiccgi/*.cgi $(PUBCGIDIR)

install-config:
	install -d $(ETCDIR)
	install --mode=0644 config/*rc $(ETCDIR)

install-lib: install-lib-ezmanage install-lib-ezmlm

install-lib-ezmanage:
	install -d $(LIBDIR)/Mail/Ezmanage
	install --mode=0644 lib/Mail/Ezmanage.pm $(LIBDIR)/Mail
	install --mode=0644 lib/Mail/Ezmanage/*.pm $(LIBDIR)/Mail/Ezmanage

install-lib-ezmlm:
	install -d $(LIBDIR)/Mail/Ezmlm
	install --mode=0644 lib/Mail/Ezmlm.pm $(LIBDIR)/Mail
	install --mode=0644 lib/Mail/Ezmlm/*.pm $(LIBDIR)/Mail/Ezmlm

install-bin:
	install -d $(BINDIR)
	install $(BINFILES) $(BINDIR)

install-man: man
	install -d $(MANDIR)
	for a in $(PERLBINFILES) ; do install $$a.1 $(MANDIR) ; done
