#
# $Id: Ezmanage.pm,v 1.2 2000/03/21 20:59:22 tv42 Exp $
#
# Module Mail::Ezmanage - a library to manipulate multiple Ezmlm mailing lists
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

package Mail::Ezmanage;

sub Version { $VERSION; }
$VERSION = sprintf("%d.%02d", q$Revision: 1.2 $ =~ /(\d+)\.(\d+)/);

=head1 NAME

Mail::Ezmanage - a library to manipulate multiple Ezmlm mailing lists

=head1 SYNOPSIS

  use Mail::Ezmanage;
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
require Mail::Ezmlm::Maintenance;

############################################################################

$Mail::Ezmanage::ERROR=''; # will contain an explanation of last error. Set when routines return undef.
$Mail::Ezmanage::ERROR_FAIL=0; # this will be 1 if the error is permanent, and 1 on soft errors.

sub err(@) {
  $Mail::Ezmanage::ERROR = "@_";
  $Mail::Ezmanage::ERROR_FAIL = 0;
  return undef;
}

sub fail(@) {
  $Mail::Ezmanage::ERROR = "@_";
  $Mail::Ezmanage::ERROR_FAIL = 1;
  return undef;
}

sub error() { $Mail::Ezmanage::ERROR }
sub failure() { $Mail::Ezmanage::ERROR_FAIL }

############################################################################

sub prettify ($@) {
  my ($how) = shift;
  my ($prefix, $host) = ('', '');
  if ($how =~ /p/) { $prefix=$Mail::Ezmanage::EZPREFIX };
  if ($how =~ /h/) { $host='@' . $Mail::Ezmanage::EZHOST };
  return wantarray
    ? map { $prefix . $_ . $host } @_
      : $prefix . $_[0] . $host;
}

