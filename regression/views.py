from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render, redirect
from django.views.generic.edit import FormView
from django.conf import settings
from django.utils import timezone
from django.core.files.storage import FileSystemStorage

import urllib.parse as prs
from shutil import copyfile
from operator import itemgetter
import os
import copy
import logging
import json
import mimetypes
from openpyxl import load_workbook
import pandas as pd
import datetime

from .forms import FileUploadForm, SingleFileForm
from .models import Platform_File, Activity, SingleFile
# Create your views here.


class UploadError(Exception):
    pass


def regression_upload(request):
    form = FileUploadForm()
    past_uploads = get_uploads()
    context = {
        "form": form,
        "past_uploads": past_uploads,
    }
    return render(request, 'regression-upload.html', context)


def get_uploads():
    activities = []
    platform = Platform_File.objects.all()
    for i in platform:
        activity = Activity.objects.filter(platform=i.id)
        activities.append({"platform": i, "activities": activity})
    context = {
        "activities": activities
    }
    return context


def upload(request):
    form = FileUploadForm()
    excelfile = None
    activity = None
    upload = None
    platform = None
    list_of_vars = None

    past_uploads = get_uploads()

    if request.method == "POST":
        existing_activity_model = None
        form = FileUploadForm(request.POST)
        if form:
            existing_activity_model = Activity.objects.filter(
                activity=request.POST['activity'])
            if len(existing_activity_model) > 0:
                for i in existing_activity_model:
                    if i.platform.platform == request.POST['platform']:
                        upload = i
                        upload.AEM = request.FILES['AEM']
                        upload.NONAEM = request.FILES['NONAEM']
            if not upload:
                upload = Activity(
                    activity=request.POST['activity'],
                    list_of_vars=request.POST['list_of_vars'],
                    AEM=request.FILES['AEM'],
                    NONAEM=request.FILES['NONAEM']
                )
        else:
            logging.error("ITS NOT VALID")
        list_of_vars = request.POST['list_of_vars'] or None
        if list_of_vars:

            list_of_vars = list_of_vars.split(',')
            list_of_vars = [i.strip("\"") for i in list_of_vars]

        activity = request.POST['activity']
        platform = request.POST['platform']

        final = []
        try:
            parsed_AEM = create_parsed_dicts(
                upload.AEM, list_of_var=list_of_vars)
            parsed_NON_AEM = create_parsed_dicts(
                upload.NONAEM, list_of_var=list_of_vars)
        except UploadError as exc:
            context = {
                "form": form,
                "error": UploadError(exc),
                "files_attempted": request.FILES
            }
            return render(request, "regression-upload.html", context)

        diffkeys = [k for k in parsed_NON_AEM[0]
                    ['p'].keys() if k not in parsed_AEM[0]['p'].keys()]

        for k in diffkeys:
            parsed_AEM[0]['p'].setdefault(k, "not present")

        keys = []
        for k, v in parsed_NON_AEM[0]['p'].items():
            for k2, v2 in parsed_AEM[0]['p'].items():
                if k == k2:
                    dic = {"NON": v, "AEM":  v2}
                    if list_of_vars:
                        for i in list_of_vars:
                            if i == k:
                                keys.append(k)
                    else:
                        keys.append(k)
                    if v != v2:
                        dic['flag'] = "FAIL"
                    else:
                        dic['flag'] = "PASS"

            final.append(dic)
        if not keys:
            keys = list_of_vars
        df = pd.DataFrame.from_records(data=final, index=keys)
        excelfile = convert_to_excel(
            df, platform + '.xlsx', sheet_name=activity)

        platform_model = Platform_File.objects.filter(platform=platform)
        existing_platform_model = None
        if len(platform_model) > 0:
            existing_platform_model = platform_model[0]
        else:
            platform_model = Platform_File(
                platform=platform,
                platform_file=excelfile['file_name'],
                created=timezone.now()
            )
        if existing_platform_model:
            existing_platform_model.platform_file = excelfile['file_name']
            existing_platform_model.created = timezone.now()
            existing_platform_model.save()
            upload.platform = existing_platform_model
            upload.save()
        else:
            platform_model.save()
            upload.platform = platform_model
            upload.save()

        os.remove(upload.AEM.name)
        os.remove(upload.NONAEM.name)
        past_uploads = get_uploads()

    return render(request, "regression-upload.html", {"excelfile": excelfile, "activity": activity, "platform": platform, "list_of_vars": list_of_vars, "form": form, "past_uploads": past_uploads})


