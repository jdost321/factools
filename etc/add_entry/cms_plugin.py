country = newname.split('_')[2]
entry['attrs'][u'GLIDEIN_Country']=xmlParse.OrderedDict({'comment': None, u'const': u'True', u'glidein_publish': u'True', u'job_publish': u'True', u'parameter': u'True', u'publish': u'True', u'type': u'string', u'value': unicode(country)})
resource_name = bdii_name.split(',')[1].split('=')[1]
entry['attrs'][u'GLIDEIN_ResourceName']=xmlParse.OrderedDict({'comment': None, u'const': u'True', u'glidein_publish': u'True', u'job_publish': u'True', u'parameter': u'True', u'publish': u'True', u'type': u'string', u'value': unicode(resource_name)})
entry['attrs'][u'GLIDEIN_CMSSite']=xmlParse.OrderedDict({'comment': None, u'const': u'True', u'glidein_publish': u'True', u'job_publish': u'True', u'parameter': u'True', u'publish': u'True', u'type': u'string', u'value': unicode(argv[1])})
entry['attrs'][u'GLIDEIN_SEs']=xmlParse.OrderedDict({'comment': None, u'const': u'True', u'glidein_publish': u'True', u'job_publish': u'True', u'parameter': u'True', u'publish': u'True', u'type': u'string', u'value': unicode(argv[2])})
