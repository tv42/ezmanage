#
# $Id: Maintenance.pm,v 1.2 2000/03/21 20:59:22 tv42 Exp $
#
# Module Mail::Ezmlm::Maintenance - a library to manipulate ezmlm mailing lists
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

package Mail::Ezmlm::Maintenance;

sub Version { $VERSION; }
$VERSION = sprintf("%d.%02d", q$Revision: 1.2 $ =~ /(\d+)\.(\d+)/);

=head1 NAME

Mail::Ezmlm::Maintenance - a library to manipulate Ezmlm mailing lists

=head1 SYNOPSIS

  use Mail::Ezmlm::Maintenance;
  # the rest is too complicated for a synopsis; keep reading

=head1 ABSTRACT

This module provides a backend for the B<ezmanage> mailing list management system.

=head1 TODO

This interface is currently to be considered for internal use only. It
has not yet stabilized enough to warrant publically-usable documentation.

=cut

require Exporter;
@ISA = qw(Exporter);

@EXPORT = qw(make_list edit_list);

use strict;
require Mail::Ezmlm;

############################################################################

$Mail::Ezmlm::Maintenance::ERROR=''; # will contain an explanation of last error. Set when routines return undef.
$Mail::Ezmlm::Maintenance::ERROR_FAIL=0; # this will be 1 if the error is permanent, and 0 on soft errors.

############################################################################

my (%valid_flags) = 
  (
   archive			=> [option('a')],
   use_ezmlmrc			=> [option('c')],
   digest			=> [option('d')],
   subjectprefix		=> [option('f')],
   guardarchive			=> [option('g')],
   indexing			=> [option('i')],
   blacklist			=> [option('k')],
   remoteadmin_listsubscribers	=> [option('l')],
   moderated			=> [option('m')],	# if you combine moderated and subscribersonly,
   remoteadmin_edittext		=> [option('n')],
   public			=> [option('p')],
   requests			=> [option('q')],
   remoteadmin			=> [option('r')],
   submoderated			=> [option('s')],
   trailer			=> [option('t')],
   subscribersonly		=> [option('u')],	# you get nomod for subscribers and moderation for others
   mailtoprefix_and_mimeremove	=> [option('x')],
  );

my (%valid_parameters) =
  (
   sublist			=> 0, # mainlist@host
   owner			=> 5, # owner@host
   moderators			=> 7, # /path
   submoderators		=> 8, # /path
   remoteadmins			=> 9, # /path
   description			=> 3, # ezmanage extension: list description
   archivedir			=> 6, # ezmanage externsion: archive dir
   digest_code			=> 'special_digestcode',
  );

############################################################################

sub flags_to_args(\%\@) {
  my ($flags, $args) = @_;
  foreach (keys %$flags) {
    return fail("not a valid flag: $_") unless defined $valid_flags{$_};
    push @$args, @{$valid_flags{$_}}[ 1-$flags->{$_} ];
  }
  return 1;
}

sub params_to_args(\%\@) {
  my ($params, $args) = @_;
  my ($key, $val);
  while (($key, $val) = each %$params) {
    return fail("not a valid parameter: $key") unless defined $valid_parameters{$key};
    push @$args, '-' . $valid_parameters{$key}, $val;
  }
  return 1;
}

############################################################################

sub make_list($$$$$$$;) {
  # note $flags and $parameters are hashrefs
  my ($dir, $dot, $local, $host, $flags, $parameters, $digestcode) = @_;
  $dir =~ m{^/} or return fail('dir must be an absolute path');
  
  my (@args);
  return undef unless flags_to_args(%$flags, @args); # pass the error along
  return undef unless params_to_args(%$parameters, @args); # pass the error along
  push @args, $dir, $dot, $local, $host;
  push @args, $digestcode if defined $digestcode;
  Mail::Ezmlm::run_system('ezmlm-make', @args) == 0 or return err('ezmlm-make did not succeed');
}

