#!/usr/bin/perl -wT
#
# $Id: ezmanage-list-new.cgi,v 1.2 2000/03/21 20:59:22 tv42 Exp $
#
# ezmanage-list-new.cgi - create a new mailing list
#
# Copyright (C) 1998-2000 Tommi Virtanen
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

ezmanage-list-new.cgi - create a new mailing list

=head1 SYNOPSIS

  Called by a WWW server as a CGI script.

=head1 DESCRIPTION

This script provides a WWW interface to create a new list.  Normally
it is called by F<ezmanage-menu.cgi>, but it may be called directly - in
that case it will display a form to enter group name to.

=head1 PARAMETERS

=over 4

=item name

Name of the moderator group to add.

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
my $name=$query->param('name');
$name =~ tr/./:/ if defined $name;

my $lists = Mail::Ezmanage::get_lists();

if (not defined $name) {
  print $query->header,
  $query->start_html(
		     -title=>'Create a new list',
		    ), "\n",
    $query->h1('Create a new list'), "\n",
    '<P>[<A HREF="ezmanage-menu.cgi">back to menu</A>]', "\n",
    '<P>Enter name for the new list:', "\n\n",
    '<BR>', $query->start_form(), 
    $query->textfield(-name=>'name'), ' ', $query->submit(-name=>'Create'),
    $query->endform(), "\n",
    about();
}
elsif ($name !~ /^[a-z0-9:_-]+$/i) {
  print $query->header,
  $query->start_html(
		     -title=>'List name was invalid',
		    ), "\n",
    $query->h1('List name was invalid'), "\n",
    '<P>[<A HREF="ezmanage-menu.cgi">back to menu</A>]', "\n",
    '<P>The name "<CODE>', $name, '</CODE>" you gave contains invalid characters or is empty.', "\n",
    '<P>Allowed characters: a-z, A-Z, and any of ".:_-"', "\n",
    
    '<P>Choose a new name for the list:', "\n\n",
    '<BR>', $query->start_form(), 
    $query->textfield(-name=>'name'), ' ', $query->submit(-name=>'Create'),
    $query->endform(), "\n",
    about();
}
elsif (not defined $lists) {
  print $query->header,
  $query->start_html(-title=>'Error while fetching list of all lists'), "\n",
  $query->h1('Error while fetching list of all lists'), "\n",
    '<P>[<A HREF="ezmanage-menu.cgi">back to menu</A>]', "\n";
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
elsif (grep { $_ eq $name } @$lists) {
  print $query->header,
  $query->start_html(
		     -title=>'List exists',
		    ), "\n",
    $query->h1('List exists'), "\n",
    '<P>[<A HREF="ezmanage-menu.cgi">back to menu</A>]', "\n",
    '<P>List "<CODE>', $name, '</CODE>" exists already.', "\n\n",
    
    '<P>Choose a new name for the list:', "\n\n",
    '<BR>', $query->start_form(), 
    $query->textfield(-name=>'name'), ' ', $query->submit(-name=>'Create'),
    $query->endform(), "\n",
    about();
}
else {
  ($name) = ($name =~ /^([a-z0-9:_-]+)$/i);
  if (Mail::Ezmanage::create($name)) {
    print $query->header,
    $query->start_html(
		       -title=>'List was created successfully',
		      ), "\n",
      $query->h1('List was created successfully'), "\n",
      '<P>[<A HREF="ezmanage-menu.cgi">back to menu</A>]', "\n",
      '<P>The list "<CODE>', $name, '</CODE>" was created.', "\n\n",
      
      '<P><A href="ezmanage-list-config.cgi?name=', $name, '">', 
      'Configure it', "</A>\n\n",
      about();
  }
  else {
    print $query->header,
    $query->start_html(
		       -title=>'List creation failed',
		      ), "\n",
      $query->h1('List creation failed'), "\n",
      '<P>[<A HREF="ezmanage-menu.cgi">back to menu</A>]', "\n",
      "<P>List <STRONG>$name</STRONG> could not be created.\n",
      '<BR>Error is <EM>', (Mail::Ezmanage::failure() ? 'fatal' : 'transient'), "</EM>, error message was:\n",
      "<BR><PRE>\n", Mail::Ezmanage::error(), "\n</PRE>\n\n",
      about();
  }
}

sub about() {
  my ($n, $v) = ' $Id: ezmanage-list-new.cgi,v 1.2 2000/03/21 20:59:22 tv42 Exp $ ' =~ m{^.*?Id: (\S+) (\S+) .*};
  $v='0.0' unless defined $v;
  $n='unknown' unless defined $n;
  $n =~ s/,v$//g;
  return 
    "\n\n", $query->hr, "\n",
    '<SMALL>', "$n v$v, Copyright 1998-2000 Tommi Virtanen, Havoc Consulting.", '</SMALL>', "\n",
    $query->end_html, "\n";
}
