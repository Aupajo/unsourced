import urllib   # for urlencode
from pprint import pprint
import datetime

import tornado.web
from sqlalchemy import not_
from models import Source,SourceKind,Article,Action,Label
import util


source_presentation = {
    SourceKind.PAPER: {'icon':'paper_icon.png', 'desc':'Academic paper'},
    SourceKind.PR: {'icon':'recycle_icon.png', 'desc':'Press release'},
    SourceKind.OTHER: {'icon':'chain_icon.png', 'desc':'Other link'},
    }


class formfield(tornado.web.UIModule):
    def render(self, field):
        return self.render_string("modules/formfield.html", field=field)


class form(tornado.web.UIModule):
    def render(self, form):
        return self.render_string("modules/form.html", form=form)




class postbutton(tornado.web.UIModule):
    """ a button which POSTs to a url, falling back to an <a> with login link if user not logged on """
    def render(self, url, txt):
        return self.render_string("modules/postbutton.html", url=url, txt=txt)


class domain(tornado.web.UIModule):
    def render(self, url):
        return util.domain(url)



class user(tornado.web.UIModule):
    def render(self, user, show_avi):
        out = u''
        if show_avi:
            out += user.photo_img('s')

        if user is not None:
            out += u'<a href="/user/%d">%s</a>' % (user.id, user.username)
        else:
            out += u'anonymous'
        return out

class art_link(tornado.web.UIModule):
    def render(self, art):
        return '<a href="/art/%s">%s</a> (%s)' % (art.id, art.headline, util.domain(art.permalink))









class source(tornado.web.UIModule):
    def render(self, src, container='div'):

        can_upvote = False
        can_downvote = False
        if self.current_user is not None:
            prev_vote = self.handler.session.query(Action).filter_by(what='src_vote',user_id=self.current_user.id, source=src).first()

            if prev_vote is None or prev_vote.value>0:
                can_downvote = True
            if prev_vote is None or prev_vote.value<0:
                can_upvote = True

        title=src.title
        if not title:
            if src.kind==SourceKind.PR:
                title = "Press release (%s)" % (util.domain(src.url),)
            if src.kind==SourceKind.OTHER:
                title = "Other link (%s)" % (util.domain(src.url),)

        return self.render_string("modules/source.html",
            id=src.id,
            title=title,
            kind=src.kind,
            url=src.url,
            publication=src.publication,
            pubdate=src.pubdate,
            doi=src.doi,
            creator=src.creator,
            score=src.score,

            can_upvote=can_upvote,
            can_downvote=can_downvote,
            container=container,
            kind_desc=source_presentation[src.kind]['desc'],
            kind_icon='/static/' + source_presentation[src.kind]['icon'])


class art_list(tornado.web.UIModule):
    """ show a list of articles (eg search results)"""
    def render(self, arts):
        return self.render_string("modules/art_list.html", arts=arts)


class art_item(tornado.web.UIModule):
    """ handle an article as an entry in a list - ie one line with title, link etc... """
    def render(self, art):
        return self.render_string("modules/art_item.html", art=art)


class action(tornado.web.UIModule):
    """ describe an action """
    def render(self, act, show_article=True, show_full_source=True, user_display='m', show_timestamp=True ):

        desc = u''

        art = act.article
        if art:
            artlink = u'<a href="%s">%s</a>' % (art.art_url(), art.headline)

        src_kinds = {
            SourceKind.PAPER: u'a paper',
            SourceKind.PR: u'a press release',
            SourceKind.OTHER: u'a link' }

        if not show_article:
            # article point of view - show without article link
            if act.what == 'src_add':
                desc = u"added %s" % (src_kinds[act.source.kind],)
            elif act.what == 'src_remove':
                desc = u"removed %s" % (src_kinds[act.source.kind],)
            elif act.what =='art_add':
                desc = u'submitted this article'
            elif act.what =='comment':
                desc = u'<blockquote>%s</blockquote>' % (act.comment.format(),)
            elif act.what =='tag_add':
                if act.tag.name=='help':
                    desc = u'asked for help'
                elif act.tag.name=='done':
                    desc = u'marked article as complete'
            elif act.what =='tag_remove':
                if act.tag.name=='help':
                    desc = u'turned off the help request'
                elif act.tag.name=='done':
                    desc = u'marked article as incomplete'
            elif act.what =='mark_sourced':
                desc = u'marked article as sourced'
            elif act.what =='mark_unsourced':
                desc = u'marked article as unsourced'
            elif act.what =='helpreq_open':
                desc = u'asked for help'
            elif act.what =='helpreq_close':
                desc = u'closed a help request'
            elif act.what =='label_add':
                desc = u"Added a '%s' label" % (act.label.prettyname,)
            elif act.what =='label_remove':
                desc = u"Removed a '%s' label" % (act.label.prettyname,)

        else:
            if act.what == 'src_add':
                desc = u"added %s to %s" % (src_kinds[act.source.kind], artlink)
            elif act.what == 'src_remove':
                desc = u"removed a source from %s" % (artlink,)
            elif act.what =='art_add':
                desc = u'submitted article %s' % (artlink,)
            elif act.what =='comment':
                desc = u'<blockquote>%s</blockquote> on %s' % (act.comment.format(), artlink)
            elif act.what =='tag_add':
                if act.tag.name=='help':
                    desc = u'asked for help with %s' %(artlink,)
                elif act.tag.name=='done':
                    desc = u'marked article %s as complete' %(artlink,)
            elif act.what =='tag_remove':
                if act.tag.name=='help':
                    desc = u'closed help request on %s' %(artlink,)
                elif act.tag.name=='done':
                    desc = u'marked article %s as incomplete' %(artlink,)
            elif act.what =='mark_sourced':
                desc = u'marked article %s as sourced' % (artlink,)
            elif act.what =='mark_unsourced':
                desc = u'marked article %s as unsourced' % (artlink,)
            elif act.what =='helpreq_open':
                desc = u'asked for help on article %s' % (artlink,)
            elif act.what =='helpreq_close':
                desc = u'closed a help request on article %s' % (artlink,)
            elif act.what =='label_add':
                desc = u"added a '%s' label to %s" % (act.label.prettyname, artlink)
            elif act.what =='label_remove':
                desc = u"removed a '%s' label to %s" % (act.label.prettyname, artlink)

        return self.render_string("modules/action.html",
            act=act,
            show_article=show_article,
            show_full_source=show_full_source,
            show_timestamp=show_timestamp,
            desc_html=desc,
            user_display=user_display
        )