sub edit_list($$;$$$$$;) {
  # note $flags and $parameters are hashrefs
  my ($dir, $flags, $parameters, $dot, $local, $host, $digestcode) = @_;
  $dir =~ m{^/} or return fail('dir must be an absolute path');
  
  my (@args);
  @args = ('-+c');
  return undef unless flags_to_args(%$flags, @args);
  if (defined $parameters) {
    return undef unless params_to_args(%$parameters, @args);
  }
  push @args, $dir;
  if (defined $dot) {
    return fail("all or none of dot local host must be present")
      unless defined $local and defined $host;
    push @args, $dot, $local, $host;
    
    push @args, $digestcode if defined $digestcode;
  }
  
  Mail::Ezmlm::run_system('ezmlm-make', @args) == 0 or return err('ezmlm-make did not succeed');
}

sub get_config($;) {
  # return list config as a hash
  my ($dir) = @_;
  open CONF, '<' . $dir . '/config'
    or return err("cannot open $dir/config for reading; $!");
  my (%h, @misc);
  while (<CONF>) {
    chomp;
    my ($key, $data) = /^(.*?):(.*)/;
    if (defined $key and defined $data) { $h{$key} = $data }
    else { push @misc, $_ }
  }
  close CONF
    or return err("cannot close $dir/config; $!");
  $h{EZMANAGE_NO_KEY} = \@misc if (@misc);
  return \%h;
}

sub get_msgsize($;) { # in return values, 0 means unlimited
  my ($dir) = @_;
  if (not open MSGSIZE, '<' . $dir . '/msgsize') {
    if ($! =~ /^No such file or directory/) {
      return wantarray ? (0,0) : 0;
    }
    else { return err("open failed for $dir/msgsize; $!") }
  }
  my $l = <MSGSIZE>;
  close MSGSIZE;
  defined $l or return wantarray ? (0, 0) : 0;
  my ($max, $min) = $l =~ /^(\d+)(?::(\d+))?$/;
  return err("invalid data in $dir/msgsize; $l not in form max[:min]")
    unless defined $max;
  return wantarray ? ($max, defined $min ? $min : 0) : $max;  
}

sub set_msgsize($$;$;) {
  my ($dir, $max, $min) = @_;
  ($dir) = ($dir =~ /(.*)/); # TODO why is this tainted?
  open MSGSIZE, '>' . $dir . '/msgsize.tmp' or return err("cannot open file $dir/msgsize.tmp for writing; $!");
  print MSGSIZE $max, defined $min ? ":$min\n" : "\n"
    or return err("writing to $dir/msgsize.tmp failed; $!");
  close MSGSIZE
    or return err("closing $dir/msgsize.tmp failed; $!");
  rename $dir . '/msgsize.tmp', $dir . '/msgsize'
    or return err("renaming $dir/msgsize.tmp to $dir/msgsize failed; $!");
  return 1;
}

sub remove_msgsize($;) {
  my ($dir) = @_;
  -e $dir . '/msgsize' or return 1;
  unlink $dir . '/msgsize' or return err("cannot remove $dir/msgsize; $!");
  return 1;
}

############################################################################

sub option ($;$;) {
  my ($yes, $no) = @_;
  $no = swap_case($yes) unless defined $no;
  return "-$yes", "-$no";
}

sub swap_case($;) {
  my ($c) = @_;
  my ($lc, $uc) = (lc $c, uc $c);
  if ($lc eq $c) { return $uc }
  elsif ($uc eq $c) { return $lc }
  else { return $c }
}

############################################################################

sub err($;) {
  $Mail::Ezmlm::Maintenance::ERROR = $_[0];
  $Mail::Ezmlm::Maintenance::ERROR_FAIL = 0;
  return undef;
}

sub fail($;) {
  $Mail::Ezmlm::Maintenance::ERROR = $_[0];
  $Mail::Ezmlm::Maintenance::ERROR_FAIL = 1;
  return undef;
}

sub error() { $Mail::Ezmlm::Maintenance::ERROR }
sub failure() { $Mail::Ezmlm::Maintenance::ERROR_FAIL }

############################################################################

1;

=head1 AUTHOR

Tommi Virtanen, Havoc Consulting (tv@havoc.fi)

=cut
