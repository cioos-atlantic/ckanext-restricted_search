from ast import keyword
import logging

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckan.lib.helpers as helper
import ckanext.restricted_search.cli as cli
from ckanext.spatial.interfaces import ISpatialHarvester
from ckanext.spatial.validation.validation import BaseValidator
from ckanext.cioos_harvest import plugin as harvester
import xml.etree.ElementTree as ET
from ckanext.scheming.validation import scheming_validator

import json

log = logging.getLogger(__name__)


class RestrictedSearchPlugin(plugins.SingletonPlugin):
    #TODO find out which are no longer required
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IFacets)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IActions, inherit=True)
    plugins.implements(plugins.IDatasetForm)
    plugins.implements(plugins.IClick)
    plugins.implements(ISpatialHarvester, inherit=True) 

    
    def get_commands(self):
        return cli.get_commands()

    # IConfigurer
    # ITemplateHelpers
    def get_helpers(self):
        return {
        }

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic',
            'restricted_search')

    def get_actions(self):
        return {}

    
    """
    Required by CKAN for the schema changes to function
    """
    def is_fallback(self):
        # Return True to register this plugin as the default handler for
        # package types not handled by any other IDatasetForm plugin.
        return False
    
    """
    Required by CKAN for the schema changes to function
    """
    def package_types(self):
        # This plugin doesn't handle any special package types, it just
        # registers itself as the default (above).
        return []

   # Interfaces
    """
    Commented out as the restricted field is a 'text' instead of 'string' and gets tokenized
    Reintroduce if new field set up
    """
    def dataset_facets(self, facets_dict, package_type):
        # facets_dict['extras_eov_restricted'] = toolkit._('Restricted EOVs')
        return facets_dict

    def organization_facets(self, facets_dict, organization_type, package_type, ):
        return facets_dict

    def group_facets(self, facets_dict, group_type, package_type, ):
        return facets_dict

    def before_index(self, data_dict):
        data_dict['extras_eov_restricted'] = json.loads(data_dict.get('extras_eov_restricted', '') or 'null')
        return data_dict
        
    """
    Hook into before_search
    If the set string is included in the filter query, duplicate the EOV and keywords fields and 
        set them in either extras_eov_restricted or extras_keywords_restricted respectively
    """
    def before_search(self, search_params):
        if 'fq' not in search_params:
            return search_params
        filter_query = search_params['fq']
        if 'restricted_search:"enabled"' in filter_query:
            filter_query = filter_query.replace('restricted_search:"enabled"', "")
            if "eov:" in filter_query or 'tags_en:' in filter_query or 'tags_fr:' in filter_query or 'tags:' in filter_query:
                fq_split = filter_query.split(' ')
                final_query = ""
                for x in fq_split:
                    if(x.startswith('eov:') and '"' in x):
                        eov = x.split('"')[1]
                        eov_restricted = 'extras_eov_restricted:"' + eov + '"'
                        x= '(eov:"' + eov + '" OR ' + eov_restricted + ')'
                    elif(x.startswith('tags_en:') and '"' in x):
                        tags = x.split('"')[1]
                        tags_restricted = 'extras_keywords_restricted:"' + tags + '"'
                        x= '(tags_en:"' + tags + '" OR ' + tags_restricted + ')'
                    elif(x.startswith('tags_fr:') and '"' in x):
                        tags = x.split('"')[1]
                        tags_restricted = 'extras_keywords_restricted:"' + tags + '"'
                        x= '(tags_fr:"' + tags + '" OR ' + tags_restricted + ')'
                    elif(x.startswith('tags:') and '"' in x):
                        tags = x.split('"')[1]
                        tags_restricted = 'extras_keywords_restricted:"' + tags + '"'
                        x= '(tags:"' + tags + '" OR ' + tags_restricted + ')'
                    final_query += x + ' '
                search_params['fq'] = final_query.strip()
            else:
                search_params['fq'] = filter_query.strip()   
        return search_params

    # IPackageController -> When displaying a dataset
    def after_show(self,context, pkg_dict):
        return pkg_dict

    def after_search(self, search_results, search_params):
        # Gets the current user's ID (or if the user object does not exist, sets user as 'public')
        datasets = search_results['results']
        
        # Checks if the search requires restricted variable checking
        # TODO Overall costly - find a better alternative
        restricted_search_enabled = False
        restricted_search_eovs = []
        restricted_search_keywords = []
        for x in search_params['fq'][0].replace(")","").replace("(", "").split(" "):
            if(x.startswith('extras_eov_restricted')):
                restricted_search_eovs.append(x.split('"')[1])
                restricted_search_enabled = True
            elif(x.startswith('extras_keywords_restricted')):
                restricted_search_keywords.append(x.split('"')[1])
                restricted_search_enabled = True

        # Go through each of the datasets returned in the results
        for x in range(len(datasets)):
            pkg_dict = search_results['results'][x]
            if restricted_search_enabled:
                try:
                    if('extras_eov_restricted' in pkg_dict):
                        log.info(pkg_dict['extras_eov_restricted'])
                        log.info(restricted_search_eovs)
                        for x in restricted_search_eovs:
                            if x in pkg_dict['extras_eov_restricted']:
                                pkg_dict['mark_restricted'] = True
                                continue
                    if('extras_keywords_restricted' in pkg_dict and 'mark_restricted' not in pkg_dict):
                        for x in restricted_search_keywords:
                            if x in pkg_dict['extras_keywords_restricted']['en'] or x in pkg_dict['extras_keywords_restricted']['fr']:
                                pkg_dict['mark_restricted'] = True
                                continue
                except:
                    log.info('An error with restricted search occurred')
        return search_results


class RestrictedHarvestPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IActions, inherit=True)
    plugins.implements(plugins.IDatasetForm)
    plugins.implements(ISpatialHarvester, inherit=True) 


    # IConfigurer
    # ITemplateHelpers
    """
    Required by CKAN
    """
    def get_helpers(self):
        return {
        }

    """
    Required by CKAN
    """
    def update_config(self, config_):
        toolkit.add_resource('fanstatic',
            'restricted_harvest')

    """
    Required by CKAN
    """
    def get_actions(self):
        return {}

        
    """
    Required by CKAN
    """
    def is_fallback(self):
        # Return True to register this plugin as the default handler for
        # package types not handled by any other IDatasetForm plugin.
        return False

    """
    Required by CKAN
    """
    def package_types(self):
        # This plugin doesn't handle any special package types, it just
        # registers itself as the default (above).
        return []

    def get_package_dict(self, context, data_dict):
        log.info("Getting pkg dict")
        pkg_dict = data_dict['package_dict']
        iso_values = data_dict['iso_values']
        harvest_object = data_dict['harvest_object']
        source_config = json.loads(data_dict['harvest_object'].source.config)

        ET.register_namespace('mri', 'http://standards.iso.org/iso/19115/-3/mri/1.0')
        ET.register_namespace('gco', 'http://standards.iso.org/iso/19115/-3/gco/1.0')
        ET.register_namespace('xsi', 'http://www.w3.org/2001/XMLSchema-instance')
        ET.register_namespace('lan', 'http://standards.iso.org/iso/19115/-3/lan/1.0')
        tree = ET.fromstring(harvest_object.content)
        namespaces = {'mri':'http://standards.iso.org/iso/19115/-3/mri/1.0', 'gco':'http://standards.iso.org/iso/19115/-3/gco/1.0',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance', 'lan': 'http://standards.iso.org/iso/19115/-3/lan/1.0'}
        harvest_keywords = tree.findall(".//mri:descriptiveKeywords", namespaces)
        open_keywords = pkg_dict['keywords']
        restricted_keywords = {'en':[], 'fr':[]}
        if 'extras_keywords_restricted' in pkg_dict:
            restricted_keywords = pkg_dict["extras_keywords_restricted"]
        
        for k in harvest_keywords:
            # Find the one that has a class of restricted keywords, remove the rest
            keyword_root = k.find(".//mri:MD_KeywordClass/mri:className[gco:CharacterString='Restricted Keywords']", namespaces)
            if(keyword_root):
                harvest_restricted_keywords_en = k.findall(".//mri:MD_Keywords/mri:keyword/gco:CharacterString", namespaces)
                for r in harvest_restricted_keywords_en:
                    if r.text in open_keywords['en']:
                        open_keywords['en'].remove(r.text)
                        restricted_keywords['en'].append(r.text)
                harvest_restricted_keywords_fr = k.findall(".//mri:MD_Keywords/mri:keyword/lan:PT_FreeText/lan:textGroup/lan:LocalisedCharacterString", namespaces)
                for r in harvest_restricted_keywords_fr:
                    if r.text in open_keywords['fr']:
                        open_keywords['fr'].remove(r.text)
                        restricted_keywords['fr'].append(r.text)
        pkg_dict['keywords'] = open_keywords
        pkg_dict['extras_keywords_restricted'] = restricted_keywords
        return pkg_dict

class RestrictedHarvestValidatorPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IPackageController, inherit=True)
    plugins.implements(plugins.IActions, inherit=True)
    plugins.implements(plugins.IDatasetForm)
    plugins.implements(plugins.IValidators)


    # IConfigurer
    # ITemplateHelpers
    """
    Required by CKAN
    """
    def get_helpers(self):
        return {
        }

    def get_validators(self):
        # For some reason returning it outside the variable causes spatial to think it's being passed a string
        #validators = {'cioos_clean_and_populate_restricted_eovs': clean_and_populate_restricted_eovs}
        #return validators
        return {'cioos_clean_and_populate_restricted_eovs':clean_and_populate_restricted_eovs}

    """
    Required by CKAN
    """
    def update_config(self, config_):
        toolkit.add_resource('fanstatic',
            'restricted_harvest')

    """
    Required by CKAN
    """
    def get_actions(self):
        return {}

        
    """
    Required by CKAN
    """
    def is_fallback(self):
        # Return True to register this plugin as the default handler for
        # package types not handled by any other IDatasetForm plugin.
        return False

    """
    Required by CKAN
    """
    def package_types(self):
        # This plugin doesn't handle any special package types, it just
        # registers itself as the default (above).
        return []
    
# IValidators

# this validator tries to populate eov from keywords. It looks for any english
# keywords that match either the value or label in the choice list for the eov
# field and add's them to the eov field.
# Validator adapted from: https://github.com/cioos-siooc/ckanext-cioos_theme/blob/master/ckanext/cioos_theme/plugin.py#L108
#   except to be used with the restricted keyword field instead and the field can be empty
@scheming_validator
def clean_and_populate_restricted_eovs(field, schema):
    def validator(key, data, errors, context):
        keywords_main = data.get(('extras_keywords_restricted',), {})
        if keywords_main:
            eov_data = keywords_main.get('en', [])
        else:
            return data

        eov_list = {}
        for x in toolkit.h.scheming_field_choices(toolkit.h.scheming_field_by_name(schema['dataset_fields'], 'eov')):
            eov_list[x['value'].lower()] = x['value']
            eov_list[x['label'].lower()] = x['value']

        log.info(eov_data)
        d = json.loads(data.get(key, '[]'))
        for x in eov_data:
            if isinstance(x, str):  # TODO: change basestring to str when moving to python 3
                val = eov_list.get(x.lower(), '')
            else:
                val = eov_list.get(x, '')
            if val and val not in d:
                d.append(val)

        data[key] = json.dumps(d)
        return data
    return validator