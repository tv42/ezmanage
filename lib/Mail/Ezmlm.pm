#
# $Id: Ezmlm.pm,v 1.1 2000/03/20 17:29:39 tv42 Exp $
#
# Module Mail::Ezmlm - a library to manipulate ezmlm mailing lists
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

package Mail::Ezmlm;

sub Version { $VERSION; }
$VERSION = sprintf("%d.%02d", q$Revision: 1.1 $ =~ /(\d+)\.(\d+)/);

=head1 NAME

Mail::Ezmlm - a library to manipulate Ezmlm mailing lists

=head1 SYNOPSIS

  use Mail::Ezmlm;
  # the rest is too complicated for a synopsis; keep reading

=head1 ABSTRACT

This module provides a backend for the B<ezmanage> mailing list management system.

=head1 TODO

This interface is currently to be considered for internal use only. It
has not yet stabilized enough to warrant publically-usable documentation.

=cut

require Exporter;
@ISA = qw(Exporter);

@EXPORT = qw(subscribe unsubscribe subscribe_mail unsubscribe_mail
	     subscribers is_subscriber is_subscriber_n make_list edit_list
	     get_dir digest_address);

use strict;

use Mail::Send;
use Mail::Address;
use IO::Handle;

############################################################################

$Mail::Ezmlm::ERROR=''; # will contain an explanation of last error. Set when routines return undef.
$Mail::Ezmlm::ERROR_FAIL=0; # this will be 1 if the error is permanent, and 1 on soft errors.
sub fail(@);
sub err(@);

############################################################################

sub get_dir($@) {
  my ($type) = shift;
# should be one of digest blacklist mod remote - others possible due to weird moderation schemes
  my (@r) = map { s{/+$}{}g; "$_/$type" } @_;
  return wantarray ? @r : "@r";
}

sub digest_address(@) { 
  my (@r) = map {
    m/(.*)@(.*)/; 
    defined $1 and defined $2 or return undef; 
    $1 . '-digest@' . $2 
  } @_;
  return \@r;
}