class daily_chart(tornado.web.UIModule):
    def render(self, stats, max_arts):

        def _width(v):
            perc = int(float(100*v)/ float(max_arts))
            return "%d%%" % (perc,)

        return self.render_string("modules/daily_chart.html", stats=stats, max_arts=max_arts, w=_width, human_day=util.human_day)





class source_icon(tornado.web.UIModule):
    """ iconic representation of a source """
    def render(self,src):
        kind_icon = '/static/' + source_presentation[src.kind]['icon']
        kind_desc = source_presentation[src.kind]['desc']
        return """<img src="%s" title="%s"/>""" % (kind_icon,kind_desc)


class league_table(tornado.web.UIModule):
    def render(self, rows, heading, action_desc):
        return self.render_string('modules/league_table.html',rows=rows, heading=heading, action_desc=action_desc)




class tool_googlescholar(tornado.web.UIModule):
    def render(self, institutions, journals, researchers):
        return self.render_string('modules/tool_googlescholar.html',
            institutions=institutions,
            journals=journals,
            researchers=researchers)


    def embedded_javascript(self):
        return """
    $('.helper form .researcher').each(function(index) {
        var fullname = '"' + $.trim($(this).text()) + '"';

        var cb = $('<input type="checkbox" />').change(function() {
            var cur = $.trim($('#as_sauthors').val());
            var pat = new RegExp($.reescape(fullname),"ig");
            if(this.checked) {
               cur = cur + " " + fullname;
            } else {
               cur = cur.replace(pat,'');
            }
            $('#as_sauthors').val(cur);
        });
        cb.prependTo(this);
        $(this).wrap("<label/>");
    });

    $('.helper form .journal').each(function(index) {
        var fullname = $.trim($(this).text()); 

        var cb = $('<input type="radio" name="j"/>').change(function() {
            var cur = $.trim($('#as_publication').val());
            var pat = new RegExp($.reescape(fullname),"ig");
            if(this.checked) {
               cur = fullname;
            } else {
               cur = cur.replace(pat,'');
            }
            $('#as_publication').val(cur);
        });
        cb.prependTo(this);
        $(this).wrap("<label/>");

    });

        """


class add_paper(tornado.web.UIModule):
    def render(self, art, add_paper_form):
        return self.render_string('modules/add_paper.html', art=art, form=add_paper_form, field=add_paper_form.url)

    def embedded_javascript(self):
        return """
            ajaxifyAddSourceForm(
                $('#add-paper'),
                "Looking up details...");
        """


class add_pr(tornado.web.UIModule):
    def render(self, art, add_pr_form):
        return self.render_string('modules/add_pr.html', art=art, form=add_pr_form)

    def embedded_javascript(self):
        return """
            ajaxifyAddSourceForm(
                $('#add-pr'),
                "Adding..." );
        """



class add_other(tornado.web.UIModule):
    def render(self, art, add_other_form):
        return self.render_string('modules/add_other.html', art=art, form=add_other_form)

    def embedded_javascript(self):
        return """
            ajaxifyAddSourceForm(
                $('#add-other'),
                "Adding...");
        """




class login(tornado.web.UIModule):
    def render(self, form):
        reg_url = '/register'
        forgot_url = '/login/forgot'
        twitter_login_url = '/login/twitter'
        google_login_url = '/login/google'
        try:
            next = form.next.data
            if next is not None:
                foo = "?" + urllib.urlencode({'next':next})
                reg_url += foo
                twitter_login_url += foo
                google_login_url += foo
        except AttributeError:
            pass
        return self.render_string('modules/login.html',
            form=form,
            reg_url=reg_url,
            forgot_url=forgot_url,
            twitter_login_url=twitter_login_url,
            google_login_url=google_login_url)