def get_single_uploads():
    single_files = SingleFile.objects.all()
    return single_files


def single_file_upload(request):
    form = SingleFileForm()
    past_uploads = get_single_uploads()
    context = {
        "form": form,
        "past_uploads": past_uploads
    }
    return render(request, "single-upload.html", context)


def upload_single_file(request):
    context = {}
    form = SingleFileForm()
    if request.method == "POST":
        incoming_req = request.POST
        form = SingleFileForm(request.POST)
        single_upload = SingleFile(
            platform=incoming_req['platform'],
            environment=incoming_req['environment'],
            list_of_vars=incoming_req['list_of_vars'],
        )
        to_convert_file = request.FILES['upload_file']
        list_of_vars = incoming_req['list_of_vars'] or None
        if list_of_vars:
            list_of_vars = list_of_vars.split(',')
            list_of_vars = [i.strip("\"") for i in list_of_vars]
        try:
            parsed = create_parsed_dicts(
                to_convert_file, list_of_var=list_of_vars)
        except UploadError as exc:
            context = {
                "form": form,
                "error": UploadError(exc),
                "files_attempted": request.FILES
            }
            return render(request, "single-upload.html", context)

        final = []
        diffkeys = []
        keys = []
        for i in parsed:
            for k, v in copy.deepcopy(i['p']).items():
                if k.startswith('get '):
                    del i['p'][k]

        for i in parsed:
            diffmaker = [diffkeys.append(k)
                         for k in i['p'].keys() if k not in diffkeys]

        for i in parsed:
            for k in diffkeys:
                if not i['p'].get(k):
                    i['p'].setdefault(k, "not present")

            final.append(i['p'])
            keys.append(''.join(i['call']))

        if list_of_vars:
            keys = list_of_vars

        df = pd.DataFrame.from_records(data=final, index=keys)
        df = df.transpose()
        excelfile = convert_to_excel(
            df, incoming_req['environment'] + '.xlsx', sheet_name=incoming_req['platform'])
        single_upload.single_file = excelfile['file_name']
        single_upload.save()

        past_uploads = get_single_uploads()

        context = {
            "excelfile": excelfile,
            "past_uploads": past_uploads,
            "form": form

        }

    return render(request, "single-upload.html", context)


