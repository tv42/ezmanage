#
# $Id: Fullnames.pm,v 1.2 2000/03/21 20:59:22 tv42 Exp $
#
# Module Mail::Ezmanage::Fullnames - a library to manipulate multiple Ezmlm mailing lists
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

package Mail::Ezmanage::Fullnames;

sub Version { $VERSION; }
$VERSION = sprintf("%d.%02d", q$Revision: 1.2 $ =~ /(\d+)\.(\d+)/);

=head1 NAME

Mail::Ezmanage::Fullnames - a library to manipulate multiple Ezmlm mailing lists

=head1 SYNOPSIS

  use Mail::Ezmanage::Fullnames;
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
use DB_File;
use Fcntl ':flock';
use Mail::Ezmanage;

# non-exported package globals go here
use vars qw($_ioref %_fullnames $_tied $_lockwrite);
$_tied = 0;
$_ioref = undef;
%_fullnames = ();
$_lockwrite = undef;

############################################################################

$Mail::Ezmanage::Fullnames::ERROR=''; # will contain an explanation of last error. Set when routines return undef.
$Mail::Ezmanage::Fullnames::ERROR_FAIL=0; # this will be 1 if the error is permanent, and 1 on soft errors.

############################################################################

sub err(@) {
  $Mail::Ezmanage::Fullnames::ERROR = "@_";
  $Mail::Ezmanage::Fullnames::ERROR_FAIL = 0;
  return undef;
}

sub fail(@) {
  $Mail::Ezmanage::Fullnames::ERROR = "@_";
  $Mail::Ezmanage::Fullnames::ERROR_FAIL = 1;
  return undef;
}

sub error() { $Mail::Ezmanage::Fullnames::ERROR }
sub failure() { $Mail::Ezmanage::Fullnames::ERROR_FAIL }

############################################################################

sub tie_it(;$;) { # undef on error, 1 on success, 0 on readonly&&nonexistent
  my ($readonly) = @_;
  return 1 if $_tied;
  my $dbfile = $Mail::Ezmanage::EZMANAGEDIR . '/fullnames.db';

  # this is to circumvent a weird behaviour in File_DB:
  # if the db does not exist, and is opened but no written
  # to, it will end up with size zero, and cannot be opened
  # later..
  return 0 if $readonly and not -f $dbfile;

  my $r=tie(%_fullnames, 'DB_File', $dbfile,
	    O_RDWR|O_CREAT, 0640, $DB_HASH);
  return undef unless defined $r;
  $_tied++;
  return 1;
}

sub untie_it() {
  if ($_tied) {
    untie %_fullnames;
    $_tied=0;
  }
  return 1;
}

sub lock(;$;) {
  ($_lockwrite) = @_;
  
  my $db = tied %_fullnames;
  defined $db or return undef;
  my $fd = $db->fd();
  defined $fd or return undef;
  open DB, "+<&=$fd" or return undef;
  flock DB, $_lockwrite ? LOCK_EX : LOCK_SH or return undef;
  $_ioref = *DB{IO};
  return 1;
}

sub unlock() {
  my $db = tied %_fullnames;
  defined $db or return undef;
  $db->sync if $_lockwrite;
  defined $_ioref or return undef;
  flock $_ioref, LOCK_UN or return undef;
  close $_ioref;
  undef $_ioref;
  undef $_lockwrite;
  return 1;
}

############################################################################

sub set_name(%) {
  my (%names) = @_;
  tie_it()
    or return err "cannot open fullnames database; $!";
  lock(1)
    or return err "cannot lock fullnames database; $!";
  my ($addr, $name);
  while (($addr, $name) = each %names) {
    $_fullnames{$addr} = $name;
  }
  unlock()
    or return err "unlock failed for fullnames database; $!";
  untie_it();
  return 1;
}

sub remove_name(@) {
  my (@names) = @_;
  tie_it()
    or return err "cannot open fullnames database; $!";
  lock(1)
    or return err "cannot lock fullnames database; $!";
  foreach (@names) {
    delete $_fullnames{$_}
  }
  unlock()
    or return err "unlock failed for fullnames database; $!";
  untie_it();
  return 1;
}

sub get_name($;) {
  my ($address) = @_;
  my $r=tie_it(1);
  defined $r or return err "cannot open fullnames database; $!";
  return undef if $r == 0; # nonexistant
  lock()
    or return err "cannot read-lock fullnames database; $!";
  my $name=$_fullnames{$address};
  unlock()
    or return err "unlock failed for fullnames database; $!";
  untie_it();
  return $name;
}

sub open_hash() { # undef on error, 0 on nonexistant, hashref on success
  my $r=tie_it(1);
  defined $r or return err "cannot open fullnames database; $!";
  return 0 if $r == 0; # nonexistant
  lock()
    or return err "cannot read-lock fullnames database; $!";
  return \%_fullnames;
}

sub close_hash() {
  unlock()
    or return err "unlock failed for fullnames database; $!";
  untie_it();
  return 1;
}

############################################################################

1;

=head1 AUTHOR

Tommi Virtanen, Havoc Consulting (tv@havoc.fi)

=cut