sub rawify ($@) {
  my ($how) = shift;
  my ($prefix, $host) = ('', '');
  if ($how =~ /p/) { $prefix=$Mail::Ezmanage::EZPREFIX };
  if ($how =~ /h/) { $host='@' . $Mail::Ezmanage::EZHOST };
  my @r = map { s/^$prefix//; s/@$host$//g; $_ } @_;
  return wantarray ? @r : $r[0];
}

sub getfirstline(@) {
  my (@r);
  foreach (@_) {
    if (open IN, '<' . $_) {
      my $r = <IN>;
      $r = '' if not defined $r; # empty files are considered to contain one empty line
      close IN;
      chomp $r;
      push @r, $r;
    }
    else {
      err "cannot open file $_ for reading: $!";
      push @r, undef;
    }
  }
  return wantarray ? @r : $r[0];
}

sub read_dir(&$;) {
  my ($grep, $dir) = @_;
  my @r;
  opendir DIR, $dir or return err "cannot open directory $dir";
  my $d;
  while (defined ($d=readdir DIR)) {
    next if $d =~ /^\./;
    $_ = $dir . '/' . $d;
    next unless &{$grep};
    push @r, $d;
  }
  closedir DIR;
  @r=sort @r;
  return \@r;
}

sub recdel($;) {
  my ($f) = @_;
  unlink $f and return () or return ("cannot unlink $f; $!") if -f $f or -l $f;
  return ("not a file or directory: $f") unless -d $f;
  opendir DIR, $f or return ("cannot open dir $f; $!");
  my @e = map {recdel($f . '/' . $_)} 
  map {/^(.*)$/; $1} # TODO this is just here to get around tainting
  grep {$_ ne '.' and $_ ne '..'} readdir DIR;
  closedir DIR;
  rmdir $f or return (@e, "cannot remove directory $f; $!");
  return @e;
} 

############################################################################

BEGIN {
  my $home = (getpwuid($<))[7]
    or die 'userid ', $<, ' not found in passwd, exiting';
  $Mail::Ezmanage::EZMANAGEDIR = $ENV{EZMANAGEDIR} || $home  . '/.ezmanage';
  $Mail::Ezmanage::EZCONFDIR = $ENV{EZCONFDIR} || $Mail::Ezmanage::EZMANAGEDIR . '/config';
  $Mail::Ezmanage::EZLISTS = $ENV{EZLISTS} || $Mail::Ezmanage::EZMANAGEDIR . '/lists';
  $Mail::Ezmanage::EZARCHIVE = $ENV{EZARCHIVE} || $Mail::Ezmanage::EZMANAGEDIR . '/archive';
  $Mail::Ezmanage::EZWEBARCHIVE = $ENV{EZWEBARCHIVE} || $Mail::Ezmanage::EZMANAGEDIR . '/webarchive';

  
  $Mail::Ezmanage::EZDOTQMAIL =  $ENV{EZDOTQMAIL}
  || getfirstline($Mail::Ezmanage::EZCONFDIR . '/dotqmail')
    || $home . '/.qmail-';
  
  # run some checks here to make EZDOTQMAIL not tainted
  ($Mail::Ezmanage::EZDOTQMAIL) = ($Mail::Ezmanage::EZDOTQMAIL =~ /^(.+)$/i) 
    if defined $Mail::Ezmanage::EZDOTQMAIL; # TODO
  
  my $prefix = $ENV{EZPREFIX};
  $prefix = getfirstline($Mail::Ezmanage::EZCONFDIR . '/prefix')
    if not defined $prefix;
  defined $prefix or die 'Ezmanage: cannot read config file "prefix", exiting';
  $Mail::Ezmanage::EZPREFIX = $prefix;

  $Mail::Ezmanage::EZHOST = $ENV{EZHOST} 
  || getfirstline($Mail::Ezmanage::EZCONFDIR . '/hostname')
    || die 'Ezmanage: cannot read config file "hostname", exiting';
}
	     
############################################################################

sub listmaster() {
  return ${Mail::Ezmanage::EZPREFIX} . 'listmaster@' . ${Mail::Ezmanage::EZHOST};
}

sub get_descriptions() { # output raw list names => desc
  my $lists = get_lists();
  return undef unless defined $lists; # pass the error along
  my %r;
  
  foreach my $l (@$lists) {
    my $d = get_list_description($l);
    defined $d or return err "getting list description for list $l failed";
    $r{$l} = $d;
  }
  return \%r;
}

sub get_descriptions_with_list_address() { # output raw list names => pretty: desc
  # prepend list name to description
  my $r = get_descriptions();
  return undef unless defined $r; # pass the error along
  my $d;
  foreach (keys %$r) {
    if (defined $r->{$_} and $r->{$_} ne '') {
      $r->{$_} = prettify('hp',$_) . ': ' . $r->{$_};
    }
    else {
      $r->{$_} = prettify('hp',$_);
    }
  }
  return $r;
}

sub get_list_description($;) { # input raw list name
  my ($list) = @_;
  my $r = Mail::Ezmlm::Maintenance::get_config($Mail::Ezmanage::EZLISTS . '/' . $list);
  if (not defined $r) {
    $Mail::Ezmanage::Maintenance::ERROR = $Mail::Ezmlm::Maintenance::ERROR;
    $Mail::Ezmanage::Maintenance::ERROR_FAIL = $Mail::Ezmlm::Maintenance::ERROR_FAIL;
    return undef;
  }
  my $desc = $r->{3}; # TODO this bypasses the API
  return defined $desc ? $desc : '';
}

sub set_list_description($$;) {
  my ($list, $desc) = @_;
  return err "Newlines not allowed in description" if $desc =~ /\n/;
  my $r = Mail::Ezmlm::Maintenance::edit_list($Mail::Ezmanage::EZLISTS . '/' . $list,
					      {},
					      {description=>$desc});
  $Mail::Ezmanage::ERROR_FAIL=$Mail::Ezmlm::Maintenance::ERROR_FAIL;
  $Mail::Ezmanage::ERROR=$Mail::Ezmlm::Maintenance::ERROR;
  return $r;
}

sub get_lists() { # raw, not prettified
  my $r = read_dir {-d} $Mail::Ezmanage::EZLISTS;
  return undef unless defined $r; # pass the error along
  return $r;
}

sub create($;) {
  my ($name) = @_;
  mkdir $Mail::Ezmanage::EZARCHIVE . "/$name", 0755
    or return err "archive directory creation failed; $!";
  my $r = Mail::Ezmlm::Maintenance::make_list($Mail::Ezmanage::EZLISTS . '/' . $name,
					      $Mail::Ezmanage::EZDOTQMAIL . $name,
					      $Mail::Ezmanage::EZPREFIX . $name,
					      $Mail::Ezmanage::EZHOST,
					      {use_ezmlmrc=>1},
					      {owner=>listmaster(),
					       archivedir=>$Mail::Ezmanage::EZARCHIVE
					       . '/' . $name});
  $Mail::Ezmanage::ERROR_FAIL=$Mail::Ezmlm::Maintenance::ERROR_FAIL;
  $Mail::Ezmanage::ERROR=$Mail::Ezmlm::Maintenance::ERROR;
  return $r;
}

sub remove($;) {
  my ($list) = @_;
  my $dotqmail = $Mail::Ezmanage::EZDOTQMAIL . $list;
  my @dot_ends = ('', '-owner', '-digest-owner', 
		    '-return-default', '-digest-return-default',
		    '-default');
  my @dot_ends_maybe = ('-accept-default', '-reject-default');
  
  my @err;
  foreach (@dot_ends) {
    unlink $dotqmail . $_
      or push @err, "unable to remove ${dotqmail}${_}; $!";
  }
  foreach (@dot_ends_maybe) { unlink $dotqmail . $_ }
  
  # now recursively delete .ezmanage/lists/$list and .ezmanage/archive/$list
  push @err, recdel($Mail::Ezmanage::EZLISTS . '/' . $list);
  push @err, recdel($Mail::Ezmanage::EZARCHIVE . '/' . $list)
    if -d $Mail::Ezmanage::EZARCHIVE . '/' . $list;
  
  return err join "\n",
  "problems occurred while removing list $list, summary follows:",
  @err if (@err);
  return 1;
}

############################################################################

1;

=head1 AUTHOR

Tommi Virtanen, Havoc Consulting (tv@havoc.fi)

=cut