def download_file(request):
    file_path = request.GET['file_path']
    file_id = request.GET['file_id']

    try:
        file1 = Platform_File.objects.get(id=file_id)
        bit_file = file1.platform_file
    except:
        file1 = SingleFile.objects.get(id=file_id)
        bit_file = file1.single_file

    if file1:
        response = HttpResponse(
            bit_file, content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'inline; filename=' + \
            os.path.basename(file_path)
        return response
    raise Http404


def delete(request):
    file_path = prs.urlparse(request.GET['file_path'])
    # raise RuntimeError(file_path)
    file_id = request.GET['file_id']
    page = request.GET['page']
    try:
        to_delete = Platform_File.objects.get(id=file_id)
    except:
        to_delete = SingleFile.objects.get(id=file_id)
    to_delete.delete()
    delete_local(file_path)

    return redirect(page)


def preview_file(request):
    file_id = request.GET['file_id']
    try:
        qs = Platform_File.objects.get(id=file_id)
        file1 = qs.platform_file
    except:
        qs = SingleFile.objects.get(id=file_id)
        file1 = qs.single_file
    # raise RuntimeError(file1.read())
    xls = pd.ExcelFile(file1)
    df = xls.parse()
    # raise RuntimeError(df.columns)
    df.index = df['Unnamed: 0']
    del df['Unnamed: 0']
    json = df.to_html()
    columns = df.columns
    template = "preview.html"

    context = {
        'data': json,
        'columns': columns
    }

    return render(request, template, context)


# LOCAL FUNCTIONS
def delete_local(file_path):
    # raise RuntimeError(file_path)
    try:
        os.remove(file_path)
    except:
        return
    return


def create_parsed_dicts(file_obj, list_of_var=None):
    """Parse file and create list of dictionaries of url parameters, if key 'pageName' is present"""
    req = []
    firstlines = []
    parsed_urls = []
    with_pageName_urls = []
    if list_of_var:
        lower_list_of_keys = [i.lower() for i in list_of_var]
    else:
        lower_list_of_keys = []
    specified_key_list_of_dicts = []
    try:
        data = json.load(file_obj.file)
        for p in data:
            req.append(p['request'])
    except Exception:
        raise UploadError("Please be sure you are uploading a JSON file")

    # with open(file_obj, 'rb') as json_file:
    #     data = json.load(json_file)
    #     for p in data:
    #         req.append(p['request'])
    column_headers = []

    for k in req:
        try:
            if k.get('header'):
                request_string = k['header'].get('firstLine', {})
                if len(request_string) > 100:
                    firstlines.append(k['header']['firstLine'])

            if k.get('body'):
                request_string = k['body'].get('text', {})
                if len(request_string) > 100:
                    try:
                        post_call = k['header'].get('firstLine')
                        post_call = post_call.rstrip(" HTTP/1.1")
                    except:
                        post_call = 'Unavailable'
                    k['body']['text'] = 'charles_log_ref=' + \
                        post_call+'&' + \
                        k['body']['text']

                    firstlines.append(k['body']['text'])
        except:
            raise RuntimeError(
                'Please examine CHLSJ file and locate url parameters')

    for l in firstlines:
        parsed_urls.append(prs.parse_qs(l))

    for m in parsed_urls:
        for k, v in m.items():
            m[k] = "".join(v)

    for p in parsed_urls:
        p = {k.lower(): v for k, v in p.items()}
        specified = {}
        index = [ky for ky, va in p.items() if ky.startswith(
            ('get ', 'POST ', 'GET '))]
        if len(index) > 0 and len(lower_list_of_keys) > 0:
            for k in lower_list_of_keys:
                specified.update({k: p.get(k, p.get(k, "Not Present"))})
            specified_key_list_of_dicts.append(
                {"call": index[0], "p": specified})
        else:
            # print(p)
            specified_key_list_of_dicts.append({"call": index, "p": p})
    # print(specified_key_list_of_dicts)

    return specified_key_list_of_dicts


def convert_to_dataframe(parsed_dicts, list_of_keys):
    """Converts list of dictionaires to pandas Dataframe"""
    def flatten(kv, prefix=[]):
        for k, v in kv.items():
            if isinstance(v, dict):
                yield from flatten(v, prefix+[str(k)])
            else:
                if prefix:
                    yield '_'.join(prefix+[str(k)]), v
                else:
                    yield str(k), v

    df = pd.DataFrame({k: v for k, v in flatten(kv)} for kv in parsed_dicts)
    df.index = df['call']
    df.index.names = [None]
    del df['call']
    result = df.transpose()
    return result


def convert_to_excel(df, file_name, sheet_name=None):
    """Converts Pandas DataFrame to Excel readable format"""

    try:
        book = load_workbook(file_name)
        writer = pd.ExcelWriter(file_name, engine='openpyxl')
        writer.book = book
        writer.sheets = dict((ws.title, ws) for ws in book.worksheets)
        df.to_excel(writer, sheet_name=sheet_name)
        writer.save()
        writer.close()
    except:
        df.to_excel(file_name, sheet_name=sheet_name)
    return {"ok": True, "file_name": file_name, "sheet": sheet_name}


def convert_from_chls_to_txt(file_name):
    head, sep, tail = file_name.partition('.')
    copyfile(file_name, head + '.txt')
    # json_friendly = os.rename(file_name, head + '.txt')
    return head + '.txt'
