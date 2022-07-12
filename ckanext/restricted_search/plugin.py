import logging

import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckan.lib.helpers as helper
import ckanext.restricted_search.cli as cli
from ckanext.spatial.interfaces import ISpatialHarvester
from ckanext.spatial.validation.validation import BaseValidator

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
        data_dict['extras_eov_restricted'] = json.loads(data_dict.get('extras_eov_restricted', '[]'))
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
    
class MyValidator(BaseValidator):

    name = 'my-validator'

    title= 'My very own validator'

    @classmethod
    def is_valid(cls, xml):

        return True, []