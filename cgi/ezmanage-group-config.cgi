#!/usr/bin/perl -wT
#
# $Id: ezmanage-group-config.cgi,v 1.1 2000/03/20 17:29:38 tv42 Exp $
#
# ezmanage-group-config.cgi - configure a moderator group
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

ezmanage-group-config.cgi - configure a moderator group

=head1 SYNOPSIS

  Called by a WWW server as a CGI script.

=head1 DESCRIPTION

This script provides a WWW interface to configuring a moderator group.
Normally it is called by F<ezmanage-menu.cgi>, but it may be called directly
- in that case it will display a menu from which choose the moderator group.

To remove a moderator group, first remove all the moderators,

=head1 PARAMETERS

=over 4

=item name

Name of the moderator group to modify. If not present, a menu will be displayed.

=item add

A string of newline-separated email addresses to add to the moderator group I<name>.

=item del

A list of email addresses to remove from the moderator group I<name>.

=item remove

If 't', the moderator group I<name> will be removed.

=back

Name must be speficied for any of I<add>, I<del> or I<remove>. Only
one of I<add>, I<del> or I<remove> may be specified at once.

=head1 AUTHOR

Tommi Virtanen, Havoc Consulting (tv@havoc.fi)

=cut

############################################################################

use strict;
use lib '/usr/lib/ezmanage/lib';
use CGI::Carp; # qw(fatalsToBrowser);
use CGI;
require Mail::Ezmanage::Mod;

my $query=new CGI;
my $name=$query->param('name');

my $groups = Mail::Ezmanage::Mod::get_groups();

sub select_group() {
  return 
    "<P>Select the moderator group you wish, either from the scrollable list\n",
    "or by typing it's name in the box:\n\n",
    '<P>', $query->start_form(), 
    $query->textfield(-name=>'name'), ' ', $query->submit(-name=>'Select'), 
    $query->endform(), "\n",
    '<P>', $query->start_form(),
    $query->scrolling_list('name', $groups, undef, 10),
    ' ', $query->submit(-name=>'Select'), 
    $query->endform(), "\n";
}

