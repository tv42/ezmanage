#!/usr/bin/perl -wT
#
# $Id: ezmanage-websub.cgi,v 1.2 2000/03/21 20:59:22 tv42 Exp $
#
# ezmanage-websub.cgi - subscribe to a mailing list via WWW
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

ezmanage-websub.cgi - subscribe to a mailing list via WWW

=head1 SYNOPSIS

  Called by a WWW server as a CGI script.

=head1 DESCRIPTION

This script provides a WWW frontend for end users to subscribe
themselves to one or multiple mailing lists managed by B<ezmanage>.

The interface consists of a textbox to type one's email address in,
and a scrolling list from which to choose lists.

Subscribing users is handled by sending email to the list, using
B<ezmlm>'s I<listname-subscribe-user=domain@example.com> -syntax. The
user has to reply to the confirmation request before any action will
be taken.

=head1 PARAMETERS

=over 4

=item list

Name of the list to subscribe to/unsubscribe from. Note this is not
the same as the list's email address.

=item email

Email address to subscribe/unsubscribe.

=item submit

If 'Subscribe', request subscribing. If 'Unsubscribe', request unsubscribing.

=back

=head1 USING DIRECTLY FROM OTHER HTML PAGES

By using html like

  <FORM method="POST" 
    action="http://www.example.com/cgi-bin/ezmanage-websub.cgi">
    <INPUT type="hidden" name="list" value="foo">
    <P>Enter your address below to subscribe to the list
      <EM>foo@lists.example.com</EM>:
      <BR><INPUT type="text" name="email">
      <INPUT type="submit" name="submit" value="Subscribe">
  </FORM>

you can embed the list subscription into other contexts.

=head1 AUTHOR

Tommi Virtanen, Havoc Consulting (tv@havoc.fi)

=cut

############################################################################
#
# Configure this:
#

my $back = './';
my $backtext = 'back';

############################################################################

use CGI ':standard';
use CGI::Carp; # qw(fatalsToBrowser);

use lib '/usr/lib/ezmanage/lib';
require Mail::Ezmlm;
require Mail::Ezmanage;


############################################################################

my $query = new CGI;
$query->import_names();
print $query->header;

if ((@Q::list) and $Q::list[0] ne ''
    and defined $Q::email and $Q::email =~ /.+@.+/
    and defined $Q::submit 
    and ($Q::submit eq 'Subscribe' or $Q::submit eq 'Unsubscribe')
   ) {
  my $errors = 0;
  my ($sub, $un);
  if ($Q::submit eq 'Subscribe') {
    $sub = \&Mail::Ezmlm::subscribe_mail;
    $un = '';
  }
  else {
    $sub = \&Mail::Ezmlm::unsubscribe_mail;
    $un = 'un';
  }
  print start_html('Your ' . ($Q::submit eq 'Subscribe' ? '' : 'un') .
		   'subscription request', Mail::Ezmanage::listmaster()),
    h1('Processing your request'), 
    "<P>[<A HREF=\"$back\">$backtext</A>]\n",
    "\n<ul>\n";
  foreach (map {Mail::Ezmanage::prettify('hp', $_)} @Q::list) {
    print li, $_, ': ';
    if (&{$sub}($_, $Q::email)) {
      print "ok.\n";
    }
    else {
      $errors++;
      print "<strong>error</strong>; ", Mail::Ezmlm::error(), "\n";
      warn Mail::Ezmlm::error();
    }
  }
  print "</ul>\n",
  p("Requests to ${un}subscribe you ", $un ? 'from' : 'to', " the above\n",
    "mailing lists have been sent. You will shortly receive confirmation\n",
    "messages. When you reply to those, you will be finally\n",
    "${un}subscribed. If you have any questions, please contact\n",
    a({href=>'mailto:' . Mail::Ezmanage::listmaster()}, 
      Mail::Ezmanage::listmaster()), ".\n"),
  end_html, "\n";
}
else {
  print start_html('Subscription/unsubscription', Mail::Ezmanage::listmaster()),
  startform,
  h1('Subscription/unsubscription'), "\n",
  "<P>[<A HREF=\"$back\">$backtext</A>]\n",
  p('Your email address:'), "\n",
  textfield(-name=>'email',
	    -size=>30), "\n\n";
  
  my $lists = Mail::Ezmanage::get_lists();
  die "Unable to get list of mailing lists" unless defined $lists;
  my $desc = Mail::Ezmanage::get_descriptions_with_list_address();
  print p('Select appropriate mailing list(s):'), "\n",
  scrolling_list('list',
		 $lists,
		 [@Q::list],
		 10, 'true',
		 $desc), "\n\n",
  p(), submit(-name=>'submit',
	 -value=>'Subscribe'), "\n",
  submit(-name=>'submit',
	 -value=>'Unsubscribe'), "\n",
  reset, "\n", 
  endform, end_html, "\n";
}
