#!/usr/bin/perl -wT
#
# $Id: ezmanage-list-subscribers.cgi,v 1.1 2000/03/20 17:29:39 tv42 Exp $
#
# ezmanage-list-subscribers.cgi - manage list subscribers
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

ezmanage-list-subscribers.cgi - manage list subscribers

=head1 SYNOPSIS

  Called by a WWW server as a CGI script.

=head1 DESCRIPTION

Modify the subscriber list of the selected list.

=head1 PARAMETERS

=over 4

=item name

Name of the list to modify. If not provided, display a menu to select list from.

=item user

Email address to add/delete/modify.

=item to

New email address for I<user>.

=item fullname

Full name of the user at email address I<user>.

=item confirm

If set, confirm adding/removing an address to the list by sending a
message to the address in question. Only if the user replies to the
message, and the cryptographical checksum matches, the action will be
taken.

=item Add

Add the address I<user> to the list I<name> and set I<user>'s full
name to be I<fullname>, if provided.

=item Remove

Remove the address I<user> from the list I<name>.

=item Change

Change the address I<user> to I<to>, and add I<fullname> as a full name for I<to>.

=item Use_full_name

Change I<user>'s full name to I<fullname>.

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
require Mail::Ezmanage::Fullnames;
require Mail::Ezmlm;

my $query=new CGI;
$query->import_names();

my $lists = Mail::Ezmanage::get_lists();

sub select_list() {
  return 
    "<P>Select the list you wish, either from the scrollable list\n",
    "or by typing it's name in the box:\n\n",
    '<P>', $query->startform(-method=>'GET'), 
    $query->textfield(-name=>'name'), ' ', $query->submit(-name=>'Select'), 
    $query->endform(), "\n",
    '<P>', $query->startform(-method=>'GET'),
    $query->scrolling_list('name', $lists, undef, 15),
    ' ', $query->submit(-name=>'Select'), 
    $query->endform(), "\n";
}

sub add($$;$;) {
  my ($user, $name, $confirm) = @_;
  if (defined $confirm) {
    return Mail::Ezmlm::subscribe_mail(Mail::Ezmanage::prettify('hp', $name), $user);
  } 
  else {
    return Mail::Ezmlm::subscribe($Mail::Ezmanage::EZLISTS . '/' . $name, $user);
  }
}

if (not defined $Q::name) {
  print $query->header,
  $query->start_html(-title=>'Select list to manage'), "\n",
  $query->h1('Select list to manage'), "\n",
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
  select_group(),
  about();
}
elsif (not defined $lists) {
  print $query->header,
  $query->start_html(-title=>'Error while fetching list of lists'), "\n",
  $query->h1('Error while fetching list of lists'), "\n",
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
  $query->start_html(-title=>'Subscriber list administration for list ', 
		     $Q::name), "\n",
  $query->h1('Subscriber list administration for list ', $Q::name), "\n",
  '<P>[<A HREF="ezmanage-menu.cgi">back to menu</A>]', "\n",  
  "<P><UL>\n";
  if (defined $Q::Remove) {
    undef $Q::Remove;
    if (remove_address($Q::user, $Q::name, $Q::confirm)) {
      $query->delete('user');
      $query->delete('fullname');
      undef $Q::user;
      undef $Q::fullname;
    }
  }
  elsif (defined $Q::Add) {
    undef $Q::Add;
    print "<LI>Handling addition of $Q::user: ";
    if (add($Q::user, $Q::name, $Q::confirm)) {
      print "ok.\n";
      if (defined $Q::fullname and $Q::fullname ne '') {
	print "<LI>Setting full name of $Q::user to be $Q::fullname: ";
	if (Mail::Ezmanage::Fullnames::set_name($Q::user, $Q::fullname)) {
	  print "ok.\n";
	}
	else {
	  print Mail::Ezmanage::Fullnames::failure() ? 'fatal' : 'transient',
	  " error: ", Mail::Ezmanage::Fullnames::error(), "\n";
	}
      }
    }
    else {
      print Mail::Ezmlm::failure() ? 'fatal' : 'transient',
      " error: ", Mail::Ezmlm::error(), "\n";
    }
  }
  elsif (defined $Q::Change) {
    undef $Q::Change;
    if (change_address($Q::name, $Q::user, $Q::to)) {
      $Q::user = $Q::to;
      $query->param('user', $Q::user);
      undef $Q::to;
      $query->delete('to');
    }
  }
  elsif (defined $Q::Use_full_name) {
    undef $Q::Use_full_name;
    my $r;
    if (defined $Q::fullname and $Q::fullname ne '') {
      print "<LI>Setting full name of $Q::user to be $Q::fullname: ";
      $r = Mail::Ezmanage::Fullnames::set_name($Q::user, $Q::fullname);
    }
    else {
      print "<LI>Removing full name of $Q::user: ";
      $r = Mail::Ezmanage::Fullnames::remove_name($Q::user);
    }
    
    if ($r) {
      print "ok.\n";
    }
    else {
      print Mail::Ezmanage::Fullnames::failure() ? 'fatal' : 'transient',
      " error: ", Mail::Ezmanage::Fullnames::error(), "\n";
    }
  }
  print "</UL>\n\n";

  if (defined $Q::user and (not defined $Q::fullname or $Q::fullname eq '')) {
    $Q::fullname=Mail::Ezmanage::Fullnames::get_name($Q::user);
    $query->param('fullname', $Q::fullname);
  }

  print $query->startform(-method=>'POST'), "\n",
  $query->hidden(-name=>'name', -default=>$Q::name), "\n",
  '<P>User: ', $query->textfield(-name=>'user'), "\n",
  '<BR>', $query->submit(-name=>'Add'), $query->submit(-name=>'Remove'), "\n",
  '<BR>', $query->checkbox(-name=>'confirm', 
			   -checked=>$Q::confirm, 
			   -label=>' Confirm action with user'), "\n",
  '<P>Change to: ', $query->textfield(-name=>'to'), "\n",
  '<BR>', $query->submit(-name=>'Change'), "\n",
  '<P>Full name (optional): ', 
  $query->textfield(-name=>'fullname'), "\n",
  '<BR>', $query->submit(-name=>'Use full name'), "\n\n",
  $query->endform(),
  $query->hr(), "\n",
  '<P><STRONG>User list in alphabetical order</STRONG>', "\n";

  $query->delete_all;
  $query->param('name', $Q::name);
  $query->param('user', $Q::user);
  print '<BR>', 
  $query->startform(-method=>'GET'), 
  $query->hidden(-name=>'name', -value=>$Q::name),
  $query->hidden(-name=>'user', -value=>$Q::user),
  $query->submit(-name=>'Refresh'),
  $query->endform(),
  "<UL>\n";

  my $s = Mail::Ezmlm::subscribers($Mail::Ezmanage::EZLISTS . '/' . $Q::name);
  if (defined $s) {
    if (@$s) {
      $query->param('name', $Q::name);
      foreach (sort @$s) {
	$query->param('user', $_);
	my $name = Mail::Ezmanage::Fullnames::get_name($_);
	print '  <LI><A href="', $query->self_url(), '">', $_, '</A>',
	defined $name ? " ($name)\n" : "\n"
	  or die "write to stdout failed; $!";
      }
    }
    else {
      print "  <LI>No subscribers.\n";
    }
  }
  else {
    print Mail::Ezmlm::failure() ? 'fatal' : 'transient',
    ' error while fetching list of subscribers: ', Mail::Ezmlm::error(), "\n";
  }

  print "</UL>\n",
  about();
}       