sub subscribe($;@) {
# WISHLIST digest handling ugly - subscribe(get_dir($dir, 'digest'), @sub)
  my ($dir, @sub) = @_;
  $dir =~ m{^/} or return fail('dir must be an absolute path');
  run_system('ezmlm-sub', $dir, map {s/\r?\n?$//; $_} @sub) == 0 or return err('ezmlm-sub did not succeed');
}

sub unsubscribe($;@) {
  my ($dir, @sub) = @_;
  $dir =~ m{^/} or return fail('dir must be an absolute path');
  run_system('ezmlm-unsub', $dir, map {s/\r?\n?$//; $_} @sub) == 0 or return err('ezmlm-unsub did not succeed');
}

sub subscribe_mail($;@) {
# WISHLIST digest handling ugly - subscribe_mail(digest_address($list), @sub)
  my ($list, @sub) = @_;
  mail_request($list, 'subscribe', "This is an automated request to subscribe you to the mailing list\n$list.", map {s/\r?\n?$//; $_} @sub);
}

sub unsubscribe_mail($;@) {
  my ($list, @sub) = @_;
  mail_request($list, 'unsubscribe', "This is an automated request to unsubscribe you from the mailing list\n$list.", map {s/\r?\n?$//; $_} @sub);
}

sub subscribers($) {
  my ($dir) = @_;
  return fail('dir not defined') unless defined $dir;
  
  my $sleep_count = 0;
  my $pid;
  while ($sleep_count <= 6 and not defined $pid) {
    STDERR->flush();
    STDOUT->flush();
    $pid = open(KID_TO_READ, "-|");
    unless (defined $pid) {
      warn "cannot fork: $!";
      $sleep_count++;
      sleep 10;
    }
  }
  return err('fork failed') unless defined $pid;

  my (@sub);
  if ($pid) {  # parent
    while (<KID_TO_READ>) {
      chomp;
      push @sub, $_;
    }
    close(KID_TO_READ) or return err('ezmlm-list did not succeed');
  } else {     # child
    run_exec('ezmlm-list', $dir) or die "can't exec program: $!";
    # NOTREACHED
  }
  
  return \@sub;
}
		
sub is_subscriber($;@) {
  my ($dir, @sub) = @_;
  my $is_sub;
  my $r = 0;
  foreach (map {s/\r?\n?$//; $_} @sub) {
    $is_sub = is_subscriber_n($_, $dir);
    return undef unless defined $is_sub; # pass the error along..
    $r++ if $is_sub;
  }
  return $r; # return how many addresses were on the list
}

sub is_subscriber_n($;@) {
# NOTE - will give false for non-existent mailing lists
  my ($sub, @dir) = @_;
  (@dir) or return 0;
  $sub =~ s/\r?\n?$//;
  my ($old_sender) = $ENV{SENDER};
  $ENV{SENDER} = $sub;
  my $rc = run_system('ezmlm-issubn', @dir);
  if (defined $old_sender) { $ENV{SENDER} = $old_sender }
  else { delete $ENV{SENDER} }
  if ($rc == 0) { return 1 }
  elsif ($rc == 0xff00) { return err("command failed: $!") }
  elsif ($rc > 0x80) { 
    $rc >>= 8;
    if ($rc == 0) { return 1 }
    elsif ($rc == 99) { return 0 }
    else { return err('ezmlm-issubn returned an unknown errorlevel') }
  }
  else { return err('ezmlm-issubn dumped core or was killed by a signal') }
}


############################################################################

sub mangled (@) {
  my (@addr) = @_;
  foreach (@addr) { s/@/=/ }
  return wantarray ? @addr : "@addr";
}

sub mail_request_old($$$;@) {
  my ($list, $request, $body, @addr) = @_;
  defined $list and defined $request and defined $body 
    or return fail 'list or request or body not defined';
  my ($list_local, $list_host) = $list=~/(.*)@(.*)/;
  defined $list_local and defined $list_host or return fail 'list mailbox or host not defined';
  $list_local ne '' and $list_host ne '' or return fail 'list mailbox or host empty';
  my $msg = new Mail::Send Subject=>'Automated subscription request' or return err('unable to create new Mail::Send');
  $msg->to('');
  $msg->bcc(map { $list_local . '-' . $request . '-' . mangled($_) . '@' . $list_host } map {s/\r?\n?$//; $_} @addr);
  STDERR->flush();
  STDOUT->flush();
  my $fh = $msg->open;
  defined $fh or return err("unable to open file handle; $!");
  print $fh $body;
  $fh->close or return err("close failed; $!");
}

sub mail_request($$$;@) {
  my ($list, $request, $body, @addr) = @_;
  defined $list and defined $request and defined $body 
    or return fail 'list or request or body not defined';
  my ($list_local, $list_host) = $list=~/(.*)@(.*)/;
  defined $list_local and defined $list_host or return fail 'list mailbox or host not defined';
  $list_local ne '' and $list_host ne '' or return fail 'list mailbox or host empty';
  
  my $sleep_count = 0;
  my $pid;
  do {
    $pid = open(KID_TO_WRITE, "|-");
    unless (defined $pid) {
      warn "cannot fork: $!";
      die "bailing out" if $sleep_count++ > 6;
      sleep 10;
    }
  } until defined $pid;
  
  if ($pid) {  # parent
    print KID_TO_WRITE 
      "Subject: Automated subscription request\n",
      "To: ", (map { $list_local . '-' . $request . '-' . mangled($_)
		       . '@' . $list_host } map {s/\r?\n?$//; $_} @addr), "\n\n",
	$body
	  or return err "writing to qmail-inject failed; $!";
    close(KID_TO_WRITE) || return($? == 111 
				  ? err "qmail-inject deferred $?"
				  : fail "qmail-inject failed $?");
  } else {     # child
    $ENV{PATH} = '/bin:/usr/bin:/usr/sbin:/var/qmail/bin';
    exec 'qmail-inject' or exit 111;
  }
  return 1;
}

sub run_system($@) {
  STDERR->flush();
  STDOUT->flush();
  $ENV{PATH} = '/bin:/usr/bin';
  my ($rc) = system(@_);
  return $rc;
}

sub run_exec($@) {
  STDERR->flush();
  STDOUT->flush();
  $ENV{PATH} = '/bin:/usr/bin';
  { # exec is in it's own block to suppress warning messages from perl
    exec(@_);
  }
  return undef;
}

############################################################################

sub err(@) {
  $Mail::Ezmlm::ERROR = "@_";
  $Mail::Ezmlm::ERROR_FAIL = 0;
  return undef;
}

sub fail(@) {
  $Mail::Ezmlm::ERROR = "@_";
  $Mail::Ezmlm::ERROR_FAIL = 1;
  return undef;
}

sub error() { $Mail::Ezmlm::ERROR }
sub failure() { $Mail::Ezmlm::ERROR_FAIL }

############################################################################
1;

=head1 AUTHOR

Tommi Virtanen, Havoc Consulting (tv@havoc.fi)

=cut
