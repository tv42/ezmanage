#
# $Id: Mod.pm,v 1.1 2000/03/20 17:29:39 tv42 Exp $
#
# Module Mail::Ezmanage::Mod - a library to manipulate multiple Ezmlm mailing lists
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

package Mail::Ezmanage::Mod;

sub Version { $VERSION; }
$VERSION = sprintf("%d.%02d", q$Revision: 1.1 $ =~ /(\d+)\.(\d+)/);

=head1 NAME

Mail::Ezmanage::Mod - a library to manipulate multiple Ezmlm mailing lists

=head1 SYNOPSIS

  use Mail::Ezmanage::Mod;
  # the rest is too complicated for a synopsis; keep reading

=head1 ABSTRACT

This module provides a backend for the B<ezmanage> mailing list management system.

=head1 TODO

This interface is currently to be considered for internal use only. It
has not yet stabilized enough to warrant publically-usable documentation.

=cut

require Exporter;
@ISA = qw(Exporter);

@EXPORT = qw(); #TODO

use strict;
use Mail::Ezmanage; # has to be use so that our BEGIN {} can access variables
require Mail::Ezmlm;
require Mail::Ezmlm::Maintenance;
use Mail::Ezmanage;

############################################################################

$Mail::Ezmanage::Mod::ERROR=''; # will contain an explanation of last error. Set when routines return undef.
$Mail::Ezmanage::Mod::ERROR_FAIL=0; # this will be 1 if the error is permanent, and 1 on soft errors.

############################################################################

sub err(@) {
  $Mail::Ezmanage::Mod::ERROR = "@_";
  $Mail::Ezmanage::Mod::ERROR_FAIL = 0;
  return undef;
}

sub fail(@) {
  $Mail::Ezmanage::Mod::ERROR = "@_";
  $Mail::Ezmanage::Mod::ERROR_FAIL = 1;
  return undef;
}

sub error() { $Mail::Ezmanage::Mod::ERROR }
sub failure() { $Mail::Ezmanage::Mod::ERROR_FAIL }

############################################################################

BEGIN {
  defined $Mail::Ezmanage::EZMANAGEDIR or die 'EZMANAGEDIR not defined, exiting';
  $Mail::Ezmanage::Mod::EZMODS = $ENV{EZMODS} || $Mail::Ezmanage::EZMANAGEDIR . '/mods';
}

sub dir_to_modgroup($;) {
  my ($dir) = @_;
  if ($dir =~ s{^$Mail::Ezmanage::Mod::EZMODS/}{}g) { return $dir }
  elsif ($dir eq '') { return 'default' } # silently change local default to global default
  else { return fail 'dir does not begin with modgroup base dir, and is not empty' }
}

sub modgroup_to_dir($;) { return $Mail::Ezmanage::Mod::EZMODS . '/' . $_[0] }

############################################################################

sub get_groups() {
  my $r = Mail::Ezmanage::read_dir {-d} $Mail::Ezmanage::Mod::EZMODS;
  return $r if defined $r;
  $Mail::Ezmanage::Mod::ERROR_FAIL = $Mail::Ezmanage::ERROR_FAIL;
  $Mail::Ezmanage::Mod::ERROR = 'read_dir said; ' . $Mail::Ezmanage::ERROR;
  return undef; # pass the error along
}

sub list($) {
  my ($name) = @_;
  my $r = Mail::Ezmlm::subscribers($Mail::Ezmanage::Mod::EZMODS . '/' . $name);
  return $r if defined $r;
  $Mail::Ezmanage::Mod::ERROR_FAIL = $Mail::Ezmlm::ERROR_FAIL;
  $Mail::Ezmanage::Mod::ERROR = 'subscribers said; ' . $Mail::Ezmlm::ERROR;
  return undef; # pass the error along
}

sub add($@) {
  my ($name) = shift;
  my $r = Mail::Ezmlm::subscribe($Mail::Ezmanage::Mod::EZMODS . '/' . $name, @_);
  return $r if defined $r; # return success if succesful
  $Mail::Ezmanage::Mod::ERROR_FAIL = $Mail::Ezmlm::ERROR_FAIL;
  $Mail::Ezmanage::Mod::ERROR = 'subscribe said; ' . $Mail::Ezmlm::ERROR;
  return undef; # pass the error along
}

sub del($@) {
  my ($name) = shift;
  return fail 'Cannot remove listmaster from the default moderator group'
    if $name eq 'default' and grep {$_ eq Mail::Ezmanage::listmaster()} @_;
  my $r = Mail::Ezmlm::unsubscribe($Mail::Ezmanage::Mod::EZMODS . '/' . $name, @_);
  return $r if defined $r; # return success if succesful
  # pass the error along
  if ($Mail::Ezmlm::ERROR_FAIL) { return fail "Mail::Ezmlm::unsubscribe said; $Mail::Ezmanage::ERROR" }
  else { return err "Mail::Ezmlm::unsubscribe said; $Mail::Ezmanage::ERROR" }
}

