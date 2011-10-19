from django.http import HttpResponse, Http404
from django.template import loader, RequestContext, Template
from django.views.decorators.http import require_http_methods

from tiote import forms, functions

def ajax(request):
    return functions.http_500('feature not yet implemented!')


def overview(request):
    # form initiliazation
    TableForm = ''
    FieldFormSet = ''
    if request.session.get('TIOTE_DIALECT') == 'mysql':
        TableForm = forms.TableForm_my
        FieldFormSet = forms.FieldFormSet_my
    elif request.session.get('TIOTE_DIALECT', '') == 'postgresql':
        pass
#        TableForm = TableForm_gre()
#        FieldFormSet = FieldFormSet_gre()

    if request.method == 'POST':
        # form submission
        tableform = TableForm(request.POST)
        fieldformset = FieldFormSet(request.POST)
        if tableform.is_valid() and fieldformset.is_valid():
            return HttpResponse('post data accepted. feature not yet implemented!')
    else:
        # form generation
        tableform = TableForm()
        fieldformset = FieldFormSet()
        template = skeleton('overview')
        c = {'db': request.GET.get('database', '')}
        context = RequestContext(request,
            {'tableform': tableform, 'fieldformset': fieldformset},
            [site_proc]
        )
        return HttpResponse(template.render(context))
    

def query(request):
    pass


def import_(request):
    pass


def export(request):
    pass