sub change_address($$$;) {
  my ($name, $user, $to) = @_;
  print "<LI>Handling change of $user to $to";
  if (not defined $to or $to eq '') {
    print ": field empty - not changed.\n";
    return undef;
  }
  print "\n  <UL>\n";

  my $fullname = Mail::Ezmanage::Fullnames::get_name($user);

  if (defined $fullname) {
    print '    <LI>Adding full name for new address: ';
    if (Mail::Ezmanage::Fullnames::set_name($to, $fullname)) {
      print "ok.\n";
    }
    else {
      print Mail::Ezmanage::Fullnames::failure() ? 'fatal' : 'transient',
      ' error: ', Mail::Ezmanage::Fullnames::error(), "\n",
      "  </UL>\n";
      return undef;
    }
  }
  
  print '    <LI>Adding new address: ';
  if (add($to, $name)) { print "ok.\n" }
  else {
    print Mail::Ezmlm::failure() ? 'fatal' : 'transient',
    ' error: ', Mail::Ezmlm::error(), "\n",
    "  </UL>\n";
    return undef;
  }

  print '    <LI>Removing old address: ';
  if (Mail::Ezmlm::unsubscribe($Mail::Ezmanage::EZLISTS . '/' . $name, $user)) {
    print "ok.\n";
  }
  else {
    print Mail::Ezmlm::failure() ? 'fatal' : 'transient',
    " error in the middle - please remove $user manually: ", 
    Mail::Ezmlm::error(), "\n",
    "  </UL>\n";
    return undef;
  }

  # don't remove the old full name - other lists may still have the old email
  # address as a subscriber, and we want to still have the full name available
  # for them
  print "  </UL>\n";
  return 1;
}

sub remove_address($$;$;) {
  my ($user, $name, $confirm) = @_;
  print "<LI>Handling removal of $Q::user",
  "  <UL>\n",
  "    <LI>Removing subscription information: ";

  my $r = defined $confirm
    ? Mail::Ezmlm::unsubscribe_mail(Mail::Ezmanage::prettify('hp', $name), $user)
      : Mail::Ezmlm::unsubscribe($Mail::Ezmanage::EZLISTS . '/' . $name, $user);
  
  if ($r) {
    print "ok.\n";
  }
  else {
    print Mail::Ezmlm::failure() ? 'fatal' : 'transient', " error: ",
    Mail::Ezmlm::error(), "\n",
    "  </UL>\n";
    return undef;
  }

  if (not $confirm) {
    print "    <LI>Removing full name: ";
    if (Mail::Ezmanage::Fullnames::remove_name($user)) {
      print "ok.\n";
    }
    else {
      print Mail::Ezmanage::Fullnames::failure() ? 'fatal' : 'transient',
      " error: ", Mail::Ezmanage::Fullnames::error(), "\n",
      "<BR>Note: this will be automatically corrected\n",
      "in the next maintenance run.\n";
    }
  }
  print "  </UL>\n";
  return 1;
}

sub about() {
  my ($n, $v) = ' $Id: ezmanage-list-subscribers.cgi,v 1.1 2000/03/20 17:29:39 tv42 Exp $ ' =~ m{^.*?Id: (\S+) (\S+) .*};
  $v='0.0' unless defined $v;
  $n='unknown' unless defined $n;
  $n =~ s/,v$//g;
  return 
    "\n\n", $query->hr, "\n",
    '<SMALL>', "$n v$v, Copyright 1998 Tommi Virtanen, Havoc Consulting.", '</SMALL>', "\n",
    $query->end_html, "\n";
}
