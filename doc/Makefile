#
# $Id: Makefile,v 1.1 2000/03/20 17:29:39 tv42 Exp $
# Copyright 1998 Tommi Virtanen, Havoc Consulting
#
HTML = ezmanage.html \
	admin/structure.html \
	owner/faq.html owner/interface.html \
	install/quickstart.html install/blurb.html
# install/install-guide.html owner/setup.html owner/common-activities.html

TODO = $(HTML:.html=.todo.html)
FILES = $(HTML) $(TODO)

OPTIONS = -q -DROOT~. -I. --includefile=template.wml
#--epilog=weblint --epilog=linklint

INSTDIR=/usr/doc/ezmanage

all: $(FILES)

%.html %.todo.html: %.wml template.wml
	wml $(OPTIONS) $< -o$*.todo.html -o'!(TODO+THINK)':$*.html

bugs:
	grep -ri '#.*TODO' ..|cut -d: -f1|grep -v '^.*~$$'|sort|uniq -c|sort -nr|perl -F'"\t../"' -ane 'chomp @F; push @F, "*" x shift @F; printf "%35s %s\n", @F;'

showbugs:
	grep -ri '#.*TODO.*' ..|grep -v '^[^:]*~:'|perl -F: -ane '$$_=shift @F; s!^\.\./!!; $$F[0]=~s!^\s+!!; $$p=$$_, print "$$_:\n" if $$_ ne $$p; print "  ", join ":", @F'

clean:
	-rm -f $(FILES)

check: all
	weblint $(HTML)

validate:
	nsgmls -s -m /usr/lib/xemacs-20.4/etc/sgml//CATALOG /usr/lib/xemacs-20.4/etc/sgml/html.decl $(HTML)

install: all
	install -d $(INSTDIR)/owner $(INSTDIR)/install $(INSTDIR)/admin
	for a in $(HTML) ; do install --mode=0644 $$a $(INSTDIR)/$$a ; done
