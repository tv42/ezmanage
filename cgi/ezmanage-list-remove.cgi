#!/usr/bin/perl -wT
#
# $Id: ezmanage-list-remove.cgi,v 1.1 2000/03/20 17:29:39 tv42 Exp $
#
# ezmanage-list-remove.cgi - remove a mailing list
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

ezmanage-list-remove.cgi - remove a mailing list

=head1 SYNOPSIS

  Called by a WWW server as a CGI script.

=head1 DESCRIPTION

This script provides a backend for F<ezmanage-list-config.cgi>, to
remove a mailing list. If called without parameters, it will display a
menu to choose the list from. If called only with the list name, it
will return a confirmation request similar to
F<ezmanage-list-config.cgi>.  If called with the list name and a
positive response to the confirmation request, it will remove the
list.

=head1 PARAMETERS

=over 4

=item name

Name of the list to remove

=item Remove

Actually remove the list, and don't ask for confirmation

=back

=head1 AUTHOR

Tommi Virtanen, Havoc Consulting (tv@havoc.fi)

=cut

############################################################################

use strict;
use lib '/usr/lib/ezmanage/lib';
use CGI::Carp; # qw(fatalsToBrowser);
use CGI;
require Mail::Ezmanage;

my $query=new CGI;
$query->import_names();

my $lists = Mail::Ezmanage::get_lists();

sub select_list() {
  return 
    "<P>Select the list you wish, either from the scrollable list\n",
    "or by typing it's name in the box:\n\n",
    '<P>', $query->start_form(), 
    $query->textfield(-name=>'name'), ' ', $query->submit(-name=>'Select'), 
    $query->endform(), "\n",
    '<P>', $query->start_form(),
    $query->scrolling_list('name', $lists, undef, 10),
    ' ', $query->submit(-name=>'Select'), 
    $query->endform(), "\n";
}

sub main() {
  if (not defined $Q::name or $Q::name eq '') {
    print $query->header,
    $query->start_html(-title=>'Select list to remove'), "\n",
    $query->h1('Select list to remove'), "\n",
    '<P>[<A HREF="ezmanage-menu.cgi">back to menu</A>]', "\n",
    select_list(),
    about();
  }
  elsif ($Q::name !~ /^[a-z0-9:_-]+$/i) {
    print $query->header,
    $query->start_html(-title=>'Invalid list name'), "\n",
    $query->h1('Invalid list name'), "\n",
    '<P>[<A HREF="ezmanage-menu.cgi">back to menu</A>]', "\n",
    '<P>The list name contains invalid characters.', "\n",
    select_list(),
    about();
  }
  elsif (not defined $lists) {
    print $query->header,
    $query->start_html(-title=>'Error while fetching list of lists'), "\n",
    $query->h1('Error while fetching list of lists'), "\n",
    '<P>[<A HREF="ezmanage-list-menu.cgi">back to menu</A>]', "\n";
    if (Mail::Ezmanage::failure()) {
      print join "\n", 
      '<P>There was a fatal error fetching a list of all lists.',
      '<BR>The error message was:',
    '<PRE>',
      Mail::Ezmanage::error(),
      '</PRE>',
      '<P>Please inform the',
      '<A href="mailto:' . Mail::Ezmanage::listmaster() . '">listmaster</A>' . "\n";
    }
    else {
      print join "\n", 
      "<P>There was a transient error fetching a list of all lists.",
      "<BR>The error message was:",
      "<PRE>",
      Mail::Ezmanage::error(),
      "</PRE>",
      'Please try again.' . "\n";
    }
    print about();
  }
  elsif (not grep { $_ eq $Q::name } @$lists) {
    print $query->header,
    $query->start_html(-title=>'There is no such list'), "\n",
    $query->h1('There is no such list'), "\n",
    '<P>[<A HREF="ezmanage-menu.cgi">back to menu</A>]', "\n",
    '<P>The list "<CODE>' . $Q::name . '</CODE>" does not exist.', "\n\n",
    select_list(),
    about();
  }
  else {
    ($Q::name) = ($Q::name =~ /^([a-z0-9:_-]+)$/i);
    print $query->header,
    $query->start_html(-title=>"Remove $Q::name"), "\n";
    
    if (not defined $Q::Remove) {
      undef $Q::Remove;
      print $query->h1("Are you sure you want to remove list $Q::name?"), "\n",
      '<P>[<A HREF="ezmanage-menu.cgi">back to menu</A>]', "\n",
      '<P>', $query->startform(),
      $query->hidden(-name=>'name', -default=>$Q::name),
      $query->submit(-name=>'Remove'),
      $query->endform(), "\n",
      about();
    }
    else {
      print $query->h1("Removing list $Q::name"), "\n",
      '<P>[<A HREF="ezmanage-menu.cgi">back to menu</A>]', "\n";
      if (Mail::Ezmanage::remove($Q::name)) {
	print "<P>Removal succesful.\n",
	"<A href=\"ezmanage-menu.cgi\">Go back to main menu.</A>\n";
      }
      else {
	if (Mail::Ezmanage::failure()) {
	  print join "\n", 
	  "<P>There was a fatal error while removing list $Q::name.",
	  '<BR>The error message was:',
	  '<PRE>',
	  Mail::Ezmanage::error(),
	  '</PRE>',
	  '<P>The list is now only partially removed - please inform the',
	  '<A href="mailto:' . Mail::Ezmanage::listmaster() . '">listmaster</A>' . "\n";
	}
	else {
	  print join "\n", 
	  "<P>There was a transient error while removing list $Q::name.",
	  "<BR>The error message was:",
	  "<PRE>",
	  Mail::Ezmanage::error(),
	  "</PRE>",
	  'The list is now only partially removed - please try again.' . "\n";
	}
      }
      print about();
    }
  }
}

main();

sub about() {
  my ($n, $v) = ' $Id: ezmanage-list-remove.cgi,v 1.1 2000/03/20 17:29:39 tv42 Exp $ ' =~ m{^.*?Id: (\S+) (\S+) .*};
  $v='0.0' unless defined $v;
  $n='unknown' unless defined $n;
  $n =~ s/,v$//g;
  return 
    "\n\n", $query->hr, "\n",
    '<SMALL>', "$n v$v, Copyright 1998 Tommi Virtanen, Havoc Consulting.", '</SMALL>', "\n",
    $query->end_html, "\n";
}