sub create($;) {
  my ($name) = @_;
  if (mkdir $Mail::Ezmanage::Mod::EZMODS . '/' . $name, 0755) {
    if (mkdir $Mail::Ezmanage::Mod::EZMODS . '/' . $name . '/subscribers', 0755) {
      return 1;
    }
    else {
      $Mail::Ezmanage::Mod::ERROR = "mkdir said; $!";
      rmdir $Mail::Ezmanage::Mod::EZMODS . '/' . $name; # clean up
    }
  }
  else {
    $Mail::Ezmanage::Mod::ERROR = "mkdir said; $!";
  }
  
  $Mail::Ezmanage::Mod::ERROR_FAIL = 0;
  return undef;
}

sub remove($;) {
  my ($name) = @_;
  return fail 'Cannot remove the default moderator group'
    if $name eq 'default';

  my $err = not_in_use($name);
  return undef unless defined $err; # pass the error along

  rename $Mail::Ezmanage::Mod::EZMODS . '/' . $name, $Mail::Ezmanage::Mod::EZMODS . '/.remove.' . $name
    or return err "rename moderator group $name to .remove.$name failed; $!";
  unlink $Mail::Ezmanage::Mod::EZMODS . '/.remove.' . $name . '/lock'; # ignore errors so missing files won't cause it to bomb out
  unlink $Mail::Ezmanage::Mod::EZMODS . '/.remove.' . $name . '/Log'; # ignore errors
  foreach (ord '@' .. ord 't') {
    unlink $Mail::Ezmanage::Mod::EZMODS . '/.remove.' . $name . '/subscribers/' . chr $_; # ignore errors
  }
  rmdir $Mail::Ezmanage::Mod::EZMODS . '/.remove.' . $name . '/subscribers'
    or return err "removal of ${name}'s subscribers failed; $!";
  rmdir $Mail::Ezmanage::Mod::EZMODS . '/.remove.' . $name
    or return fail "moderator group $name could not be removed";
}

sub not_in_use($;) {
  my ($group) = @_;
  my $lists = Mail::Ezmanage::get_lists();
  return err "cannot get lists; $Mail::Ezmanage::Mod::ERROR" unless defined $lists;
  my $tmp;
  foreach my $l (@$lists) {
    $tmp = get_moderatorgroup($l);
    defined $tmp or return undef; # pass the error along
    return fail "moderator group $group is in use for mailing list $l - cannot remove"
      if $tmp eq $group;

    $tmp = get_submoderatorgroup($l);    
    defined $tmp or return undef; # pass the error along
    return fail "moderator group $group is in use for subscription moderation "
    . "of mailing list $l - cannot remove"
      if $tmp eq $group;
  }
  return 1;
}

sub get_moderatorgroup($;) {
  my ($list) = @_;
  my $h = Mail::Ezmlm::Maintenance::get_config($Mail::Ezmanage::EZLISTS . '/' . $list);
  if (not defined $h) {
    $Mail::Ezmanage::Mod::ERROR = $Mail::Ezmlm::Maintenance::ERROR;
    $Mail::Ezmanage::Mod::ERROR_FAIL = $Mail::Ezmlm::Maintenance::ERROR_FAIL;
    return undef;
  }
  return return dir_to_modgroup $h->{7};
}

sub get_submoderatorgroup($;) {
  my ($list) = @_;
  my $h = Mail::Ezmlm::Maintenance::get_config($Mail::Ezmanage::EZLISTS . '/' . $list);
  if (not defined $h) {
    $Mail::Ezmanage::Mod::ERROR = $Mail::Ezmlm::Maintenance::ERROR;
    $Mail::Ezmanage::Mod::ERROR_FAIL = $Mail::Ezmlm::Maintenance::ERROR_FAIL;
    return undef;
  }
  return dir_to_modgroup $h->{8};
}

sub set_moderatorgroup($$;) {
  my ($list, $group) = @_;
  my $r = Mail::Ezmlm::Maintenance::edit_list($Mail::Ezmanage::EZLISTS . '/' . $list,
					      {},
					      {moderators=>$Mail::Ezmanage::Mod::EZMODS . '/' . $group});
  $Mail::Ezmanage::Mod::ERROR = $Mail::Ezmlm::Maintenance::ERROR;
  $Mail::Ezmanage::Mod::ERROR_FAIL = $Mail::Ezmlm::Maintenance::ERROR_FAIL;
  return $r;
}

sub set_submoderatorgroup($$;) {
  my ($list, $group) = @_;
  my $r = Mail::Ezmlm::Maintenance::edit_list($Mail::Ezmanage::EZLISTS . '/' . $list,
					      {},
					      {submoderators=>$Mail::Ezmanage::Mod::EZMODS . '/' . $group});
  $Mail::Ezmanage::Mod::ERROR = $Mail::Ezmlm::Maintenance::ERROR;
  $Mail::Ezmanage::Mod::ERROR_FAIL = $Mail::Ezmlm::Maintenance::ERROR_FAIL;
  return $r;
}

############################################################################

1;

=head1 AUTHOR

Tommi Virtanen, Havoc Consulting (tv@havoc.fi)

=cut
