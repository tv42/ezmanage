#!/usr/bin/perl -wT
#
# $Id: ezmanage-menu.cgi,v 1.1 2000/03/20 17:29:39 tv42 Exp $
#
# ezmanage-menu.cgi - main menu for ezmanage
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

=head1 NAME

ezmanage-menu.cgi - main menu for ezmanage

=head1 SYNOPSIS

  Called by a WWW server as a CGI script.

=head1 DESCRIPTION

This script provides a WWW interface to the B<ezmanage> mailing list
management system. The user can choose a list to configure, create a
new list, choose a moderator group to configure or create a new
moderator group.

=head1 AUTHOR

Tommi Virtanen, Havoc Consulting (tv@havoc.fi)

=cut

############################################################################
#
# Configure this:
#

my $back = './';
my $backtext = 'back';

############################################################################

use strict;
use CGI::Carp; # qw(fatalsToBrowser);
use CGI;
use lib '/usr/lib/ezmanage/lib';
require Mail::Ezmanage;
require Mail::Ezmanage::Mod;

sub main() {
  my $query = new CGI('');
  print $query->header, $query->start_html(
					   -title=>'Ezmanage Main Menu',
					  ), "\n",
    $query->h1('Ezmanage Main Menu'), "\n",
    "<P>[<A HREF=\"$back\">$backtext</A>]\n",
    '<A href="#groups">[skip to moderator groups]</A>', "\n\n",
    
    $query->h2('Lists:'), "\n";
  
  my $l = Mail::Ezmanage::get_lists();
  if (defined $l) { print html_list('ezmanage-list-config.cgi', @$l), "\n"; }
  else { 
    print '<P>There was a ', 
    Mail::Ezmanage::failure() ? 'fatal' : 'transient', 
    'error while fetching a list of all lists; ', Mail::Ezmanage::error(); 
  }
  undef $l;
  
  print $query->startform(-action=>'ezmanage-list-new.cgi'),
  $query->submit(-name=>'New list'), 
  $query->textfield(-name=>'name'),
  $query->endform, "\n",

  '<A name="groups">', $query->hr, "</A>\n\n",
  $query->h2('Moderator Groups:'), "\n";

  my $g = Mail::Ezmanage::Mod::get_groups();
  if (defined $g) { print html_list('ezmanage-group-config.cgi', @$g), "\n"; }
  else { 
    print '<P>There was a ', 
    Mail::Ezmanage::Mod::failure() ? 'fatal' : 'transient', 
    'error while fetching a list of moderator groups; ', Mail::Ezmanage::Mod::error(); 
  }
  print $query->startform(-action=>'ezmanage-group-new.cgi'),
  $query->submit(-name=>'New moderator group'), 
  $query->textfield(-name=>'name'),
  $query->endform, "\n",
  about($query);
}

sub html_list($@) {
  my ($url) = shift;
  return "<UL>\n", (map {
    '  <LI>' . (defined $url ? '<A href="' . $url . '?name=' . $_ . '">' : '')
      . $_ . (defined $url ? '</A>' : '') . "\n" 
    } @_), "</UL>\n";
}

main();

sub about($) {
  my ($query) = @_;
  my ($n, $v) = ' $Id: ezmanage-menu.cgi,v 1.1 2000/03/20 17:29:39 tv42 Exp $ ' =~ m{^.*?Id: (\S+) (\S+) .*};
  $v='0.0' unless defined $v;
  $n='unknown' unless defined $n;
  $n =~ s/,v$//g;
  return 
    "\n\n", $query->hr, "\n",
    '<SMALL>', "$n v$v, Copyright 1998 Tommi Virtanen, Havoc Consulting.", '</SMALL>', "\n",
    $query->end_html, "\n";
}
