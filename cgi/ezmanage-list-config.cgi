#!/usr/bin/perl -wT
#
# $Id: ezmanage-list-config.cgi,v 1.2 2000/03/21 20:59:22 tv42 Exp $
#
# ezmanage-list-config.cgi - configure a mailing list
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

ezmanage-list-config.cgi - configure a mailing list

=head1 SYNOPSIS

  Called by a WWW server as a CGI script.

=head1 DESCRIPTION

This script provides a WWW interface to configuring a mailing list.
Normally it is called by F<ezmanage-menu.cgi>, but it may be called
directly - in that case it will display a menu from which choose the
list.

=head1 PARAMETERS

=over 4

=item name

Name of the list to configure. If not present, a menu will be displayed.

=item description

A one-line description for list I<name>. See I<save_description>.

=item maxsize

Maximum size of a message to allow through. Messages with more than
I<maxsize> bytes in the body will be bounced with a rejection notice.

=item moderation

One of no, sub, submod, mod.

=over 4

=item no

No message moderation is to be done.

=item sub

If the messages envelope sender is a subscriber of the list, the
message is allowed through, otherwise it is rejected.

=item submod

Same as I<sub>, but instead of rejecting the message is sent for moderation.

=item mod

All messages are sent for moderation.

=back

=item moderators

Name of the moderator group that will moderate the list I<name>.

=item publicsubs

If 'y', everyone will be allowed to subscribe/unsubscribe from the
list I<name>.  If 'n', subscription/unsubscription must be approved by
a subscription moderator (see below).

=item submods

Name of the moderator group that will handle subscription moderation
for list I<name>.

=item save_description
=item save_misc
=item save_moderation
=item save_subscription
=item save_all

One of these must be present to actually save the configuration
variables described above. With I<save_description> the list
description will be saved, etc. I<save_moderation> will save both
I<moderators> and I<moderation>, I<save_subscription> will save
I<publicsubs> and I<submods>, and I<save_all> will save everything.

=item remove

If specified, display a confirmation dialog, and set positive
responses to go to F<ezmanage-list-remove.cgi>.

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
require Mail::Ezmanage;
require Mail::Ezmlm::Maintenance;

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

sub get_modsettings($$;) { # TODO this bypasses the API..
  my ($name, $config) = @_;
  
  my $m = '';
  $m .= 'sub' if $config =~ /u/;
  $m .= 'mod' if $config =~ /m/;
  $m = 'no' if $m eq '';
  
  my $s = 'y';
  $s = 'n' if $config =~ /s/;

  return [$m, $s];
}

sub fetch_defaults($;$) { # TODO improve error returns to differentiate source of error
  my ($name, $errref) = @_;
  my %d;
  my $dummy;
  $errref = \$dummy unless defined $errref;
  $d{maxsize} = Mail::Ezmlm::Maintenance::get_msgsize($Mail::Ezmanage::EZLISTS . '/' . $name);
  defined $d{maxsize}
  or $$errref=(Mail::Ezmlm::Maintenance::failure() ? 'fatal' : 'transient')
    . ' error while fetching max message size; ' . Mail::Ezmlm::Maintenance::error(),
    return undef;
  my $config = Mail::Ezmanage::getfirstline($Mail::Ezmanage::EZLISTS
					    . '/' . $name . '/config');
  defined $config or
    $$errref='transient error while fetching list config',
    return undef;
  $d{guardarchive} = $config =~ /g/;
  my $m = get_modsettings($name, $config);
  defined $m 
    or $$errref='get_modsettings failed',
    return undef;
  ($d{moderation}, $d{publicsubs}) = @$m;
  defined $d{publicsubs} or $$errref='this cannot happen', return undef;
  defined $d{moderation} or $$errref='this cannot happen', return undef;
  $d{moderators} = Mail::Ezmanage::Mod::get_moderatorgroup($name);
  defined $d{moderators} 
  or $$errref=(Mail::Ezmanage::Mod::failure() ? 'fatal' : 'transient')
    . ' error while fetching moderator group; ' . Mail::Ezmanage::Mod::error(),
    return undef;
  $d{submods} = Mail::Ezmanage::Mod::get_submoderatorgroup($name);
  defined $d{submods}
  or $$errref=(Mail::Ezmanage::Mod::failure() ? 'fatal' : 'transient')
    . ' error while fetching subscription moderator group; ' . Mail::Ezmanage::Mod::error(),
    return undef;
  $d{description} = Mail::Ezmanage::get_list_description($name);
  defined $d{description}
  or $$errref=(Mail::Ezmanage::failure() ? 'fatal' : 'transient')
    . ' error while fetching list description; ' . Mail::Ezmanage::error(),
    return undef;
  undef $$errref;
  return \%d;
}