if (not defined $name) {
  print $query->header,
  $query->start_html(
		     -title=>'Select moderator group to configure',
		    ), "\n",
    $query->h1('Select moderator group to configure'), "\n",
    '<P>[<A HREF="ezmanage-menu.cgi">back to menu</A>]', "\n",
    select_group(),
    about();
}
elsif ($name !~ /^[a-z0-9:_-]+$/i) {
  print $query->header,
  $query->start_html(
		     -title=>'Invalid moderator group name',
		    ), "\n",
    $query->h1('Invalid moderator group name'), "\n",
    '<P>[<A HREF="ezmanage-menu.cgi">back to menu</A>]', "\n",
    '<P>The moderator group name contains invalid characters.', "\n",
    select_group(),
    about();
}
elsif (not defined $groups) {
  print $query->header,
  $query->start_html(-title=>'Error while fetching list of moderator groups'), "\n",
  $query->h1('Error while fetching list of moderator groups'), "\n",
    '<P>[<A HREF="ezmanage-menu.cgi">back to menu</A>]', "\n";
  if (Mail::Ezmanage::Mod::failure()) {
    print join "\n", 
    '<P>There was a fatal error fetching a list of moderator groups.',
    '<BR>The error message was:',
    '<PRE>',
    Mail::Ezmanage::Mod::error(),
    '</PRE>',
    '<P>Please inform the',
    '<A href="mailto:' . Mail::Ezmanage::listmaster() . '">listmaster</A>' . "\n";
  }
  else {
    print join "\n", 
    "<P>There was a transient error fetching a list of moderator groups.",
    "<BR>The error message was:",
    "<PRE>",
    Mail::Ezmanage::Mod::error(),
    "</PRE>",
    'Please try again.' . "\n";
  }
  print about();
}
elsif (not grep { $_ eq $name } @$groups) {
  print $query->header,
  $query->start_html(-title=>'There is no such moderator group'), "\n",
  $query->h1('There is no such moderator group'), "\n",
  '<P>[<A HREF="ezmanage-menu.cgi">back to menu</A>]', "\n",
  '<P>Moderator group "<CODE>' . $name . '</CODE>" does not exist.', "\n\n",
  select_group(),
  about();
}
else {
  print $query->header,
  $query->start_html(-title=>'Moderator group ', $name, ' configuration'), "\n";
  
  if (defined $query->param('add')) { # add
    print $query->h1('Handling requested additions'), "\n<UL>\n";
    foreach (split "\n", $query->param('add')) {
      print "  <LI><STRONG>$_</STRONG>: ";
      if (Mail::Ezmanage::Mod::add($name, $_)) {
	print "ok.\n";
      }
      else {
	print Mail::Ezmanage::Mod::failure() ? 'fatal' : 'transient',
	' error; ', Mail::Ezmanage::Mod::error(), ".\n";
      }
    }
    print "\n</UL>\n";
  }
  elsif (defined $query->param('del')) { # del
    print $query->h1('Handling requested removals'), "\n<UL>\n";
    foreach ($query->param('del')) {
      print "  <LI><STRONG>$_</STRONG>: ";
      if (Mail::Ezmanage::Mod::del($name, $_)) {
	print "ok.\n",
      }
      else {
	print Mail::Ezmanage::Mod::failure() ? 'fatal' : 'transient',
	' error; ', Mail::Ezmanage::Mod::error(), ".\n";
      }
    }
    print "\n</UL>\n";
  }
  elsif (defined $query->param('remove')
	 and $query->param('remove') eq 't') {
    print "<P>Removing moderator group $name: ";
    ($name) = ($name =~ /^([a-z0-9:_-]+)$/i);
    if (Mail::Ezmanage::Mod::remove($name)) {
      print "ok.\n",
      '<P><A href="', $query->url(), '">Go back</A>', "\n",
      $query->end_html(), "\n";
      exit 0;	
    }
    else {
      print Mail::Ezmanage::Mod::failure() ? 'fatal' : 'transient',
      ' error; ', Mail::Ezmanage::Mod::error(), ".\n";
    }
  }
  
  $query->delete_all();
  print $query->h1('Configure moderator group ' . $name), "\n",
  '<P>[<A HREF="ezmanage-menu.cgi">back to menu</A>]', "\n",
  '<P>Enter email addresses to add as moderators, one per line:', "\n",
  '<BR>', $query->startform(),
  $query->hidden(-name=>'name', -default=>$name),
  $query->textarea(-name=>'add', -rows=>5, -columns=>30), "\n",
  '<P>', $query->submit(-name=>'Ok'),
  $query->reset(-name=>'Reset'), "\n", 
  $query->endform, "\n<HR>\n\n";
  
  my $mods = Mail::Ezmanage::Mod::list($name);
  if (not defined $mods) {
    if (Mail::Ezmanage::Mod::failure()) {
      print join "\n", 
      "<P>There was a fatal error fetching a list of moderators in group $name.\n",
      '<BR>The error message was:',
      '<PRE>',
      Mail::Ezmanage::Mod::error(),
      '</PRE>',
      '<P>Please inform the',
      '<A href="mailto:' . Mail::Ezmanage::listmaster() . '">listmaster</A>' . "\n";
    }
    else {
      print join "\n", 
      "<P>There was a transient error fetching a list of moderator groups.",
      "<BR>The error message was:",
      "<PRE>",
      Mail::Ezmanage::Mod::error(),
      "</PRE>",
      'Please try again.' . "\n";
    }
  }
  elsif (@$mods) {
    print $query->startform(),
    '<P>Select email addresses to remove from the list of moderators', "\n",
    $query->hidden(-name=>'name', -default=>$name),
    '<BR>', $query->checkbox_group(-name=>'del',
				   -value=>$mods,
				   -linebreak=>1), "\n\n",
    '<P>', $query->submit(-name=>'Ok'),
    $query->reset(-name=>'Reset'), "\n", 
    $query->endform, "\n";
  }
  else { 
    print '<P>', 'The moderator group is empty.', "\n",
    $query->startform(),
    $query->hidden(-name=>'name', -default=>$name),
    $query->hidden(-name=>'remove', -default=>'t'), "\n",
    '<P>Press ', $query->submit(-name=>'Remove'), ' to remove it.', "\n", 
    $query->endform;
  }
  print about();
}

sub about() {
  my ($n, $v) = ' $Id: ezmanage-group-config.cgi,v 1.1 2000/03/20 17:29:38 tv42 Exp $ ' =~ m{^.*?Id: (\S+) (\S+) .*};
  $v='0.0' unless defined $v;
  $n='unknown' unless defined $n;
  $n =~ s/,v$//g;
  return 
    "\n\n", $query->hr, "\n",
    '<SMALL>', "$n v$v, Copyright 1998 Tommi Virtanen, Havoc Consulting.", '</SMALL>', "\n",
    $query->end_html, "\n";
}