class register(tornado.web.UIModule):
    def render(self, form):
        login_url = '/login'
        twitter_login_url = '/login/twitter'
        google_login_url = '/login/google'
        try:
            next = form.next.data
            if next is not None:
                foo = "?" + urllib.urlencode({'next':next})
                login_url += foo
                twitter_login_url += foo
                google_login_url += foo
        except AttributeError:
            pass
        return self.render_string('modules/register.html',
            form=form,
            login_url=login_url,
            twitter_login_url=twitter_login_url,
            google_login_url=google_login_url)



class forgot(tornado.web.UIModule):
    """user forgot login details - request a login link"""
    def render(self, form):
        reg_url = '/register'
        login_url = '/login'
        return self.render_string('modules/forgot.html',
            form=form,
            login_url=login_url,
            reg_url=reg_url
            )


class filters(tornado.web.UIModule):
    def render(self, filters):
        return self.render_string("modules/filters.html", filters=filters)

    def embedded_javascript(self):
        return """
    $('#filters input[type="submit"]').hide();
    $('#filters form').bind('submit', function(e){
        e.preventDefault();

        var form = $(this);
        var url = form.attr('action');
        var params = form.serialize();
        var timeout = setTimeout( function() {
            $('#results').addClass("is-busy-large");
        }, 500 );
        /* clear off any old errors */
        showFormErrs(form,[]);
        $.ajax({
			type: "GET",
			url: url,
			data: params,
            complete: function(jqXHR, textStatus) {
                clearTimeout(timeout);
                $('#results').removeClass("is-busy-large");
            },
			success: function(data){
                if(data.status=='ok') {
				    $('#results').html(data.results_html);
                    if(window.history.pushState) {
                        window.history.replaceState('', "FOOO!", url+"?"+params);
                    }
                } else {    /* 'badfilters' */
                    showFormErrs(form, data.errors);
                }
			}
		});
    });

    function update_daterange() {
        var rangebutton = $('#filters input[name="date"][value="range"]');
        if(rangebutton.is(':checked')) {
            $('#dayfrom,#dayto').prop('disabled',false).closest('.field').show();
        } else {
            $('#dayfrom,#dayto').prop('disabled',true).closest('.field').hide();
        }
    }

    $('#filters input').bind("change", function(e) {
        if($(this).attr('name') == 'date') {
            update_daterange();
            if($(this).val()=='range') {
                /* only submit if there are dates */
                /*if( $('#dayfrom').val()=='' &&
                    $('#dayto').val() == '' ) {
                    return;
                }
                */
                return;
            }
        }
        $('#filters form').submit();
    });
    update_daterange();
        """

class searchresults(tornado.web.UIModule):
    def render(self, filters, paged_results):
        return self.render_string("modules/searchresults.html", filters=filters,paged_results=paged_results)

class paginator(tornado.web.UIModule):
    def render(self, pager):
        return self.render_string("modules/paginator.html", pager=pager)


class fmt_datetime(tornado.web.UIModule):
    def render(self, dt, cls=''):

        if cls:
            extra = 'class="%s"' % (cls,)
        else:
            extra = ''
        return '<time %sdatetime="%s">%s</time>' % (
            extra,
            dt.isoformat(),
            self.locale.format_date(dt, shorter=True)
            ) 

class fmt_date(tornado.web.UIModule):
    def render(self, d, cls=''):

        if cls:
            extra = 'class="%s"' % (cls,)
        else:
            extra = ''
        return '<time %sdatetime="%s">%s</time>' % (
            extra,
            d.isoformat(),
            d.strftime('%d %b %Y')
            ) 


class helper_paper(tornado.web.UIModule):
    """ show help on tracking down academic papers """
    def render(self, art, journals, institutions, researchers):
        return self.render_string('modules/helper_paper.html',
            art=art,
            institutions=institutions,
            journals=journals,
            researchers=researchers)


class helper_pr(tornado.web.UIModule):
    """ show help on tracking down press releases """
    def render(self, art, journals, institutions, researchers):
        return self.render_string('modules/helper_pr.html',
            art=art,
            institutions=institutions,
            journals=journals,
            researchers=researchers)


class helper_other(tornado.web.UIModule):
    """ show help on tracking down other links """
    def render(self, art, journals, institutions, researchers):
        return self.render_string('modules/helper_other.html',
            art=art,
            institutions=institutions,
            journals=journals,
            researchers=researchers)


class label_picker(tornado.web.UIModule):
    """ show help on tracking down other links """
    def render(self, art):

        assigned = [l.label.id for l in art.labels]
        available = self.handler.session.query(Label).\
            filter(not_(Label.id.in_(assigned))).\
            all()

        return self.render_string('modules/label_picker.html', art=art, available=available)



class label(tornado.web.UIModule):
    """ render a Label

    label: Label object (ie label definition)
    usage: ArticleLabel (an actual usage of a Label upon an Article) or None
    """
    def render(self, label, usage=None, size='l'):
        return self.render_string('modules/label.html', label=label, usage=usage, size=size)