sub main() {
  my $mods = Mail::Ezmanage::Mod::get_groups();
  if (not defined $Q::name or $Q::name eq '') {
    print $query->header,
    $query->start_html(-title=>'Select list to configure'), "\n",
    $query->h1('Select list to configure'), "\n",
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
  elsif (not defined $mods) {
    print $query->header,
    $query->start_html(-title=>'Error while fetching list of moderator groups'), "\n",
    $query->h1('Error while fetching list of moderator groups'), "\n",
    '<P>[<A HREF="ezmanage-menu.cgi">back to menu</A>]', "\n";
    if (Mail::Ezmanage::failure()) {
      print join "\n", 
      '<P>There was a fatal error fetching a list of all moderator groups.',
      '<BR>The error message was:',
    '<PRE>',
      Mail::Ezmanage::error(),
      '</PRE>',
      '<P>Please inform the',
      '<A href="mailto:' . Mail::Ezmanage::listmaster() . '">listmaster</A>' . "\n";
    }
    else {
      print join "\n", 
      "<P>There was a transient error fetching a list of all moderator groups.",
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
    $query->start_html(-title=>"List $Q::name configuration"), "\n";
    
    if (defined $Q::remove) {
      undef $Q::remove;
      print "<H1>Are you sure you want to remove list $Q::name?</H1>\n";

      print '<P>', $query->startform(-action=>'ezmanage-list-remove.cgi'),
      $query->hidden(-name=>'name', -default=>$Q::name),
      $query->submit(-name=>'Remove'),
      $query->endform(), "\n";

      print $query->startform(-method=>'GET'),
      $query->hidden(-name=>'name', -default=>$Q::name),
      $query->submit(-name=>'Cancel'),
      $query->endform(), "\n",
      about();
      exit 0;
    }

    print "<UL>\n";
    if (defined $Q::save_description or defined $Q::save_all) {
      undef $Q::save_description;
      $Q::description =~ s/^\s+//g;
      $Q::description =~ s/\s+$//g;
      print "  <LI>Saving description: ";
      if (Mail::Ezmanage::set_list_description($Q::name, $Q::description)) {
	print "ok.\n";
      }
      else {
	print Mail::Ezmanage::failure() ? 'Fatal' : 'Transient',
	' error: ', Mail::Ezmanage::error(), "\n";
      }
    }

    if (defined $Q::save_misc or defined $Q::save_all) {
      my $dir = $Mail::Ezmanage::EZLISTS . '/' . $Q::name;
      
      $Q::maxsize =~ s/^\s+//g;
      $Q::maxsize =~ s/\s+$//g;
      print "  <LI>Saving maxsize: ";
      if ($Q::maxsize =~ /^\d+(:\d+)?$/) {
	my $r = $Q::maxsize == 0
	  ? Mail::Ezmlm::Maintenance::remove_msgsize($dir)
	    : Mail::Ezmlm::Maintenance::set_msgsize($dir, $Q::maxsize);
	if ($r) {
	  print "ok.\n";
	}
	else {
	  print Mail::Ezmlm::Maintenance::failure() ? 'Fatal' : 'Transient',
	  ' error: ', Mail::Ezmlm::Maintenance::error(), "\n";
	}
      }
      else {
	print "not a number - not saved.\n";
      }
    }

    if (defined $Q::save_misc or defined $Q::save_all) {
      print " <LI>Saving archive guarding: ";
      if (Mail::Ezmlm::Maintenance::edit_list($Mail::Ezmanage::EZLISTS
					      . '/' . $Q::name,
					      {
					       guardarchive=>(defined
							      $Q::guardarchive and
							      $Q::guardarchive ne '')
					       ? 1 : 0,
					      }
					     )) {
	print $Q::guardarchive ? "on" : "off", ".\n";
      }
      else {
	print Mail::Ezmlm::Maintenance::failure() ? 'Fatal' : 'Transient',
	' error: ', Mail::Ezmlm::Maintenance::error(), "\n";
      }
    }

    if (defined $Q::save_moderation or defined $Q::save_all) {
      undef $Q::save_moderation;
      print "  <LI>Saving moderation settings\n",
      "  <UL>\n";

      defined $mods or die "This cannot happen, exiting";

      my $moddisable_ok;
      if ($Q::moderation eq 'no') {
	print "    <LI>Moderation: ";
	if (Mail::Ezmlm::Maintenance::edit_list($Mail::Ezmanage::EZLISTS
						. '/' . $Q::name,
						{
						 subscribersonly=>0,
						 moderated=>0,
						}
					       )) {
	  print "disabled.\n";
	  $moddisable_ok++;
	}
	else {
	  print Mail::Ezmlm::Maintenance::failure() ? 'Fatal' : 'Transient',
	  ' error: ', Mail::Ezmlm::Maintenance::error(), "\n";
	}
      }

      my $modgroup_ok;
      print "    <LI>Moderator group: ";
      if ($Q::moderation eq 'no' and not $moddisable_ok) {
	print "skipped.\n";
      }
      else {
	if (grep {$_ eq $Q::moderators} @$mods) {
	  if (Mail::Ezmanage::Mod::set_moderatorgroup($Q::name, $Q::moderators)) {
	    print "ok.\n";
	    $modgroup_ok++;
	  }
	  else {
	    print Mail::Ezmanage::Mod::failure() ? 'Fatal' : 'Transient',
	    ' error: ', Mail::Ezmanage::Mod::error(), "\n";
	  }
	}
	else {
	  print "invalid setting - not saved.\n";
	}
      }
      
      if ($Q::moderation ne 'no') {
	print "    <LI>Moderation: ";
	if (not $modgroup_ok) {
	  print "skipped.\n";
	}
	elsif (grep {$Q::moderation eq $_} qw(no sub submod mod)) {
	  my %f;
	  for ($Q::moderation) {
	    /sub/ and $f{subscribersonly}=1 or $f{subscribersonly}=0;
	    /mod/ and $f{moderated}=1 or $f{moderated}=0;
	  }
	  if (Mail::Ezmlm::Maintenance::edit_list($Mail::Ezmanage::EZLISTS
						  . '/' . $Q::name,
						  \%f)) {
	    print "ok.\n";
	  }
	  else {
	    print Mail::Ezmlm::Maintenance::failure() ? 'Fatal' : 'Transient',
	    ' error: ', Mail::Ezmlm::Maintenance::error(), "\n";
	  }
	}
	else {
	  print "invalid setting - not saved.\n";
	}
      }
      
      print "  </UL>\n";
    }
    
    if (defined $Q::save_subscription or defined $Q::save_all) {
      undef $Q::save_subscription;
      print "  <LI>Saving subscription settings\n",
      "  <UL>\n";

      my $submod_ok;
      print "    <LI>Subscription moderators: ";
      defined $mods or die "This cannot happen, exiting";
      if ($Q::publicsubs eq 'n') {
	if (grep {$_ eq $Q::submods} @$mods) {
	  if (Mail::Ezmanage::Mod::set_submoderatorgroup($Q::name, $Q::submods)) {
	    print "ok.\n";
	    $submod_ok++;
	  }
	  else {
	    print Mail::Ezmanage::Mod::failure() ? 'Fatal' : 'Transient',
	    ' error: ', Mail::Ezmanage::Mod::error(), "\n";
	  }
	}
	else {
	  print "invalid setting - not saved.\n";
	}
      }
      else {
	print "subscriptions are public - not saved.\n";
	$submod_ok++;
      }

      print "    <LI>Public subscriptions: ";
      if (not $submod_ok) {
	print "skipped.\n";
      }
      else {
	my $r;
	if ($Q::publicsubs eq 'n') { $r=1 }
	elsif ($Q::publicsubs eq 'y') { $r=0 }
	if (defined $r) {
	  if (Mail::Ezmlm::Maintenance::edit_list($Mail::Ezmanage::EZLISTS . '/' . $Q::name,
						  {submoderated=>$r})) {
	    print "ok.\n";
	  }
	  else {
	    print Mail::Ezmlm::Maintenance::failure() ? 'Fatal' : 'Transient',
	    ' error: ', Mail::Ezmlm::Maintenance::error(), "\n";
	  }
	}
	else {
	  print "invalid setting - not saved.\n";
	}
      }
    }
    print "</UL>\n";

    my $err;
    my $defaults = fetch_defaults($Q::name, \$err);
    if (not defined $defaults) {
      print $query->h1('Error while fetching current configuration for list ' . $Q::name), "\n",
      '<P>[<A HREF="ezmanage-menu.cgi">back to menu</A>]', "\n",
      print '<P>Error message is: ', $err, "\n" if defined $err;
      print '<P>Please try again.', "\n\n",
      select_list(),
      about();
    }
    else {
      print $query->h1('Configure list ' . $Q::name), "\n",
      '<P>[<A HREF="ezmanage-menu.cgi">back to menu</A>]', "\n",
      $query->startform(-action=>'ezmanage-list-subscribers.cgi', -method=>'GET'),
      $query->hidden(-name=>'name', -default=>$Q::name),
      $query->submit(-value=>'Administer subscribers'),
      $query->endform(),
      $query->startform(),
      $query->hidden(-name=>'name', -default=>$Q::name),
      '<P>List description: ',
      $query->textfield(-name=>'description',
			-default=>$defaults->{description}
		       ),
      $query->submit(-name=>'save_description',
		     -value=>'Save'),
      $query->hr(),
      '<P>Maximum size of messages in bytes (0 for no limit): ',
      $query->textfield(-name=>'maxsize',
			-default=>$defaults->{maxsize}
		       ),
      $query->hr(),
      '<P>',
      $defaults->{guardarchive} ?
	$query->checkbox(-name=>'guardarchive',
			 -checked=>'checked',
			 -label=>'Guard message archive from non-subscribers')
	  : $query->checkbox(-name=>'guardarchive',
			     -label=>'Guard message archive from non-subscribers'),
      '<P>',$query->submit(-name=>'save_misc', -value=>'Save'),
      $query->hr(),
      '<P><STRONG>Moderation</STRONG>', "\n",
      '<P>Message posting allowed for:', "\n",
      '<BR>', $query->radio_group(-name=>'moderation',
				  '-values'=>['no', 'sub', 'submod', 'mod'],
				  -default=>$defaults->{moderation},
				  -linebreak=>'true',
				  -labels=>{
					    'no' => 'All',
					    'sub' => 'Subscribers',
					    'submod' => 'Non-subscriber\'s posts moderated',
					    'mod' => 'All moderated',
					   }), "\n",
      '<P>Moderators for this list:', "\n";
      defined $mods or die "This cannot happen, exiting";
      print $query->scrolling_list(-name=>'moderators',
				   '-values'=>$mods,
				   -default=>$defaults->{moderators},
				   -size=>1,
				  );
      print '<P>', $query->submit(-name=>'save_moderation',
				  -value=>'Save'), "\n\n",
      $query->hr(), "\n",
      '<P><STRONG>Subscription</STRONG>', "\n",
      '<P>Subscription allowed:', "\n",
      '<BR>', $query->radio_group(-name=>'publicsubs',
				  '-values'=>['y', 'n'],
				  -default=>$defaults->{publicsubs},
				  -linebreak=>'true',
				  -labels=>{
					    'y' => 'For anyone',
					    'n' => 'Only after moderation',
					   }), "\n",
      '<P>Subscription moderators:', "\n";
      defined $mods or die "This cannot happen, exiting";
      print $query->scrolling_list(-name=>'submods',
				   '-values'=>$mods,
				   -default=>$defaults->{submods},
				   -size=>1,
				  );
      print '<P>', $query->submit(-name=>'save_subscription',
				  -value=>'Save'), "\n\n",
      $query->hr(), "\n",
      $query->submit(-name=>'save_all', -value=>'Save All'),
      $query->submit(-name=>'remove', -value=>'Remove this list'),
      $query->endform,
      about();
    }
  }       
}

main();

sub about() {
  my ($n, $v) = ' $Id: ezmanage-list-config.cgi,v 1.2 2000/03/21 20:59:22 tv42 Exp $ ' =~ m{^.*?Id: (\S+) (\S+) .*};
  $v='0.0' unless defined $v;
  $n='unknown' unless defined $n;
  $n =~ s/,v$//g;
  return 
    "\n\n", $query->hr, "\n",
    '<SMALL>', "$n v$v, Copyright 1998-2000 Tommi Virtanen, Havoc Consulting.", '</SMALL>', "\n",
    $query->end_html, "\n";
}
